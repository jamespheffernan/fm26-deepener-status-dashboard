from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfile
from typing import Any

from .parser import parse_export, slugify
from .types import ExportType


def resolve_input_files(path: str | Path) -> list[Path]:
    candidate = Path(path).expanduser().resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"Input path does not exist: {candidate}")
    if candidate.is_file():
        return [candidate]

    html_files = sorted(candidate.glob("*.html"), key=lambda item: item.stat().st_mtime)
    if not html_files:
        raise FileNotFoundError(f"No HTML files found in directory: {candidate}")
    return [item.resolve() for item in html_files]


def infer_export_type(bundle: dict[str, Any]) -> str:
    fields = set(bundle["summary"]["fields"])
    records = bundle.get("records", [])
    table_name = slugify(bundle["table_name"]).replace("-", "_")

    if {"average_rating", "uid", "club"}.issubset(fields):
        return ExportType.SQUAD.value
    if {
        "minimum_asking_price",
        "minimum_fee_release_clause",
        "minimum_foreign_club_release_clause",
    }.intersection(fields):
        return ExportType.PLAYER_SEARCH.value

    # Transfers: fee, selling_club, buying_club, status, transfer_type
    if {"fee", "selling_club", "buying_club"}.issubset(fields):
        return ExportType.TRANSFERS.value
    if {"fee"}.issubset(fields) and {"status", "transfer_type"}.intersection(fields):
        return ExportType.TRANSFERS.value

    # Staff: coaching, scouting, physiotherapy, role, job
    if {"coaching", "scouting", "physiotherapy"}.issubset(fields):
        return ExportType.STAFF.value
    if {"role", "job"}.issubset(fields) and {"coaching", "scouting"}.intersection(fields):
        return ExportType.STAFF.value

    # News: subject, sender, message, headline
    if {"subject", "headline"}.issubset(fields) or {"sender", "message"}.issubset(fields):
        return ExportType.NEWS.value

    # Competition stats: competition + statistical fields, distinct from squad (no uid/average_rating)
    if "competition" in fields and {"goals", "assists", "appearances"}.intersection(fields):
        if "uid" not in fields:
            return ExportType.COMPETITION_STATS.value

    # Schedule vs fixtures: both have date+opponent, but schedule has empty result/score
    if {"date", "opponent"}.issubset(fields) and {"result", "score", "competition"}.intersection(fields):
        has_populated_results = any(
            (record.get("result") or record.get("score"))
            for record in records
        )
        if has_populated_results:
            return ExportType.FIXTURES.value
        return ExportType.SCHEDULE.value

    if {"team", "played", "points"}.issubset(fields):
        return ExportType.LEAGUE_TABLE.value
    return table_name


def infer_club_name(datasets: dict[str, dict[str, Any]], exports_by_type: dict[str, list[str]]) -> str | None:
    # Primary: most common club in squad exports
    for key in exports_by_type.get(ExportType.SQUAD.value, []):
        clubs: Counter[str] = Counter()
        for record in datasets[key]["records"]:
            club = record.get("club")
            if isinstance(club, str) and club:
                clubs[club] += 1
        if clubs:
            return clubs.most_common(1)[0][0]

    # Fallback: home team from fixtures (venue == "H")
    for key in exports_by_type.get(ExportType.FIXTURES.value, []) + exports_by_type.get(ExportType.SCHEDULE.value, []):
        for record in datasets[key]["records"]:
            venue = record.get("venue")
            opponent = record.get("opponent")
            if isinstance(venue, str) and venue.strip().upper() == "H" and isinstance(opponent, str) and opponent:
                # In FM exports the opponent column at a home venue is the away team;
                # the exporting club is implied.  We cannot directly read the club name
                # from fixtures alone, so skip to the next fallback.
                break

    # Fallback: league table team that appears in squad-related exports
    squad_player_clubs: set[str] = set()
    for key in exports_by_type.get(ExportType.SQUAD.value, []):
        for record in datasets[key]["records"]:
            club = record.get("club")
            if isinstance(club, str) and club:
                squad_player_clubs.add(club)

    if squad_player_clubs:
        for key in exports_by_type.get(ExportType.LEAGUE_TABLE.value, []):
            for record in datasets[key]["records"]:
                team = record.get("team")
                if isinstance(team, str) and team in squad_player_clubs:
                    return team

    # Fallback: first team in the league table (usually sorted by position)
    for key in exports_by_type.get(ExportType.LEAGUE_TABLE.value, []):
        for record in datasets[key]["records"]:
            team = record.get("team")
            if isinstance(team, str) and team:
                return team

    # Fallback: club mentioned in news subject/headline
    for key in exports_by_type.get(ExportType.NEWS.value, []):
        for record in datasets[key]["records"]:
            for field in ("subject", "headline"):
                value = record.get(field)
                if isinstance(value, str) and value:
                    return value.split(" - ")[0].strip()

    return None


