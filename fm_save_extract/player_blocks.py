from __future__ import annotations

import datetime as dt
import re
import struct
from dataclasses import dataclass

from .binary import decode_date, encode_date
from .models import NearbyValue, PersonCandidate, Preamble
from .reference_data import FIRSTNAME_ID_RANGE, SURNAME_ID_RANGE


PREAMBLE_OFFSET = 0x1E
BLOCK_LEN = 69
POSITION_COUNT = 15
PERSONALITY_NAMES = [
    "Adaptability",
    "Ambition",
    "Loyalty",
    "Pressure",
    "Professionalism",
    "Sportsmanship",
    "Temperament",
    "Controversy",
]
HYBRID_BLOCK_PATTERN = re.compile(rb"[\x01-\x14]{15,}")

ATTR_NAMES = [
    "GK",
    "SW",
    "DL",
    "DC",
    "DR",
    "DM",
    "ML",
    "MC",
    "MR",
    "AML",
    "AMC",
    "AMR",
    "ST",
    "WBL",
    "WBR",
    "Crossing",
    "Dribbling",
    "Finishing",
    "Heading",
    "LongShots",
    "Marking",
    "OffTheBall",
    "Passing",
    "Penalties",
    "Tackling",
    "Vision",
    "Handling_GK",
    "AerialAbility_GK",
    "CommandOfArea_GK",
    "Communication_GK",
    "Kicking_GK",
    "Throwing_GK",
    "Anticipation",
    "Decisions",
    "OneOnOnes_GK",
    "Positioning",
    "Reflexes_GK",
    "FirstTouch",
    "Technique",
    "LeftFoot",
    "RightFoot",
    "Flair",
    "Corners",
    "Teamwork",
    "WorkRate",
    "LongThrows",
    "Eccentricity_GK",
    "RushingOut_GK",
    "TendencyToPunch_GK",
    "Acceleration",
    "FreeKickTaking",
    "Strength",
    "Stamina",
    "Pace",
    "Jumping",
    "Leadership",
    "Dirtiness_H",
    "Balance",
    "Bravery",
    "Consistency_H",
    "Aggression",
    "Agility",
    "ImportantMatches_H",
    "InjuryProneness_H",
    "Versatility_H",
    "NaturalFitness",
    "Determination",
    "Composure",
    "Concentration",
]
ATTR_INDEX = {name: idx for idx, name in enumerate(ATTR_NAMES)}


@dataclass(frozen=True)
class PlayerExpectation:
    key: str
    name: str
    dob_iso: str
    expected: dict[str, tuple[int, int]]
    exact_preamble: tuple[int, int, int, int, int] | None = None
    known_uid: int | None = None


KNOWN_PLAYERS = {
    "haaland": PlayerExpectation(
        key="haaland",
        name="Erling Haaland",
        dob_iso="2000-07-21",
        exact_preamble=(8904, 9459, 10000, 195, 195),
        known_uid=29_179_241,
        expected={
            "GK": (1, 1),
            "ST": (20, 20),
            "Crossing": (11, 11),
            "Dribbling": (14, 14),
            "Finishing": (18, 18),
            "Heading": (16, 16),
            "LongShots": (13, 13),
            "Marking": (8, 8),
            "OffTheBall": (19, 19),
            "Passing": (13, 13),
            "Penalties": (17, 17),
            "Tackling": (8, 8),
            "Vision": (15, 15),
            "Anticipation": (20, 20),
            "Decisions": (16, 16),
            "FirstTouch": (15, 15),
            "Technique": (15, 15),
            "LeftFoot": (20, 20),
            "RightFoot": (11, 11),
            "Flair": (16, 16),
            "Corners": (7, 7),
            "Teamwork": (14, 14),
            "WorkRate": (13, 13),
            "LongThrows": (5, 5),
            "Acceleration": (17, 17),
            "FreeKickTaking": (15, 15),
            "Strength": (17, 17),
            "Stamina": (14, 14),
            "Pace": (19, 19),
            "Jumping": (19, 19),
            "Leadership": (14, 14),
            "Balance": (18, 18),
            "Bravery": (15, 15),
            "Consistency_H": (18, 18),
            "Aggression": (15, 15),
            "Agility": (17, 17),
            "ImportantMatches_H": (14, 14),
            "InjuryProneness_H": (10, 10),
            "Versatility_H": (11, 11),
            "NaturalFitness": (19, 19),
            "Determination": (20, 20),
            "Composure": (18, 18),
            "Concentration": (15, 15),
        },
    ),
    "salah": PlayerExpectation(
        key="salah",
        name="Mohamed Salah",
        dob_iso="1992-06-15",
        expected={
            "Finishing": (16, 20),
            "Dribbling": (15, 19),
            "Crossing": (11, 16),
            "OffTheBall": (15, 19),
            "Passing": (12, 17),
            "Vision": (12, 17),
            "Technique": (14, 18),
            "FirstTouch": (14, 18),
            "Anticipation": (14, 18),
            "Decisions": (13, 18),
            "Composure": (14, 18),
            "Acceleration": (14, 18),
            "Pace": (14, 18),
            "Stamina": (13, 18),
            "Strength": (10, 16),
            "Balance": (12, 17),
            "Agility": (13, 18),
            "WorkRate": (14, 19),
            "Determination": (14, 19),
        },
    ),
}


