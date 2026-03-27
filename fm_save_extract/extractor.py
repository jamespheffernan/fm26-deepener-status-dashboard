from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path

from .binary import decompress_main_frame
from .diff_decoders import (
    decode_contracts_from_diff_frames,
    decode_staff_roles_from_diff_frames,
    summarize_diff_frames,
    summarize_pairwise_diff_frames,
)
from .inline_people import extract_inline_named_people
from .metadata import cluster_metadata_hits, clusters_near_range, find_metadata_hits, summarize_clusters
from .models import ExtractionBundle
from .player_blocks import enumerate_person_candidates
from .relation_resolution import resolve_relation
from .reference_data import extract_clubs, extract_firstnames, extract_game_info, extract_surnames, write_reference_tables


def load_input_frame(input_path: str | Path, *, raw: bool = False) -> bytes:
    path = Path(input_path)
    if raw or path.suffix.lower() == ".bin":
        return path.read_bytes()
    return decompress_main_frame(path)


def _collect_offsets(payload: dict[str, object]) -> list[int]:
    offsets = payload.get("offsets")
    if not isinstance(offsets, dict):
        return []

    values: list[int] = []
    for raw_value in offsets.values():
        if isinstance(raw_value, int):
            values.append(raw_value)
            continue
        if isinstance(raw_value, list):
            values.extend(value for value in raw_value if isinstance(value, int))
    return sorted(set(values))


def _annotate_with_metadata(
    payload: dict[str, object],
    metadata_clusters: list[object],
) -> dict[str, object]:
    offsets = _collect_offsets(payload)
    if not offsets:
        return payload

    matched_clusters = clusters_near_range(metadata_clusters, offsets[0], offsets[-1])
    if not matched_clusters:
        return payload

    enriched = dict(payload)
    enriched["metadata_clusters"] = [cluster.to_dict() for cluster in matched_clusters]
    enriched["metadata_keywords"] = sorted({keyword for cluster in matched_clusters for keyword in cluster.keywords})
    return enriched


def _candidate_inline_match_score(candidate: object, inline_person: dict[str, object]) -> tuple[int, int] | None:
    inline_offsets = inline_person.get("offsets", {})
    if not isinstance(inline_offsets, dict):
        return None

    name_anchor = inline_offsets.get("name_length_offset")
    if not isinstance(name_anchor, int):
        name_anchor = inline_offsets.get("name_offset")
    if not isinstance(name_anchor, int):
        return None

    inline_dob = inline_person.get("dob")
    candidate_dob = getattr(candidate, "dob", None)
    if inline_dob and candidate_dob:
        if inline_dob != candidate_dob:
            return None
    else:
        return None

    distance = abs(name_anchor - int(candidate.block_start))
    if distance > 4096:
        return None

    score = 4
    if distance <= 2048:
        score += 1
    if getattr(candidate, "uid", None) is not None:
        score += 1
    if inline_person.get("inline_secondary_tails"):
        score += 1

    return score, distance


def _merge_person_records(primary: dict[str, object], inline_person: dict[str, object]) -> dict[str, object]:
    merged = dict(primary)
    merged["source"] = "hybrid_block+inline_name_dob"
    if inline_person.get("full_name"):
        merged["full_name"] = inline_person["full_name"]

    alias_keys = [str(primary["person_key"])]
    if inline_person.get("person_key") and inline_person["person_key"] not in alias_keys:
        alias_keys.append(str(inline_person["person_key"]))
    merged["alias_person_keys"] = alias_keys

    offsets = dict(primary.get("offsets", {}))
    inline_offsets = inline_person.get("offsets", {})
    if isinstance(inline_offsets, dict):
        for key, value in inline_offsets.items():
            if key not in offsets:
                offsets[key] = value
    merged["offsets"] = offsets

    merged["confidence"] = round(max(float(primary.get("confidence", 0.0)), float(inline_person.get("confidence", 0.0))), 3)
    merged["evidence"] = list(dict.fromkeys([*primary.get("evidence", []), *inline_person.get("evidence", [])]))

    for key in ("inline_post_dob", "inline_secondary_tails", "relation_window", "relation_entries"):
        if key in inline_person:
            merged[key] = inline_person[key]

    return merged