def build_snapshot(
    input_path: str | Path,
    *,
    save_name: str | None = None,
    club_name: str | None = None,
    manager_name: str | None = None,
) -> dict[str, Any]:
    source = Path(input_path).expanduser().resolve()
    files = resolve_input_files(source)

    exports: list[dict[str, Any]] = []
    datasets: dict[str, dict[str, Any]] = {}
    exports_by_type: dict[str, list[str]] = {}
    type_counts: Counter[str] = Counter()

    for file_path in files:
        bundle = parse_export(file_path)
        export_type = infer_export_type(bundle)
        type_counts[export_type] += 1
        dataset_key = export_type if type_counts[export_type] == 1 else f"{export_type}_{type_counts[export_type]}"

        dataset = {
            "key": dataset_key,
            "export_type": export_type,
            "source_file": bundle["source_file"],
            "table_name": bundle["table_name"],
            "exported_at": bundle["exported_at"],
            "columns": bundle["columns"],
            "summary": bundle["summary"],
            "records": bundle["records"],
        }
        datasets[dataset_key] = dataset
        exports_by_type.setdefault(export_type, []).append(dataset_key)
        exports.append(
            {
                "key": dataset_key,
                "export_type": export_type,
                "source_file": bundle["source_file"],
                "table_name": bundle["table_name"],
                "record_count": bundle["summary"]["row_count"],
                "fields": bundle["summary"]["fields"],
            }
        )

    inferred_club_name = club_name or infer_club_name(datasets, exports_by_type)
    snapshot_name = save_name or source.stem
    summary = {
        "save_name": snapshot_name,
        "club_name": inferred_club_name,
        "manager_name": manager_name,
        "source_path": str(source),
        "export_count": len(exports),
        "total_record_count": sum(dataset["summary"]["row_count"] for dataset in datasets.values()),
        "exports_by_type": {export_type: len(keys) for export_type, keys in exports_by_type.items()},
    }

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "save_name": snapshot_name,
        "club_name": inferred_club_name,
        "manager_name": manager_name,
        "source_path": str(source),
        "exports": exports,
        "exports_by_type": exports_by_type,
        "datasets": datasets,
        "summary": summary,
    }


def get_primary_dataset(snapshot: dict[str, Any], export_type: str) -> dict[str, Any] | None:
    keys = snapshot.get("exports_by_type", {}).get(export_type, [])
    if not keys:
        return None
    return snapshot["datasets"][keys[-1]]


def write_snapshot_bundle(snapshot: dict[str, Any], output_dir: str | Path, name: str | None = None) -> dict[str, str]:
    target_dir = Path(output_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    base_name = slugify(name or snapshot["save_name"] or "snapshot")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{base_name}-{timestamp}"

    snapshot_path = target_dir / f"{prefix}.snapshot.json"
    summary_path = target_dir / f"{prefix}.snapshot-summary.json"
    latest_snapshot_path = target_dir / "latest.snapshot.json"
    latest_summary_path = target_dir / "latest.snapshot-summary.json"

    with snapshot_path.open("w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(snapshot["summary"], handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    copyfile(snapshot_path, latest_snapshot_path)
    copyfile(summary_path, latest_summary_path)

    return {
        "snapshot_json": str(snapshot_path),
        "summary_json": str(summary_path),
        "latest_snapshot_json": str(latest_snapshot_path),
        "latest_summary_json": str(latest_summary_path),
    }