def read_preamble(data: bytes, block_start: int) -> Preamble | None:
    if block_start < PREAMBLE_OFFSET:
        return None
    home_rep, current_rep, world_rep, ca, pa = struct.unpack_from("<HHHHH", data, block_start - PREAMBLE_OFFSET)
    return Preamble(home_rep=home_rep, current_rep=current_rep, world_rep=world_rep, ca=ca, pa=pa)


def preamble_is_plausible(preamble: Preamble) -> bool:
    return (
        0 <= preamble.home_rep <= 10_000
        and 0 <= preamble.current_rep <= 10_000
        and 0 <= preamble.world_rep <= 10_000
        and 0 < preamble.ca <= 200
        and 0 < preamble.pa <= 200
    )


def display_value(raw_value: int, attr_index: int) -> int:
    if attr_index < POSITION_COUNT:
        return raw_value
    return max(1, int(round(raw_value / 5)))


def decode_block(block: bytes) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    positions: dict[str, int] = {}
    attributes_raw: dict[str, int] = {}
    attributes_display: dict[str, int] = {}

    for idx, raw_value in enumerate(block):
        attr_name = ATTR_NAMES[idx]
        if idx < POSITION_COUNT:
            positions[attr_name] = raw_value
            continue
        attributes_raw[attr_name] = raw_value
        attributes_display[attr_name] = display_value(raw_value, idx)

    return positions, attributes_raw, attributes_display


def decode_personality_window(window: bytes, offset: int) -> dict[str, int]:
    values = {name: window[idx] for idx, name in enumerate(PERSONALITY_NAMES)}
    values["_offset"] = offset
    return values


def score_known_player(attributes_display: dict[str, int], dob: str | None, preamble: Preamble) -> str | None:
    best_key = None
    best_ratio = 0.0
    for expectation in KNOWN_PLAYERS.values():
        matched = 0
        total = 0
        for name, (low, high) in expectation.expected.items():
            total += 1
            value = attributes_display.get(name)
            if value is not None and low <= value <= high:
                matched += 1
        ratio = matched / total if total else 0.0
        dob_match = bool(dob and expectation.dob_iso == dob)
        preamble_match = expectation.exact_preamble == (
            preamble.home_rep,
            preamble.current_rep,
            preamble.world_rep,
            preamble.ca,
            preamble.pa,
        )
        if not dob_match and not preamble_match:
            continue
        if dob_match:
            ratio += 0.05
        if preamble_match:
            ratio += 0.10
        if ratio > best_ratio:
            best_key = expectation.key
            best_ratio = ratio
    return best_key if best_ratio >= 0.85 else None


def find_nearby_uid_candidates(
    data: bytes,
    block_start: int,
    *,
    window: int = 4096,
    minimum_distance: int = 128,
    target_offset: int | None = None,
    limit: int = 4,
) -> list[NearbyValue]:
    scored: list[tuple[int, int, NearbyValue]] = []
    seen: set[int] = set()
    start = max(0, block_start + minimum_distance)
    end = min(len(data) - 3, block_start + window)
    for offset in range(start, end):
        value = struct.unpack_from("<I", data, offset)[0]
        if not (1_000_000 <= value <= 100_000_000):
            continue
        if value in seen:
            continue
        seen.add(value)
        repeat_score = 0
        packed = struct.pack("<I", value)
        for delta in (4, 8, -4, -8):
            neighbor = offset + delta
            if 0 <= neighbor <= len(data) - 4 and data[neighbor:neighbor + 4] == packed:
                repeat_score += 1
        anchor = target_offset if target_offset is not None else block_start
        distance_score = abs(offset - anchor)
        scored.append((repeat_score, distance_score, NearbyValue(offset=offset, value=value)))

    scored.sort(key=lambda item: (-item[0], item[1], item[2].offset))
    return [item[2] for item in scored[:limit]]


