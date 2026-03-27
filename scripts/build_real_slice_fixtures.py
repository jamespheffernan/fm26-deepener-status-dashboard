#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fm_save_extract.inline_people import extract_inline_named_people


DEFAULT_SOURCE_DIR = Path("/tmp/fm26_phase2_frames")
DEFAULT_OUTPUT_DIR = ROOT / "tests" / "fixtures"
FIXTURE_VERSION = 1


@dataclass(frozen=True)
class SliceSpec:
    name: str
    source_frame: str
    start: int
    end: int
    files: tuple[str, ...]
    expected: dict[str, Any]


SLICE_SPECS: tuple[SliceSpec, ...] = (
    SliceSpec(
        name="xabi_contract_base",
        source_frame="base.frame3.bin",
        start=0x057C4800,
        end=0x057C8000,
        files=("real_xabi_contract_base.bin",),
        expected={
            "full_name": "Xabier Alonso Olano",
            "person_key": "frame3:person-name:0x000008C5",
            "wage": 165738,
            "start_date": "2025-06-01",
            "expiry_date": "2032-06-30",
            "notes": "Base contract variant for Xabi Alonso.",
        },
    ),
    SliceSpec(
        name="xabi_contract_raise",
        source_frame="xabi_raise.frame3.bin",
        start=0x057C4800,
        end=0x057C8000,
        files=("real_xabi_contract_raise.bin",),
        expected={
            "full_name": "Xabier Alonso Olano",
            "person_key": "frame3:person-name:0x00000996",
            "wage": 205738,
            "start_date": "2025-06-01",
            "expiry_date": "2032-06-30",
            "notes": "Raised wage variant for Xabi Alonso.",
        },
    ),
    SliceSpec(
        name="xabi_contract_expiry",
        source_frame="xabi_expiry.frame3.bin",
        start=0x057C4800,
        end=0x057C8000,
        files=("real_xabi_contract_expiry.bin",),
        expected={
            "full_name": "Xabier Alonso Olano",
            "person_key": "frame3:person-name:0x00000996",
            "wage": 205738,
            "start_date": "2025-06-01",
            "expiry_date": "2033-06-30",
            "notes": "Expiry-edited contract variant for Xabi Alonso.",
        },
    ),
    SliceSpec(
        name="jorge_staff_xabi_expiry",
        source_frame="xabi_expiry.frame3.bin",
        start=0x056C9A00,
        end=0x056CA400,
        files=("real_jorge_staff_xabi_expiry.bin",),
        expected={
            "full_name": "Jorge Manuel Domingues Maria Vital",
            "person_key": "frame3:person-name:0x000000C7",
            "working_with_youngsters": 6,
            "notes": "Pre-edit Jorge staff tail slice from xabi_expiry.",
        },
    ),
    SliceSpec(
        name="jorge_staff_squizzi_wwy",
        source_frame="squizzi_wwy.frame3.bin",
        start=0x056C9A00,
        end=0x056CA400,
        files=("real_jorge_staff_squizzi_wwy.bin",),
        expected={
            "full_name": "Jorge Manuel Domingues Maria Vital",
            "person_key": "frame3:person-name:0x000000C7",
            "working_with_youngsters": 20,
            "notes": "Squizzi WWY edit slice sharing the Jorge tail family.",
        },
    ),
    SliceSpec(
        name="control_athletic_family",
        source_frame="xabi_expiry.frame3.bin",
        start=0x056A0800,
        end=0x056A1800,
        files=("real_control_athletic_family.bin",),
        expected={
            "full_name": "Genar Andrinúa Kortabarria",
            "person_key": "frame3:person-name:0x00000CDC",
            "club_key_candidate": "frame3:club:0x0052AEE2",
            "notes": "Control slice with recurring Athletic Club relation tags and no intended edit.",
        },
    ),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build narrow real FM26 slice fixtures and manifest.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR, help="Directory containing source frame files.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory to write slice fixtures and manifest.")
    return parser


def _load_frame(source_dir: Path, source_frame: str) -> bytes:
    path = source_dir / source_frame
    if not path.exists():
        raise FileNotFoundError(f"missing source frame: {path}")
    return path.read_bytes()


def _collect_relation_tags(data: bytes) -> list[dict[str, object]]:
    people = extract_inline_named_people(data)
    counts: Counter[tuple[str, str, int, int]] = Counter()
    examples: dict[tuple[str, str, int, int], list[dict[str, object]]] = defaultdict(list)

    for person in people:
        for entry in person.get("relation_entries", []):
            key = (
                str(entry["tag"]),
                str(entry["ref_hex"]),
                int(entry["value"]),
                int(entry["slot"]),
            )
            counts[key] += 1
            if len(examples[key]) < 3:
                examples[key].append(
                    {
                        "person_key": person["person_key"],
                        "full_name": person["full_name"],
                        "offset": entry["offset"],
                    }
                )

    ordered = sorted(
        counts.items(),
        key=lambda item: (-item[1], item[0][0], item[0][1], item[0][2], item[0][3]),
    )
    return [
        {
            "tag": tag,
            "ref_hex": ref_hex,
            "value": value,
            "slot": slot,
            "count": count,
            "examples": examples[(tag, ref_hex, value, slot)],
        }
        for (tag, ref_hex, value, slot), count in ordered
    ]


def _write_slice(output_dir: Path, spec: SliceSpec, source_dir: Path) -> list[dict[str, object]]:
    data = _load_frame(source_dir, spec.source_frame)
    slice_bytes = data[spec.start:spec.end]
    tags = _collect_relation_tags(slice_bytes)

    for file_name in spec.files:
        (output_dir / file_name).write_bytes(slice_bytes)

    return tags


def build_manifest(source_dir: Path, output_dir: Path) -> dict[str, object]:
    source_frames = [
        {"name": "base.frame3.bin", "path": str(source_dir / "base.frame3.bin")},
        {"name": "xabi_raise.frame3.bin", "path": str(source_dir / "xabi_raise.frame3.bin")},
        {"name": "xabi_expiry.frame3.bin", "path": str(source_dir / "xabi_expiry.frame3.bin")},
        {"name": "squizzi_wwy.frame3.bin", "path": str(source_dir / "squizzi_wwy.frame3.bin")},
    ]

    slices: list[dict[str, object]] = []
    for spec in SLICE_SPECS:
        relation_tags = _write_slice(output_dir, spec, source_dir)
        slices.append(
            {
                "name": spec.name,
                "files": list(spec.files),
                "start": spec.start,
                "end": spec.end,
                "expected": spec.expected,
                "recurring_relation_tags": relation_tags,
            }
        )

    return {
        "fixture_version": FIXTURE_VERSION,
        "source_frames": source_frames,
        "slices": slices,
    }


def main() -> None:
    args = build_parser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(args.source_dir, args.output_dir)
    manifest_path = args.output_dir / "real_slice_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
