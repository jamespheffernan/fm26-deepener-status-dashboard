from __future__ import annotations

import struct

from .binary import decode_date

PAT = bytes.fromhex("ff01ff0000000002401000000000")
PAT2 = bytes.fromhex("ff01ff0000000102401000000000")
TAIL_MARKER_PREFIX_LEN = 7
STAFF_TAIL_PREAMBLE_LEN = 0x20
STAFF_TAIL_VECTOR_LEN = 0x40
STAFF_TAIL_WWY_RELATIVE_OFFSET = 0x3D
DEFAULT_TAIL_SCAN_LIMIT = 0x3000
RELATION_ENTRY_LEN = 0x10
RELATION_TRAILER = b"\x00\x00\x00"


def _decode_full_name(payload: bytes) -> str | None:
    if b"\x00" in payload or b" " not in payload:
        return None
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if len(text) < 6 or len(text) > 120:
        return None
    words = [word for word in text.split(" ") if word]
    if len(words) < 2:
        return None
    if not any(character.isalpha() for character in text):
        return None
    if any(len(word) > 40 for word in words):
        return None
    return text


def _nearby_dates_before_name(
    data: bytes,
    name_length_offset: int,
    *,
    radius: int = 256,
) -> list[dict[str, int | str]]:
    results: list[dict[str, int | str]] = []
    start = max(0, name_length_offset - radius)
    for offset in range(start, name_length_offset, 2):
        decoded = decode_date(data, offset)
        if decoded is None:
            continue
        results.append({"offset": offset, "value": decoded})
    return results


def _inline_post_dob_signature(data: bytes, dob_offset: int) -> dict[str, object] | None:
    end = dob_offset + 31
    if end > len(data):
        return None

    return {
        "u16_0": struct.unpack_from("<H", data, dob_offset + 4)[0],
        "u16_1": struct.unpack_from("<H", data, dob_offset + 6)[0],
        "u32_0": struct.unpack_from("<I", data, dob_offset + 8)[0],
        "u32_1": struct.unpack_from("<I", data, dob_offset + 12)[0],
        "u32_2": struct.unpack_from("<I", data, dob_offset + 16)[0],
        "band8": list(data[dob_offset + 20:dob_offset + 28]),
        "tail_u24": data[dob_offset + 28] | (data[dob_offset + 29] << 8) | (data[dob_offset + 30] << 16),
    }


def _scan_inline_name_anchors(
    data: bytes,
    *,
    search_start: int = 0,
    search_end: int | None = None,
) -> list[dict[str, object]]:
    end = len(data) if search_end is None else min(search_end, len(data))
    anchors: list[dict[str, object]] = []

    for offset in range(search_start, end - 8):
        length = struct.unpack_from("<I", data, offset)[0]
        if length < 6 or length > 120:
            continue

        payload_start = offset + 4
        payload_end = payload_start + length
        if payload_end + 4 > end:
            continue

        full_name = _decode_full_name(data[payload_start:payload_end])
        if full_name is None:
            continue

        dob = decode_date(data, payload_end)
        if dob is None:
            continue
        year = int(dob[:4])
        if not (1950 <= year <= 2015):
            continue

        anchors.append(
            {
                "name_length_offset": offset,
                "name_offset": payload_start,
                "dob_offset": payload_end,
                "full_name": full_name,
                "dob": dob,
            }
        )

    return anchors


def _scan_all_tail_markers(data: bytes, start: int, end: int) -> list[tuple[int, str]]:
    markers: list[tuple[int, str]] = []
    pos = start
    while True:
        idx = data.find(PAT, pos, end)
        if idx < 0:
            break
        markers.append((idx, "pat"))
        pos = idx + 1

    pos = start
    while True:
        idx = data.find(PAT2, pos, end)
        if idx < 0:
            break
        markers.append((idx, "pat2"))
        pos = idx + 1

    markers.sort()
    return markers


def _build_tail_payload(
    tail_markers: list[tuple[int, str]],
    index: int,
    boundary_end: int,
) -> dict[str, int | str]:
    tail_start, variant = tail_markers[index]
    next_tail_start = tail_markers[index + 1][0] if index + 1 < len(tail_markers) else boundary_end
    tail_end = min(next_tail_start, boundary_end)
    family_start = tail_start + TAIL_MARKER_PREFIX_LEN
    vector_start = family_start + STAFF_TAIL_PREAMBLE_LEN
    vector_end = vector_start + STAFF_TAIL_VECTOR_LEN
    tail: dict[str, int | str] = {
        "variant": variant,
        "tail_start": tail_start,
        "tail_end": tail_end,
        "family_start": family_start,
    }
    if vector_end <= boundary_end:
        tail["vector_start"] = vector_start
        tail["vector_end"] = vector_end
    if variant == "pat2":
        candidate_offset = tail_start + STAFF_TAIL_WWY_RELATIVE_OFFSET
        if candidate_offset < tail_end:
            tail["working_with_youngsters_candidate_offset"] = candidate_offset
    return tail


def _parse_relation_entries(data: bytes, start: int, end: int, *, max_entries: int = 256) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    cursor = start
    while cursor + RELATION_ENTRY_LEN <= end and len(entries) < max_entries:
        chunk = data[cursor:cursor + RELATION_ENTRY_LEN]
        if chunk[12:15] != RELATION_TRAILER:
            break
        tag_value = int.from_bytes(chunk[0:4], "big")
        if tag_value != 0:
            entries.append(
                {
                    "offset": cursor,
                    "tag": f"0x{tag_value:08X}",
                    "tag_value": tag_value,
                    "ref_hex": chunk[4:8].hex(),
                    "value": int.from_bytes(chunk[8:12], "little"),
                    "slot": chunk[15],
                    "raw_hex": chunk.hex(),
                }
            )
        cursor += RELATION_ENTRY_LEN
    return entries


