from __future__ import annotations

import re

from .binary import read_length_prefixed_string
from .binary import decode_date
from .metadata import find_diff_offsets_chunked, group_diff_offsets


PRINTABLE_STRING_RE = re.compile(rb"[\x20-\x7e]{6,}")
STAFF_FAMILY_MARKER = bytes.fromhex("02 40 10 00 00 00 00")
STAFF_VECTOR_PREAMBLE_LEN = 0x20
STAFF_VECTOR_LEN = 0x40


def _resolve_frame(diff_frames: dict[str, bytes], token: str) -> bytes | None:
    if token in diff_frames:
        return diff_frames[token]
    for label, data in diff_frames.items():
        if token in label:
            return data
    return None


def _extract_length_prefixed_strings_near_offset(data: bytes, center: int, *, radius: int = 256) -> dict[str, int]:
    start = max(0, center - radius)
    end = min(len(data), center + radius)
    matches: dict[str, int] = {}
    for offset in range(start, end):
        text, consumed = read_length_prefixed_string(data, offset, max_length=80)
        if not text or consumed <= 4:
            continue
        if " " not in text:
            continue
        if not any(character.isalpha() for character in text):
            continue
        matches[text] = offset + 4
    return matches


def _extract_strings_near_offset(data: bytes, center: int, *, radius: int = 256) -> dict[str, int]:
    start = max(0, center - radius)
    end = min(len(data), center + radius)
    matches = _extract_length_prefixed_strings_near_offset(data, center, radius=radius)
    for match in PRINTABLE_STRING_RE.finditer(data[start:end]):
        text = match.group().decode("utf-8", errors="ignore")
        if text in matches:
            continue
        if " " not in text:
            continue
        if not any(character.isalpha() for character in text):
            continue
        matches[text] = start + match.start()
    return matches


def _find_common_name_near_diff(reference: bytes, modified: bytes, diff_window_start: int) -> tuple[str, int, int] | None:
    reference_prefixed = _extract_length_prefixed_strings_near_offset(reference, diff_window_start)
    modified_prefixed = _extract_length_prefixed_strings_near_offset(modified, diff_window_start)
    common_prefixed = sorted(set(reference_prefixed) & set(modified_prefixed), key=len, reverse=True)
    for text in common_prefixed:
        if len(text.split()) < 2:
            continue
        return text, reference_prefixed[text], modified_prefixed[text]

    reference_strings = _extract_strings_near_offset(reference, diff_window_start)
    modified_strings = _extract_strings_near_offset(modified, diff_window_start)
    common = sorted(set(reference_strings) & set(modified_strings), key=len, reverse=True)
    for text in common:
        if len(text.split()) < 2:
            continue
        return text, reference_strings[text], modified_strings[text]
    return None


def _relative_diff_windows(
    reference: bytes,
    modified: bytes,
    reference_anchor: int,
    modified_anchor: int,
    *,
    before: int = 256,
    after: int = 256,
) -> list[tuple[int, int, int, int]]:
    ref_window = reference[reference_anchor - before:reference_anchor + after]
    mod_window = modified[modified_anchor - before:modified_anchor + after]
    offsets = find_diff_offsets_chunked(ref_window, mod_window, max_diffs=512)
    windows = group_diff_offsets(offsets, gap=4)
    return [
        (
            window.start - before,
            window.end - before,
            reference_anchor + (window.start - before),
            modified_anchor + (window.start - before),
        )
        for window in windows
    ]


def _decode_date_at(data: bytes, offset: int) -> str | None:
    if offset < 0 or offset + 4 > len(data):
        return None
    return decode_date(data, offset)


def decode_contracts_from_diff_frames(base: bytes, diff_frames: dict[str, bytes]) -> list[dict[str, object]]:
    raise_frame = _resolve_frame(diff_frames, "xabi_raise")
    expiry_frame = _resolve_frame(diff_frames, "xabi_expiry")
    if raise_frame is None or expiry_frame is None:
        return []

    expiry_offsets = find_diff_offsets_chunked(raise_frame, expiry_frame, max_diffs=256)
    expiry_windows = group_diff_offsets(expiry_offsets, gap=4)
    if not expiry_windows:
        return []

    common_name = _find_common_name_near_diff(raise_frame, expiry_frame, expiry_windows[0].start)
    if common_name is None:
        return []
    full_name, raise_name_offset, expiry_name_offset = common_name

    base_name_offset = base.find(full_name.encode("utf-8"))
    if base_name_offset < 0:
        return []

    aligned_windows = _relative_diff_windows(base, raise_frame, base_name_offset, raise_name_offset)
    if not aligned_windows:
        return []

    wage_relative_offset = None
    previous_wage = None
    current_wage = None
    for rel_start, _, base_field_offset, raise_field_offset in aligned_windows:
        base_value = int.from_bytes(base[base_field_offset:base_field_offset + 4], "little")
        raise_value = int.from_bytes(raise_frame[raise_field_offset:raise_field_offset + 4], "little")
        if 0 < abs(raise_value - base_value) <= 1_000_000:
            wage_relative_offset = rel_start
            previous_wage = base_value
            current_wage = raise_value
            break

    expiry_window = expiry_windows[0]
    expiry_relative_offset = expiry_window.start - raise_name_offset
    previous_expiry = _decode_date_at(raise_frame, expiry_window.start)
    current_expiry = _decode_date_at(expiry_frame, expiry_window.start)
    start_date = _decode_date_at(expiry_frame, expiry_window.start + 4)

    if wage_relative_offset is None or previous_wage is None or current_wage is None:
        return []
    if previous_expiry is None or current_expiry is None:
        return []

    person_key = f"frame3:person-name:0x{base_name_offset:08X}"
    contract_key = f"frame3:contract:0x{base_name_offset:08X}"

    return [
        {
            "contract_key": contract_key,
            "person_key": person_key,
            "club_key": None,
            "start_date": start_date,
            "expiry_date": current_expiry,
            "wage": current_wage,
            "bonuses": None,
            "clauses": None,
            "loan_terms": None,
            "confidence": 0.95,
            "evidence": [
                f"name:{full_name}",
                f"base_name_offset:0x{base_name_offset:08X}",
                f"modified_name_offset:0x{expiry_name_offset:08X}",
                f"wage_offset_rel:{wage_relative_offset}",
                f"wage_previous:{previous_wage}",
                f"wage_current:{current_wage}",
                f"expiry_offset_rel:{expiry_relative_offset}",
                f"expiry_previous:{previous_expiry}",
                f"expiry_current:{current_expiry}",
            ],
        }
    ]


