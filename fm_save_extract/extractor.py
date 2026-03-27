from __future__ import annotations

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
from .metadata import cluster_metadata_hits, find_metadata_hits, summarize_clusters
from .models import ExtractionBundle
from .player_blocks import enumerate_person_candidates
from .reference_data import extract_clubs, extract_firstnames, extract_game_info, extract_surnames, write_reference_tables


def load_input_frame(input_path: str | Path, *, raw: bool = False) -> bytes:
    path = Path(input_path)
    if raw or path.suffix.lower() == ".bin":
        return path.read_bytes()
    return decompress_main_frame(path)


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

    people = [candidate.to_person_record() for candidate in candidates if candidate.confidence >= 0.45]
    people.extend(inline_named_people)
    players = [candidate.to_player_record() for candidate in candidates if candidate.confidence >= 0.45]
    low_confidence_people = [
        {
            "person_key": candidate.person_key,
            "block_start": candidate.block_start,
            "confidence": candidate.confidence,
            "evidence": candidate.evidence,
        }
        for candidate in candidates
        if candidate.confidence < 0.45
    ]

    metadata_hits = find_metadata_hits(data)
    metadata_clusters = cluster_metadata_hits(metadata_hits)
    diff_frame_map = dict(diff_frames or [])
    contracts = decode_contracts_from_diff_frames(data, diff_frame_map)
    staff_roles = decode_staff_roles_from_diff_frames(diff_frame_map)
    unresolved = {
        "metadata_clusters": [cluster.to_dict() for cluster in metadata_clusters],
        "low_confidence_people": low_confidence_people,
        "inline_name_people_count": len(inline_named_people),
        "inline_name_people_sample": [
            {
                "person_key": person["person_key"],
                "full_name": person["full_name"],
                "dob": person["dob"],
            }
            for person in inline_named_people[:12]
        ],
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
