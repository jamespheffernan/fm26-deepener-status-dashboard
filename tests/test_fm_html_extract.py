from __future__ import annotations

import csv
import json
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from fm_html_extract.parser import parse_export, parse_money_value, resolve_input_path
from fm_html_extract.prompts import build_prompt_pack
from fm_html_extract.snapshot import build_snapshot, infer_export_type


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


class FMHTMLExtractTests(unittest.TestCase):
    def test_parse_export_normalizes_duplicate_headers_and_types(self) -> None:
        bundle = parse_export(FIXTURES / "squad_export.html")

        self.assertEqual(bundle["summary"]["row_count"], 2)
        self.assertEqual(
            [column["field"] for column in bundle["columns"]],
            [
                "injury_status",
                "name",
                "age",
                "wage",
                "transfer_value",
                "nationality",
                "second_nationality",
                "position",
                "average_rating",
                "height_cm",
                "jumping_reach",
                "natural_fitness",
                "uid",
                "club",
            ],
        )

        first = bundle["records"][0]
        second = bundle["records"][1]

        self.assertEqual(first["name"], "Player 1")
        self.assertEqual(first["age"], 26)
        self.assertEqual(first["average_rating"], 7.12)
        self.assertEqual(first["height_cm"], 169)
        self.assertEqual(first["natural_fitness"], 13)
        self.assertEqual(first["wage_min"], 50000)
        self.assertEqual(first["wage_max"], 50000)
        self.assertEqual(first["wage_period"], "week")
        self.assertEqual(second["transfer_value_min"], 600000)
        self.assertEqual(second["transfer_value_max"], 1200000)

    def test_resolve_input_path_uses_latest_html_in_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            older = temp_path / "older.html"
            newer = temp_path / "newer.html"
            older.write_text("<html></html>", encoding="utf-8")
            time.sleep(0.02)
            newer.write_text("<html></html>", encoding="utf-8")

            self.assertEqual(resolve_input_path(temp_path), newer.resolve())

    def test_parse_money_value_handles_ranges(self) -> None:
        parsed = parse_money_value("£600K - £1.2M")

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["currency"], "GBP")
        self.assertEqual(parsed["min"], 600000)
        self.assertEqual(parsed["max"], 1200000)

    def test_infer_export_type_classifies_common_exports(self) -> None:
        self.assertEqual(infer_export_type(parse_export(FIXTURES / "squad_export.html")), "squad")
        self.assertEqual(infer_export_type(parse_export(FIXTURES / "player_search_export.html")), "player_search")
        self.assertEqual(infer_export_type(parse_export(FIXTURES / "fixtures_export.html")), "fixtures")
        self.assertEqual(infer_export_type(parse_export(FIXTURES / "league_table_export.html")), "league_table")

    def test_infer_export_type_classifies_new_exports(self) -> None:
        self.assertEqual(infer_export_type(parse_export(FIXTURES / "transfers_export.html")), "transfers")
        self.assertEqual(infer_export_type(parse_export(FIXTURES / "staff_export.html")), "staff")
        self.assertEqual(infer_export_type(parse_export(FIXTURES / "schedule_export.html")), "schedule")
        self.assertEqual(infer_export_type(parse_export(FIXTURES / "news_export.html")), "news")

    def test_new_prompt_packs_generated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            for fixture in (
                "squad_export.html",
                "player_search_export.html",
                "fixtures_export.html",
                "league_table_export.html",
                "transfers_export.html",
                "schedule_export.html",
            ):
                shutil.copyfile(FIXTURES / fixture, temp_path / fixture)
                time.sleep(0.01)

            snapshot = build_snapshot(temp_path, manager_name="Cesar Jules")
            prompts = build_prompt_pack(snapshot)

            self.assertIn("fan-forum.prompt.md", prompts)
            self.assertIn("newspaper-back-page.prompt.md", prompts)
            self.assertIn("pre-match-preview.prompt.md", prompts)
            self.assertIn("transfer-rumours.prompt.md", prompts)

            # Fan forum should reference the club
            self.assertIn("Cambridge", prompts["fan-forum.prompt.md"])
            # Newspaper should have headline instructions
            self.assertIn("headline", prompts["newspaper-back-page.prompt.md"].lower())
            # Preview should reference schedule or fixture data
            preview = prompts["pre-match-preview.prompt.md"]
            self.assertTrue("PSG" in preview or "Bolton" in preview)
            # Rumours should reference transfer targets
            self.assertIn("Prospect 1", prompts["transfer-rumours.prompt.md"])

    def test_build_snapshot_and_prompt_pack_from_export_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            for fixture in (
                "squad_export.html",
                "player_search_export.html",
                "fixtures_export.html",
                "league_table_export.html",
            ):
                shutil.copyfile(FIXTURES / fixture, temp_path / fixture)
                time.sleep(0.01)

            snapshot = build_snapshot(temp_path, manager_name="James Heffernan")
            prompts = build_prompt_pack(snapshot)

            self.assertEqual(snapshot["club_name"], "Cambridge")
            self.assertEqual(snapshot["summary"]["exports_by_type"]["squad"], 1)
            self.assertEqual(snapshot["summary"]["exports_by_type"]["fixtures"], 1)
            self.assertIn("Bolton", prompts["match-report.prompt.md"])
            self.assertIn("Prospect 1", prompts["transfer-briefing.prompt.md"])
            self.assertIn("James Heffernan", prompts["press-conference.prompt.md"])

    def test_cli_writes_expected_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "fm_html_extract",
                    "--input",
                    str(FIXTURES / "player_search_export.html"),
                    "--output-dir",
                    temp_dir,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            latest_summary = Path(temp_dir) / "latest.summary.json"
            latest_clean = Path(temp_dir) / "latest.clean.csv"
            latest_records = Path(temp_dir) / "latest.records.json"

            self.assertTrue(latest_summary.exists())
            self.assertTrue(latest_clean.exists())
            self.assertTrue(latest_records.exists())

            summary = json.loads(latest_summary.read_text(encoding="utf-8"))
            self.assertEqual(summary["row_count"], 1)

            with latest_clean.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["club"], "Unión (SF)")

    def test_cli_snapshot_mode_writes_snapshot_and_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as export_dir, tempfile.TemporaryDirectory() as output_dir:
            export_path = Path(export_dir)
            for fixture in (
                "squad_export.html",
                "player_search_export.html",
                "fixtures_export.html",
                "league_table_export.html",
            ):
                shutil.copyfile(FIXTURES / fixture, export_path / fixture)
                time.sleep(0.01)

            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "fm_html_extract",
                    "--input",
                    export_dir,
                    "--output-dir",
                    output_dir,
                    "--snapshot",
                    "--generate-prompts",
                    "--manager-name",
                    "James Heffernan",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((Path(output_dir) / "latest.snapshot.json").exists())
            self.assertTrue((Path(output_dir) / "latest.match-report.prompt.md").exists())
            snapshot = json.loads((Path(output_dir) / "latest.snapshot-summary.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["club_name"], "Cambridge")


if __name__ == "__main__":
    unittest.main()
