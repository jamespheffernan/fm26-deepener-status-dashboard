from __future__ import annotations

import argparse
import json
from pathlib import Path

from .parser import parse_export, write_output_bundle
from .prompts import build_prompt_pack, write_prompt_pack
from .snapshot import build_snapshot, write_snapshot_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m fm_html_extract",
        description="Parse Football Manager HTML exports into clean CSV and structured JSON.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to an exported FM HTML file, or a directory containing HTML exports.",
    )
    parser.add_argument(
        "--output-dir",
        default="./artifacts/html_exports",
        help="Directory where parsed outputs should be written.",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Optional base name for the generated files.",
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print the generated summary JSON to stdout after writing files.",
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Parse every HTML export in the input directory and assemble a combined snapshot.",
    )
    parser.add_argument(
        "--generate-prompts",
        action="store_true",
        help="Generate LLM-ready prompt files from a combined snapshot.",
    )
    parser.add_argument(
        "--save-name",
        default=None,
        help="Optional save name to embed in snapshot and prompt outputs.",
    )
    parser.add_argument(
        "--club-name",
        default=None,
        help="Optional club name override for snapshot and prompt outputs.",
    )
    parser.add_argument(
        "--manager-name",
        default=None,
        help="Optional manager name/context for prompt generation.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.snapshot:
        snapshot = build_snapshot(
            args.input,
            save_name=args.save_name,
            club_name=args.club_name,
            manager_name=args.manager_name,
        )
        outputs = write_snapshot_bundle(snapshot, args.output_dir, args.name or snapshot["save_name"])
        print(f"Built snapshot from: {snapshot['source_path']}")
        print(f"Wrote snapshot JSON: {outputs['snapshot_json']}")
        print(f"Wrote snapshot summary JSON: {outputs['summary_json']}")
        print(f"Updated latest snapshot bundle in: {Path(args.output_dir).expanduser().resolve()}")

        if args.generate_prompts:
            prompt_pack = build_prompt_pack(snapshot)
            prompt_outputs = write_prompt_pack(prompt_pack, args.output_dir, args.name or snapshot["save_name"])
            for filename in sorted(prompt_pack):
                print(f"Wrote prompt: {prompt_outputs[filename]}")

        if args.print_summary:
            print(json.dumps(snapshot["summary"], indent=2, ensure_ascii=False))

        return 0

    bundle = parse_export(args.input)
    outputs = write_output_bundle(bundle, args.output_dir, args.name)

    print(f"Parsed: {bundle['source_file']}")
    print(f"Wrote clean CSV: {outputs['clean_csv']}")
    print(f"Wrote records JSON: {outputs['records_json']}")
    print(f"Wrote summary JSON: {outputs['summary_json']}")
    print(f"Updated latest bundle in: {Path(args.output_dir).expanduser()}")

    if args.print_summary:
        print(json.dumps(bundle["summary"], indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
