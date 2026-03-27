from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .relation_tags import classify_relation_entry


@dataclass(frozen=True)
class FixtureBackedClubPattern:
    club_key: str
    club_name: str
    target_confidence: float


_FIXTURE_BACKED_CLUB_PATTERNS: dict[tuple[str, str | None, int | None], FixtureBackedClubPattern] = {
    # Athletic Club control slice: repeated across a Bilbao/Athletic staff neighborhood.
    ("0x00080964", "5000ff3f", 4): FixtureBackedClubPattern(
        club_key="frame3:club:0x0052AEE2",
        club_name="Athletic Club",
        target_confidence=0.97,
    ),
    ("0x00010364", "4e00ff3f", 4): FixtureBackedClubPattern(
        club_key="frame3:club:0x0052AEE2",
        club_name="Athletic Club",
        target_confidence=0.96,
    ),
    ("0x00010364", "4e00ff70", 4): FixtureBackedClubPattern(
        club_key="frame3:club:0x0052AEE2",
        club_name="Athletic Club",
        target_confidence=0.82,
    ),
    ("0x00010364", "4e00ff7a", 4): FixtureBackedClubPattern(
        club_key="frame3:club:0x0052AEE2",
        club_name="Athletic Club",
        target_confidence=0.80,
    ),
}


def resolve_relation(entry: dict[str, object], clubs: Iterable[dict[str, object]]) -> dict[str, object]:
    typed = classify_relation_entry(entry)
    resolved = dict(typed)

    club_key = None
    if typed.get("target_kind") == "club":
        pattern = _FIXTURE_BACKED_CLUB_PATTERNS.get(
            (
                str(entry.get("tag")),
                str(entry.get("ref_hex")) if entry.get("ref_hex") is not None else None,
                int(entry["value"]) if isinstance(entry.get("value"), int) else None,
            )
        )
        if pattern is not None:
            club_key = _find_club_key(clubs, pattern.club_name) or pattern.club_key
            resolved["target_label"] = pattern.club_name
            resolved["resolution_kind"] = "fixture_backed_club_pattern"
            resolved["target_confidence"] = pattern.target_confidence

    resolved["target_key"] = club_key
    if typed.get("target_kind") == "club":
        resolved["club_key"] = club_key
    return resolved


def _find_club_key(clubs: Iterable[dict[str, object]], expected_name: str) -> str | None:
    matches = [club for club in clubs if club.get("full_name") == expected_name]
    if not matches:
        return None
    matches.sort(key=lambda club: int(club.get("offset", 10**12)))
    return str(matches[0]["club_key"])