def _reconcile_people(
    candidates: list[object],
    inline_named_people: list[dict[str, object]],
    metadata_clusters: list[object],
) -> tuple[list[dict[str, object]], dict[str, str]]:
    canonical_people: list[dict[str, object]] = []
    person_key_map: dict[str, str] = {}
    matched_inline_indexes: set[int] = set()

    candidate_records = []
    for candidate in candidates:
        record = _annotate_with_metadata(candidate.to_person_record(), metadata_clusters)
        record["alias_person_keys"] = [str(record["person_key"])]
        candidate_records.append(record)
    for candidate, candidate_record in zip(candidates, candidate_records, strict=True):
        matches: list[tuple[int, int, int]] = []
        for index, inline_person in enumerate(inline_named_people):
            score = _candidate_inline_match_score(candidate, inline_person)
            if score is None:
                continue
            matches.append((score[0], -score[1], index))

        if matches:
            _, _, best_index = max(matches)
            matched_inline_indexes.add(best_index)
            merged = _merge_person_records(candidate_record, _annotate_with_metadata(inline_named_people[best_index], metadata_clusters))
            canonical_people.append(merged)
            for alias in merged.get("alias_person_keys", []):
                person_key_map[str(alias)] = str(merged["person_key"])
            continue

        canonical_people.append(candidate_record)
        person_key_map[str(candidate_record["person_key"])] = str(candidate_record["person_key"])

    for index, inline_person in enumerate(inline_named_people):
        if index in matched_inline_indexes:
            continue
        enriched = _annotate_with_metadata(inline_person, metadata_clusters)
        enriched["alias_person_keys"] = [str(enriched["person_key"])]
        canonical_people.append(enriched)
        person_key_map[str(enriched["person_key"])] = str(enriched["person_key"])

    canonical_people.sort(
        key=lambda item: (
            int(item.get("offsets", {}).get("block_start", item.get("offsets", {}).get("name_length_offset", 10**9))),
            str(item["person_key"]),
        )
    )
    return canonical_people, person_key_map


def _canonicalize_person_key(payload: dict[str, object], person_key_map: dict[str, str]) -> dict[str, object]:
    person_key = payload.get("person_key")
    if not isinstance(person_key, str):
        return payload
    canonical_key = person_key_map.get(person_key, person_key)
    if canonical_key == person_key:
        return payload
    updated = dict(payload)
    updated["person_key"] = canonical_key
    updated["source_person_key"] = person_key
    return updated


def _relation_fingerprint(payload: dict[str, object]) -> tuple[int, str, int, int, str | None] | None:
    offset = payload.get("offset")
    tag = payload.get("tag")
    value = payload.get("value")
    slot = payload.get("slot")
    ref_hex = payload.get("ref_hex")
    if not isinstance(offset, int) or not isinstance(tag, str) or not isinstance(value, int) or not isinstance(slot, int):
        return None
    if ref_hex is not None and not isinstance(ref_hex, str):
        return None
    return offset, tag, value, slot, ref_hex


def _link_summary(link: dict[str, object]) -> dict[str, object]:
    summary = {
        "link_key": link["link_key"],
        "relation_kind": link["relation_kind"],
        "target_kind": link["target_kind"],
        "target_key": link.get("target_key"),
        "club_key": link.get("club_key"),
        "confidence": link["confidence"],
        "pattern_key": link["pattern_key"],
    }
    for key in ("target_hint", "target_label", "resolution_kind", "target_confidence"):
        if key in link:
            summary[key] = link[key]
    return summary


def _attach_people_join_summaries(
    people: list[dict[str, object]],
    club_links: list[dict[str, object]],
    contracts: list[dict[str, object]],
) -> list[dict[str, object]]:
    links_by_person: dict[str, list[dict[str, object]]] = defaultdict(list)
    for link in club_links:
        person_key = link.get("person_key")
        if isinstance(person_key, str):
            links_by_person[person_key].append(link)

    contracts_by_person: dict[str, list[dict[str, object]]] = defaultdict(list)
    for contract in contracts:
        person_key = contract.get("person_key")
        if isinstance(person_key, str):
            contracts_by_person[person_key].append(contract)

    enriched_people: list[dict[str, object]] = []
    for person in people:
        person_key = person.get("person_key")
        if not isinstance(person_key, str):
            enriched_people.append(person)
            continue

        updated = dict(person)
        person_links = links_by_person.get(person_key, [])
        if person_links:
            updated["typed_relation_summaries"] = [_link_summary(link) for link in person_links]
            club_keys = sorted({str(link["club_key"]) for link in person_links if isinstance(link.get("club_key"), str)})
            if club_keys:
                updated["club_keys"] = club_keys

        person_contracts = contracts_by_person.get(person_key, [])
        if person_contracts:
            updated["contract_keys"] = [str(contract["contract_key"]) for contract in person_contracts if isinstance(contract.get("contract_key"), str)]

        enriched_people.append(updated)

    return enriched_people