def _relation_entries_for_offsets(
    data: bytes,
    *,
    dob_offset: int,
    next_name_length_offset: int,
    tails: list[dict[str, int | str]],
) -> tuple[dict[str, int], list[dict[str, object]]]:
    relation_start = dob_offset + 0x20
    relation_end = next_name_length_offset
    if tails:
        relation_end = min(relation_end, int(tails[0]["tail_start"]))
    relation_window = {
        "start": relation_start,
        "end": relation_end,
    }
    relation_entries = _parse_relation_entries(data, relation_start, relation_end)
    return relation_window, relation_entries


def _relation_entries_for_person(data: bytes, person: dict[str, object]) -> tuple[dict[str, int], list[dict[str, object]]]:
    offsets = person["offsets"]
    return _relation_entries_for_offsets(
        data,
        dob_offset=int(offsets["dob_offset"]),
        next_name_length_offset=int(offsets["next_name_length_offset"]),
        tails=person.get("inline_secondary_tails", []),
    )


def resolve_inline_name_owner_for_offset(
    data: bytes,
    offset: int,
    *,
    radius: int = 0x4000,
) -> dict[str, object] | None:
    search_start = max(0, offset - radius)
    search_end = min(len(data), offset + radius)
    people = extract_inline_named_people(data, search_start=search_start, search_end=search_end)
    matches: list[tuple[int, dict[str, object], dict[str, object]]] = []

    for person in people:
        for tail in person.get("inline_secondary_tails", []):
            tail_start = int(tail["tail_start"])
            tail_end = int(tail["tail_end"])
            if tail_start <= offset < tail_end:
                distance = abs(offset - int(person["offsets"]["name_length_offset"]))
                matches.append((distance, person, tail))

    if not matches:
        return None

    matches.sort(key=lambda item: item[0])
    distance, person, tail = matches[0]
    relation_window, relation_entries = _relation_entries_for_person(data, person)
    return {
        "person_key": person["person_key"],
        "full_name": person["full_name"],
        "name_offset": person["offsets"]["name_offset"],
        "name_length_offset": person["offsets"]["name_length_offset"],
        "distance": distance,
        "relation_window": relation_window,
        "relation_entries": relation_entries,
        "tail": tail,
    }


def extract_inline_named_people(
    data: bytes,
    *,
    search_start: int = 0,
    search_end: int | None = None,
) -> list[dict[str, object]]:
    end = len(data) if search_end is None else min(search_end, len(data))
    people: list[dict[str, object]] = []
    anchors = _scan_inline_name_anchors(data, search_start=search_start, search_end=end)
    tail_markers = _scan_all_tail_markers(data, search_start, end)
    tail_index = 0

    for index, anchor in enumerate(anchors):
        name_length_offset = int(anchor["name_length_offset"])
        payload_start = int(anchor["name_offset"])
        payload_end = int(anchor["dob_offset"])
        nearby_dates = _nearby_dates_before_name(data, name_length_offset)
        raw_signature = _inline_post_dob_signature(data, payload_end)
        next_name_length_offset = (
            int(anchors[index + 1]["name_length_offset"])
            if index + 1 < len(anchors)
            else min(end, name_length_offset + DEFAULT_TAIL_SCAN_LIMIT)
        )
        while tail_index < len(tail_markers) and tail_markers[tail_index][0] < payload_end + 4:
            tail_index += 1
        local_tail_index = tail_index
        tails: list[dict[str, int | str]] = []
        while local_tail_index < len(tail_markers) and tail_markers[local_tail_index][0] < next_name_length_offset:
            tails.append(_build_tail_payload(tail_markers, local_tail_index, next_name_length_offset))
            local_tail_index += 1
        tail_index = local_tail_index
        evidence = ["inline_full_name", "inline_dob"]
        evidence.extend(
            f"nearby_date:{entry['value']}@0x{int(entry['offset']):08X}"
            for entry in nearby_dates[:6]
        )
        evidence.extend(
            f"tail:{str(tail['variant'])}@0x{int(tail['tail_start']):08X}"
            for tail in tails[:4]
        )
        relation_window, relation_entries = _relation_entries_for_offsets(
            data,
            dob_offset=payload_end,
            next_name_length_offset=next_name_length_offset,
            tails=tails,
        )

        people.append(
            {
                "person_key": f"frame3:person-name:0x{payload_start:08X}",
                "source": "inline_name_dob",
                "full_name": anchor["full_name"],
                "offsets": {
                    "name_length_offset": name_length_offset,
                    "name_offset": payload_start,
                    "dob_offset": payload_end,
                    "next_name_length_offset": next_name_length_offset,
                    "nearby_date_offsets": [int(entry["offset"]) for entry in nearby_dates[:6]],
                },
                "dob": anchor["dob"],
                "uid": None,
                "reputation": None,
                "ca": None,
                "pa": None,
                "personality": None,
                "name_refs": {},
                "inline_post_dob": raw_signature,
                "inline_secondary_tails": tails,
                "relation_window": relation_window,
                "relation_entries": relation_entries,
                "confidence": 0.82 if tails else (0.78 if nearby_dates else 0.72),
                "evidence": evidence,
            }
        )

    return people