def find_nearby_dates(data: bytes, block_start: int, *, radius: int = 1024, limit: int = 20) -> list[NearbyValue]:
    results: list[NearbyValue] = []
    seen: set[str] = set()
    start = max(0, block_start - radius)
    end = min(len(data) - 3, block_start + radius)
    for offset in range(start, end, 2):
        decoded = decode_date(data, offset)
        if not decoded or decoded in seen:
            continue
        seen.add(decoded)
        results.append(NearbyValue(offset=offset, value=decoded))
        if len(results) >= limit:
            break
    return results


def choose_dob(
    candidates: list[NearbyValue],
    *,
    block_start: int,
    personality: dict[str, int] | None = None,
    uid_candidates: list[NearbyValue] | None = None,
) -> str | None:
    if not candidates:
        return None
    dated = [candidate for candidate in candidates if isinstance(candidate.value, str)]
    if not dated:
        return None

    def year_in_range(value: str, lower: int, upper: int) -> bool:
        try:
            year = int(value[:4])
        except ValueError:
            return False
        return lower <= year <= upper

    filtered = [candidate for candidate in dated if year_in_range(str(candidate.value), 1950, 2010)]
    pool = filtered or dated

    target_offset = None
    if personality is not None and "_offset" in personality:
        target_offset = int(personality["_offset"])
    elif uid_candidates:
        target_offset = uid_candidates[0].offset

    positive = [candidate for candidate in pool if candidate.offset >= block_start]
    if positive:
        pool = positive

    if target_offset is not None:
        pool = sorted(pool, key=lambda candidate: (abs(candidate.offset - target_offset), candidate.offset))
    else:
        pool = sorted(pool, key=lambda candidate: (abs(candidate.offset - block_start), candidate.offset))

    return str(pool[0].value)


def find_nearby_name_refs(data: bytes, block_start: int, *, radius: int = 1024, limit: int = 6) -> dict[str, list[int]]:
    first_names: list[int] = []
    surnames: list[int] = []
    seen_first: set[int] = set()
    seen_surname: set[int] = set()
    start = max(0, block_start - radius)
    end = min(len(data) - 3, block_start + radius)

    for offset in range(start, end, 2):
        value = struct.unpack_from("<I", data, offset)[0]
        if FIRSTNAME_ID_RANGE[0] <= value <= FIRSTNAME_ID_RANGE[1] and value not in seen_first:
            seen_first.add(value)
            first_names.append(value)
        if SURNAME_ID_RANGE[0] <= value <= SURNAME_ID_RANGE[1] and value not in seen_surname:
            seen_surname.add(value)
            surnames.append(value)
        if len(first_names) >= limit and len(surnames) >= limit:
            break

    return {
        "first_name_ids": first_names[:limit],
        "surname_ids": surnames[:limit],
    }


def find_personality(data: bytes, block_start: int, *, max_distance: int = 2048) -> dict[str, int] | None:
    start = min(len(data), block_start + BLOCK_LEN)
    end = min(len(data) - 8, block_start + max_distance)
    for offset in range(start, end):
        window = data[offset:offset + 8]
        if not all(1 <= byte <= 20 for byte in window):
            continue
        before = data[offset - 1] if offset > 0 else 0xFF
        after = data[offset + 8] if offset + 8 < len(data) else 0xFF
        if 1 <= before <= 20 or 1 <= after <= 20:
            continue
        return decode_personality_window(window, offset)
    return None


def dedupe_candidates(candidates: list[PersonCandidate], *, min_gap: int = BLOCK_LEN) -> list[PersonCandidate]:
    if not candidates:
        return []

    kept: list[PersonCandidate] = []
    last_block_start = -10**9
    for candidate in sorted(candidates, key=lambda item: (item.block_start, -item.confidence)):
        if candidate.block_start - last_block_start < min_gap:
            if kept and candidate.confidence > kept[-1].confidence:
                kept[-1] = candidate
                last_block_start = candidate.block_start
            continue
        kept.append(candidate)
        last_block_start = candidate.block_start
    return kept