def _best_person_club_links(club_links: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    best: dict[str, dict[str, object]] = {}
    for link in club_links:
        person_key = link.get("person_key")
        club_key = link.get("club_key")
        if (
            not isinstance(person_key, str)
            or not isinstance(club_key, str)
            or link.get("relation_kind") != "club_employment"
        ):
            continue
        existing = best.get(person_key)
        link_score = (
            float(link.get("target_confidence", link.get("confidence", 0.0))),
            float(link.get("confidence", 0.0)),
        )
        existing_score = (
            float(existing.get("target_confidence", existing.get("confidence", 0.0))),
            float(existing.get("confidence", 0.0)),
        ) if existing is not None else None
        if existing is None or (existing_score is not None and link_score > existing_score):
            best[person_key] = link
    return best


def _contracts_by_person(contracts: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    by_person: dict[str, list[dict[str, object]]] = defaultdict(list)
    for contract in contracts:
        person_key = contract.get("person_key")
        if isinstance(person_key, str):
            by_person[person_key].append(contract)
    return by_person


def _derive_team_target_key(club_key: str, value: int) -> str:
    return f"{club_key}:team:{value}"


def _resolve_contextual_link_targets(
    club_links: list[dict[str, object]],
    contracts: list[dict[str, object]],
) -> list[dict[str, object]]:
    best_person_club_links = _best_person_club_links(club_links)
    contracts_by_person = _contracts_by_person(contracts)

    resolved_links: list[dict[str, object]] = []
    for link in club_links:
        updated = dict(link)
        person_key = updated.get("person_key")

        if updated.get("relation_kind") == "contract_reference" and updated.get("target_key") is None and isinstance(person_key, str):
            person_contracts = contracts_by_person.get(person_key, [])
            if len(person_contracts) == 1:
                contract = person_contracts[0]
                updated["target_key"] = contract["contract_key"]
                updated["target_label"] = str(contract["contract_key"])
                updated["resolution_kind"] = "person_contract_match"
                updated["target_confidence"] = round(
                    min(float(updated.get("confidence", 0.0)), float(contract.get("confidence", 0.0))),
                    3,
                )
                updated["evidence"] = [*updated.get("evidence", []), f"contract_key:{contract['contract_key']}"]

        if updated.get("relation_kind") == "staff_assignment" and updated.get("target_key") is None and isinstance(person_key, str):
            best_club = best_person_club_links.get(person_key)
            if best_club is not None and isinstance(best_club.get("club_key"), str) and isinstance(updated.get("value"), int):
                team_value = int(updated["value"])
                updated["club_key"] = best_club["club_key"]
                updated["target_key"] = _derive_team_target_key(best_club["club_key"], team_value)
                club_label = str(best_club.get("target_label", best_club["club_key"]))
                updated["target_label"] = f"{club_label} team {team_value}"
                updated["resolution_kind"] = "club_scoped_team_slot"
                updated["target_confidence"] = round(
                    min(
                        float(updated.get("confidence", 0.0)),
                        float(best_club.get("target_confidence", best_club.get("confidence", 0.0))),
                    ),
                    3,
                )
                updated["evidence"] = [*updated.get("evidence", []), f"derived_team_target:{updated['target_key']}"]

        resolved_links.append(updated)

    return resolved_links


def _enrich_contracts_with_links(
    contracts: list[dict[str, object]],
    best_person_club_links: dict[str, dict[str, object]],
    club_links: list[dict[str, object]],
) -> list[dict[str, object]]:
    contract_refs: dict[str, list[dict[str, object]]] = defaultdict(list)
    for link in club_links:
        if link.get("relation_kind") != "contract_reference":
            continue
        target_key = link.get("target_key")
        if isinstance(target_key, str):
            contract_refs[target_key].append(link)

    enriched: list[dict[str, object]] = []
    for contract in contracts:
        person_key = contract.get("person_key")
        updated = dict(contract)
        if isinstance(person_key, str) and updated.get("club_key") is None:
            best_link = best_person_club_links.get(person_key)
            if best_link is not None:
                updated["club_key"] = best_link["club_key"]
                evidence = list(updated.get("evidence", []))
                evidence.append(f"club_link_match:{best_link['pattern_key']}")
                updated["evidence"] = evidence

        contract_key = updated.get("contract_key")
        if isinstance(contract_key, str):
            linked_refs = contract_refs.get(contract_key, [])
            if linked_refs:
                updated["reference_link_keys"] = [str(link["link_key"]) for link in linked_refs]

        enriched.append(updated)
    return enriched


def _enrich_staff_roles_with_typed_links(
    staff_roles: list[dict[str, object]],
    club_links: list[dict[str, object]],
) -> list[dict[str, object]]:
    links_by_person_and_relation: dict[str, dict[tuple[int, str, int, int, str | None], dict[str, object]]] = defaultdict(dict)
    for link in club_links:
        person_key = link.get("person_key")
        if not isinstance(person_key, str):
            continue
        fingerprint = _relation_fingerprint(link)
        if fingerprint is None:
            continue
        links_by_person_and_relation[person_key][fingerprint] = link

    best_person_club_links = _best_person_club_links(club_links)
    enriched_roles: list[dict[str, object]] = []
    for role in staff_roles:
        person_key = role.get("person_key")
        if not isinstance(person_key, str):
            enriched_roles.append(role)
            continue

        updated = dict(role)
        typed_links = []
        for relation in role.get("club_link_refs", []):
            if not isinstance(relation, dict):
                continue
            fingerprint = _relation_fingerprint(relation)
            if fingerprint is None:
                continue
            resolved = links_by_person_and_relation.get(person_key, {}).get(fingerprint)
            if resolved is None:
                continue
            typed_links.append(
                {
                    **_link_summary(resolved),
                    "raw_tag": relation.get("tag"),
                    "raw_ref_hex": relation.get("ref_hex"),
                    "raw_value": relation.get("value"),
                    "raw_slot": relation.get("slot"),
                    "raw_offset": relation.get("offset"),
                }
            )

        if typed_links:
            updated["typed_link_refs"] = typed_links
            team_keys = sorted({str(link["target_key"]) for link in typed_links if link.get("target_kind") == "team" and isinstance(link.get("target_key"), str)})
            if team_keys:
                updated["team_keys"] = team_keys

        best_club = best_person_club_links.get(person_key)
        if best_club is not None and isinstance(best_club.get("club_key"), str):
            updated["club_key"] = best_club["club_key"]

        enriched_roles.append(updated)
    return enriched_roles


def _emit_club_links(
    people: list[dict[str, object]],
    staff_roles: list[dict[str, object]],
    clubs: list[dict[str, object]],
    person_key_map: dict[str, str],
) -> list[dict[str, object]]:
    seen: set[tuple[str, int, str, int, int, str | None]] = set()
    links: list[dict[str, object]] = []

    def append_link(
        person_key: str,
        relation: dict[str, object],
        *,
        source: str,
        confidence: float,
    ) -> None:
        offset = relation.get("offset")
        tag = relation.get("tag")
        value = relation.get("value")
        slot = relation.get("slot")
        if not isinstance(offset, int) or not isinstance(tag, str) or not isinstance(value, int) or not isinstance(slot, int):
            return

        canonical_person_key = person_key_map.get(person_key, person_key)
        dedupe_key = (canonical_person_key, offset, tag, value, slot, str(relation.get("ref_hex")) if relation.get("ref_hex") is not None else None)
        if dedupe_key in seen:
            return
        seen.add(dedupe_key)

        resolved = resolve_relation(relation, clubs)
        club_key = resolved.get("club_key")
        links.append(
            {
                "link_key": f"{canonical_person_key}:0x{offset:08X}:{tag}",
                "person_key": canonical_person_key,
                "source": source,
                "relation_kind": resolved["relation_kind"],
                "target_kind": resolved["target_kind"],
                "target_key": resolved.get("target_key"),
                "club_key": club_key,
                "tag": tag,
                "ref_hex": relation.get("ref_hex"),
                "value": value,
                "slot": slot,
                "offset": offset,
                "confidence": round(max(confidence, float(resolved["confidence"])), 3),
                "pattern_key": resolved["pattern_key"],
                **({"target_hint": resolved["target_hint"]} if "target_hint" in resolved else {}),
                **({"target_label": resolved["target_label"]} if "target_label" in resolved else {}),
                **({"resolution_kind": resolved["resolution_kind"]} if "resolution_kind" in resolved else {}),
                **({"target_confidence": resolved["target_confidence"]} if "target_confidence" in resolved else {}),
                "evidence": [
                    source,
                    f"pattern:{resolved['pattern_key']}",
                    f"tag:{tag}",
                    f"value:{value}",
                    f"slot:{slot}",
                    f"offset:0x{offset:08X}",
                    *( [f"club_key:{club_key}"] if club_key is not None else [] ),
                ],
            }
        )

    for person in people:
        for relation in person.get("relation_entries", []):
            if isinstance(relation, dict):
                append_link(str(person["person_key"]), relation, source="inline_relation_entry", confidence=0.58)

    for staff_role in staff_roles:
        if not isinstance(staff_role, dict):
            continue
        person_key = staff_role.get("person_key")
        if not isinstance(person_key, str):
            continue
        for relation in staff_role.get("club_link_refs", []):
            if isinstance(relation, dict):
                append_link(person_key, relation, source="staff_role_ref", confidence=0.66)

    links.sort(key=lambda item: (item["person_key"], int(item["offset"]), item["tag"]))
    return links


def extract_world_state(
    data: bytes,
    *,
    diff_frames: list[tuple[str, bytes]] | None = None,
    reference_tables: bool = False,
) -> tuple[ExtractionBundle, dict[str, dict[int, str]]]:
    game_info = extract_game_info(data)
    clubs = extract_clubs(data)
    candidates = enumerate_person_candidates(data)
    inline_named_people = extract_inline_named_people(data)
    players = [candidate.to_player_record() for candidate in candidates if candidate.confidence >= 0.45]

    metadata_hits = find_metadata_hits(data)
    metadata_clusters = cluster_metadata_hits(metadata_hits)
    people, person_key_map = _reconcile_people(candidates, inline_named_people, metadata_clusters)
    low_confidence_people = [
        _annotate_with_metadata(
            {
                "person_key": candidate.person_key,
                "block_start": candidate.block_start,
                "confidence": candidate.confidence,
                "evidence": candidate.evidence,
            },
            metadata_clusters,
        )
        for candidate in candidates
        if candidate.confidence < 0.45
    ]
    diff_frame_map = dict(diff_frames or [])
    contracts = decode_contracts_from_diff_frames(data, diff_frame_map)
    staff_roles = decode_staff_roles_from_diff_frames(diff_frame_map)
    contracts = [_canonicalize_person_key(contract, person_key_map) for contract in contracts]
    staff_roles = [_canonicalize_person_key(staff_role, person_key_map) for staff_role in staff_roles]
    club_links = _emit_club_links(people, staff_roles, clubs, person_key_map)
    club_links = _resolve_contextual_link_targets(club_links, contracts)
    best_person_club_links = _best_person_club_links(club_links)
    contracts = _enrich_contracts_with_links(contracts, best_person_club_links, club_links)
    staff_roles = _enrich_staff_roles_with_typed_links(staff_roles, club_links)
    people = _attach_people_join_summaries(people, club_links, contracts)
    unresolved = {
        "metadata_clusters": [cluster.to_dict() for cluster in metadata_clusters],
        "low_confidence_people": low_confidence_people,
        "inline_name_people_count": len(inline_named_people),
        "canonical_people_count": len(people),
        "club_link_count": len(club_links),
        "inline_secondary_tail_counts": {
            "pat": sum(
                1
                for person in inline_named_people
                for tail in person.get("inline_secondary_tails", [])
                if tail.get("variant") == "pat"
            ),
            "pat2": sum(
                1
                for person in inline_named_people
                for tail in person.get("inline_secondary_tails", [])
                if tail.get("variant") == "pat2"
            ),
        },
        "inline_name_people_sample": [
            {
                "person_key": person["person_key"],
                "full_name": person["full_name"],
                "dob": person["dob"],
            }
            for person in inline_named_people[:12]
        ],
        "inline_pat2_tail_sample": [
            {
                "person_key": person["person_key"],
                "full_name": person["full_name"],
                "tail_start": tail["tail_start"],
                "working_with_youngsters_candidate_offset": tail.get("working_with_youngsters_candidate_offset"),
            }
            for person in inline_named_people
            for tail in person.get("inline_secondary_tails", [])
            if tail.get("variant") == "pat2"
        ][:12],
        **summarize_clusters(metadata_clusters),
    }

    if diff_frame_map:
        unresolved["diff_frames"] = summarize_diff_frames(data, diff_frame_map)
        unresolved["edited_diff_pairs"] = summarize_pairwise_diff_frames(diff_frames or [])

    bundle = ExtractionBundle(
        game_info=game_info,
        clubs=clubs,
        people=people,
        players=players,
        staff_roles=staff_roles,
        club_links=club_links,
        contracts=contracts,
        unresolved_candidates=unresolved,
    )

    reference_payload: dict[str, dict[int, str]] = {}
    if reference_tables:
        reference_payload = {
            "firstnames": extract_firstnames(data),
            "surnames": extract_surnames(data),
        }

    return bundle, reference_payload


def write_bundle(output_dir: Path, bundle: ExtractionBundle) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, payload in bundle.to_dicts().items():
        with (output_dir / filename).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)


def write_reference_payload(output_dir: Path, payload: dict[str, dict[int, str]]) -> None:
    if not payload:
        return
    write_reference_tables(output_dir, payload.get("firstnames", {}), payload.get("surnames", {}))