def decode_staff_roles_from_diff_frames(diff_frames: dict[str, bytes]) -> list[dict[str, object]]:
    before = _resolve_frame(diff_frames, "xabi_expiry")
    after = _resolve_frame(diff_frames, "squizzi_wwy")
    if before is None or after is None:
        return []
    diff_offsets = find_diff_offsets_chunked(before, after, max_diffs=256)
    if not diff_offsets:
        return []

    changed_offset = diff_offsets[0]
    previous_value = before[changed_offset]
    current_value = after[changed_offset]
    if not (1 <= previous_value <= 20 and 1 <= current_value <= 20):
        return []

    family_start = after.rfind(
        STAFF_FAMILY_MARKER,
        max(0, changed_offset - 0x400),
        changed_offset + 1,
    )
    if family_start < 0:
        family_start = changed_offset

    vector_start = family_start + STAFF_VECTOR_PREAMBLE_LEN
    vector_end = vector_start + STAFF_VECTOR_LEN
    changed_bytes = [
        {
            "offset": offset,
            "relative_offset": offset - vector_start,
            "before": before[offset],
            "after": after[offset],
        }
        for offset in diff_offsets
        if vector_start <= offset < vector_end
    ]
    relative_offset = changed_offset - vector_start

    return [
        {
            "person_key": f"frame3:staff:0x{family_start:08X}",
            "role_flags": {},
            "staff_attributes": {
                "WorkingWithYoungsters": current_value,
            },
            "club_link_refs": [],
            "confidence": 0.88,
            "vector_start": vector_start,
            "vector_length": STAFF_VECTOR_LEN,
            "changed_bytes": changed_bytes,
            "evidence": [
                "diff_frame:squizzi_wwy",
                f"family_start:0x{family_start:08X}",
                f"vector_start:0x{vector_start:08X}",
                f"vector_end:0x{vector_end - 1:08X}",
                f"changed_offset:0x{changed_offset:08X}",
                f"working_with_youngsters_rel:+0x{relative_offset:02X}",
                f"previous_value:{previous_value}",
                f"current_value:{current_value}",
                *[
                    "changed_byte:+0x{rel:02X}:{before}->{after}".format(
                        rel=entry["relative_offset"],
                        before=entry["before"],
                        after=entry["after"],
                    )
                    for entry in changed_bytes
                ],
            ],
        }
    ]


def summarize_diff_frames(base: bytes, diff_frames: dict[str, bytes]) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for label, data in diff_frames.items():
        offsets = find_diff_offsets_chunked(base, data, max_diffs=512)
        windows = group_diff_offsets(offsets, gap=4)
        summaries.append(
            {
                "label": label,
                "same_length": len(base) == len(data),
                "diff_offset_count": len(offsets),
                "windows": [window.to_dict() for window in windows[:64]],
            }
        )
    return summaries


def summarize_pairwise_diff_frames(diff_frames: list[tuple[str, bytes]]) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []

    for (left_label, left_data), (right_label, right_data) in zip(diff_frames, diff_frames[1:]):
        offsets = find_diff_offsets_chunked(left_data, right_data, max_diffs=512)
        windows = group_diff_offsets(offsets, gap=4)
        summary: dict[str, object] = {
            "left_label": left_label,
            "right_label": right_label,
            "same_length": len(left_data) == len(right_data),
            "diff_offset_count": len(offsets),
            "windows": [window.to_dict() for window in windows[:64]],
        }

        if offsets and len(offsets) <= 64:
            summary["changed_bytes"] = [
                {
                    "offset": offset,
                    "before": left_data[offset],
                    "after": right_data[offset],
                }
                for offset in offsets
            ]

        if windows:
            common_name = _find_common_name_near_diff(left_data, right_data, windows[0].start)
            if common_name is not None:
                full_name, left_offset, right_offset = common_name
                summary["common_name"] = {
                    "text": full_name,
                    "left_offset": left_offset,
                    "right_offset": right_offset,
                }

        summaries.append(summary)

    return summaries
