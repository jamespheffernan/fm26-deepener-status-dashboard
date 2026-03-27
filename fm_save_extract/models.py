from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Preamble:
    home_rep: int
    current_rep: int
    world_rep: int
    ca: int
    pa: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class NearbyValue:
    offset: int
    value: int | str

    def to_dict(self) -> dict[str, int | str]:
        return {"offset": self.offset, "value": self.value}


@dataclass(frozen=True)
class MetadataHit:
    keyword: str
    offset: int
    family: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


@dataclass(frozen=True)
class MetadataCluster:
    cluster_id: str
    start: int
    end: int
    families: list[str]
    keywords: list[str]
    hit_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PersonCandidate:
    block_start: int
    preamble: Preamble
    positions: dict[str, int]
    attributes_raw: dict[str, int]
    attributes_display: dict[str, int]
    uid: int | None
    uid_candidates: list[NearbyValue]
    dob: str | None
    dob_candidates: list[NearbyValue]
    personality: dict[str, int] | None
    name_refs: dict[str, list[int]]
    confidence: float
    evidence: list[str]
    known_match: str | None = None

    @property
    def person_key(self) -> str:
        if self.uid is not None:
            return f"uid:{self.uid}"
        return f"frame3:0x{self.block_start:08X}"

    @property
    def offsets(self) -> dict[str, int | list[int] | None]:
        personality_offset = None
        if self.personality is not None and "_offset" in self.personality:
            personality_offset = int(self.personality["_offset"])
        return {
            "block_start": self.block_start,
            "preamble_start": self.block_start - 0x1E,
            "uid_offset": self.uid_candidates[0].offset if self.uid_candidates else None,
            "dob_offsets": [candidate.offset for candidate in self.dob_candidates],
            "personality_offset": personality_offset,
        }

    def to_person_record(self) -> dict[str, object]:
        personality = None
        if self.personality is not None:
            personality = {key: value for key, value in self.personality.items() if not key.startswith("_")}
        return {
            "person_key": self.person_key,
            "source": "hybrid_block",
            "full_name": None,
            "offsets": self.offsets,
            "dob": self.dob,
            "uid": self.uid,
            "reputation": {
                "home": self.preamble.home_rep,
                "current": self.preamble.current_rep,
                "world": self.preamble.world_rep,
            },
            "ca": self.preamble.ca,
            "pa": self.preamble.pa,
            "personality": personality,
            "name_refs": self.name_refs,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }

    def to_player_record(self) -> dict[str, object]:
        return {
            "person_key": self.person_key,
            "positions": self.positions,
            "attributes_raw": self.attributes_raw,
            "attributes_display": self.attributes_display,
        }


@dataclass(frozen=True)
class DiffWindow:
    start: int
    end: int
    before_len: int
    after_len: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass
class ExtractionBundle:
    game_info: dict[str, object]
    clubs: list[dict[str, object]]
    people: list[dict[str, object]]
    players: list[dict[str, object]]
    staff_roles: list[dict[str, object]] = field(default_factory=list)
    club_links: list[dict[str, object]] = field(default_factory=list)
    contracts: list[dict[str, object]] = field(default_factory=list)
    unresolved_candidates: dict[str, object] = field(default_factory=dict)

    def to_dicts(self) -> dict[str, object]:
        return {
            "game_info.json": self.game_info,
            "clubs.json": self.clubs,
            "people.json": self.people,
            "players.json": self.players,
            "staff_roles.json": self.staff_roles,
            "club_links.json": self.club_links,
            "contracts.json": self.contracts,
            "unresolved_candidates.json": self.unresolved_candidates,
        }