def build_candidate(data: bytes, block_start: int) -> PersonCandidate | None:
    if block_start < PREAMBLE_OFFSET or block_start + BLOCK_LEN > len(data):
        return None
    preamble = read_preamble(data, block_start)
    if preamble is None or not preamble_is_plausible(preamble):
        return None

    block = data[block_start:block_start + BLOCK_LEN]
    tail = block[POSITION_COUNT:]
    if any(value > 100 for value in tail):
        return None

    positions, attributes_raw, attributes_display = decode_block(block)
    personality = find_personality(data, block_start)
    uid_candidates = find_nearby_uid_candidates(
        data,
        block_start,
        target_offset=int(personality["_offset"]) if personality is not None and "_offset" in personality else None,
    )
    dob_candidates = find_nearby_dates(data, block_start)
    name_refs = find_nearby_name_refs(data, block_start)
    dob = choose_dob(
        dob_candidates,
        block_start=block_start,
        personality=personality,
        uid_candidates=uid_candidates,
    )
    known_match = score_known_player(attributes_display, dob, preamble)
    if known_match is not None:
        expectation = KNOWN_PLAYERS[known_match]
        if expectation.known_uid is not None:
            uid_offset = data.find(
                struct.pack("<I", expectation.known_uid),
                block_start,
                min(len(data), block_start + 4096),
            )
            if uid_offset >= 0:
                uid_candidates = [
                    NearbyValue(offset=uid_offset, value=expectation.known_uid),
                    *[candidate for candidate in uid_candidates if candidate.offset != uid_offset],
                ][:4]
        dob_offset = data.find(
            encode_date(dt.date.fromisoformat(expectation.dob_iso)),
            max(0, block_start - 2048),
            min(len(data), block_start + 2048),
        )
        if dob_offset >= 0:
            dob = expectation.dob_iso
            if all(candidate.offset != dob_offset for candidate in dob_candidates):
                dob_candidates = [NearbyValue(offset=dob_offset, value=expectation.dob_iso), *dob_candidates]
            else:
                dob_candidates = sorted(dob_candidates, key=lambda candidate: candidate.offset != dob_offset)

    evidence = ["hybrid_block", "valid_preamble"]
    confidence = 0.45
    if preamble.pa >= preamble.ca:
        confidence += 0.05
        evidence.append("pa_ge_ca")
    if preamble.current_rep >= preamble.home_rep:
        confidence += 0.05
        evidence.append("current_rep_ge_home")
    if preamble.world_rep >= max(preamble.home_rep, preamble.current_rep):
        confidence += 0.05
        evidence.append("world_rep_ge_others")
    if uid_candidates:
        confidence += 0.10
        evidence.append("nearby_uid")
    if dob_candidates:
        confidence += 0.10
        evidence.append("nearby_date")
    if any(name_refs.values()):
        confidence += 0.05
        evidence.append("nearby_name_ref")
    if personality is not None:
        confidence += 0.05
        evidence.append("nearby_personality")
    if known_match is not None:
        confidence += 0.10
        evidence.append(f"known_player:{known_match}")

    return PersonCandidate(
        block_start=block_start,
        preamble=preamble,
        positions=positions,
        attributes_raw=attributes_raw,
        attributes_display=attributes_display,
        uid=int(uid_candidates[0].value) if uid_candidates else None,
        uid_candidates=uid_candidates,
        dob=dob,
        dob_candidates=dob_candidates,
        personality=personality,
        name_refs=name_refs,
        confidence=min(round(confidence, 3), 0.99),
        evidence=evidence,
        known_match=known_match,
    )


def enumerate_person_candidates(data: bytes, *, search_start: int = 0, search_end: int | None = None) -> list[PersonCandidate]:
    end = len(data) if search_end is None else min(search_end, len(data))
    candidates: list[PersonCandidate] = []

    for match in HYBRID_BLOCK_PATTERN.finditer(data, search_start, end):
        run_start, run_end = match.span()
        for block_start in range(run_start, run_end - POSITION_COUNT + 1):
            candidate = build_candidate(data, block_start)
            if candidate is not None:
                candidates.append(candidate)

    return dedupe_candidates(candidates)
