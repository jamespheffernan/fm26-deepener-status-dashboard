from __future__ import annotations

import argparse
from pathlib import Path

from .extractor import extract_world_state, load_input_frame, write_bundle, write_reference_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract first-pass FM26 world state from a save or raw frame.")
    parser.add_argument("--input", required=True, help="Path to a .fm save or raw frame .bin file")
    parser.add_argument("--output-dir", default="output/world", help="Directory for extractor JSON outputs")
    parser.add_argument("--raw", action="store_true", help="Treat input as an already-decompressed raw frame")
    parser.add_argument(
        "--diff-frame",
        action="append",
        default=[],
        help="Optional comparison raw frame(s) for supervised diff summaries",
    )
    parser.add_argument(
        "--emit-reference-tables",
        action="store_true",
        help="Also write firstnames.json and surnames.json from the frame",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    data = load_input_frame(args.input, raw=args.raw)
    diff_frames = [(Path(path).stem, load_input_frame(path, raw=True)) for path in args.diff_frame]
    bundle, reference_payload = extract_world_state(
        data,
        diff_frames=diff_frames,
        reference_tables=args.emit_reference_tables,
    )

    output_dir = Path(args.output_dir)
    write_bundle(output_dir, bundle)
    write_reference_payload(output_dir, reference_payload)


if __name__ == "__main__":
    main()
