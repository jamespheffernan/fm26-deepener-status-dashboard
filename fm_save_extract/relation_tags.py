from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RelationPattern:
    tags: tuple[str, ...]
    relation_kind: str
    target_kind: str
    confidence: float
    target_hint: str | None = None


def _normalize_tag(entry: dict[str, object]) -> str | None:
    tag = entry.get("tag")
    if isinstance(tag, str) and tag.strip():
        value = tag.strip()
        if not value.lower().startswith("0x"):
            return value
        try:
            return f"0x{int(value, 16):08X}"
        except ValueError:
            return value

    tag_value = entry.get("tag_value")
    if isinstance(tag_value, int):
        return f"0x{tag_value:08X}"

    return None


RELATION_PATTERNS: tuple[RelationPattern, ...] = (
    RelationPattern(
        tags=("0x00080964", "0x00010364"),
        relation_kind="club_employment",
        target_kind="club",
        confidence=0.93,
        target_hint="club employment",
    ),
    RelationPattern(
        tags=("0x0001033C", "0x00010346"),
        relation_kind="staff_assignment",
        target_kind="team",
        confidence=0.88,
        target_hint="staff/team assignment",
    ),
    RelationPattern(
        tags=("0x00030164",),
        relation_kind="contract_reference",
        target_kind="contract",
        confidence=0.86,
        target_hint="contract reference",
    ),
)


def classify_relation_entry(entry: dict[str, object]) -> dict[str, object]:
    tag = _normalize_tag(entry)
    if tag is not None:
        for pattern in RELATION_PATTERNS:
            if tag in pattern.tags:
                result = {
                    "relation_kind": pattern.relation_kind,
                    "target_kind": pattern.target_kind,
                    "confidence": pattern.confidence,
                    "pattern_key": f"tag:{tag}",
                }
                if pattern.target_hint is not None:
                    result["target_hint"] = pattern.target_hint
                return result

        return {
            "relation_kind": "unknown",
            "target_kind": "unknown",
            "confidence": 0.10,
            "pattern_key": f"tag:{tag}",
        }

    return {
        "relation_kind": "unknown",
        "target_kind": "unknown",
        "confidence": 0.05,
        "pattern_key": "unknown",
    }
