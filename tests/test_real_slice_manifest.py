from __future__ import annotations

import json
import unittest
from pathlib import Path

from fm_save_extract.inline_people import extract_inline_named_people


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
MANIFEST_PATH = FIXTURES / "real_slice_manifest.json"


def load_manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


class RealSliceManifestTests(unittest.TestCase):
    def test_manifest_shape_is_locked(self) -> None:
        manifest = load_manifest()

        self.assertEqual(set(manifest.keys()), {"fixture_version", "source_frames", "slices"})
        self.assertEqual(manifest["fixture_version"], 1)
        self.assertIsInstance(manifest["source_frames"], list)
        self.assertIsInstance(manifest["slices"], list)
        self.assertGreaterEqual(len(manifest["slices"]), 6)

        for source_frame in manifest["source_frames"]:
            self.assertEqual(set(source_frame.keys()), {"name", "path"})
            self.assertTrue(source_frame["name"])
            self.assertTrue(source_frame["path"])

        for slice_entry in manifest["slices"]:
            self.assertEqual(
                set(slice_entry.keys()),
                {"name", "files", "start", "end", "expected", "recurring_relation_tags"},
            )
            self.assertIsInstance(slice_entry["name"], str)
            self.assertIsInstance(slice_entry["files"], list)
            self.assertGreaterEqual(len(slice_entry["files"]), 1)
            self.assertIsInstance(slice_entry["start"], int)
            self.assertIsInstance(slice_entry["end"], int)
            self.assertGreater(slice_entry["end"], slice_entry["start"])
            self.assertIsInstance(slice_entry["expected"], dict)
            self.assertIsInstance(slice_entry["recurring_relation_tags"], list)

    def test_slice_files_load_with_expected_lengths(self) -> None:
        manifest = load_manifest()

        for slice_entry in manifest["slices"]:
            size = slice_entry["end"] - slice_entry["start"]
            for file_name in slice_entry["files"]:
                path = FIXTURES / file_name
                self.assertTrue(path.exists(), file_name)
                blob = path.read_bytes()
                self.assertEqual(len(blob), size, file_name)

    def test_manifest_contains_the_expected_control_and_edit_families(self) -> None:
        manifest = load_manifest()
        slices_by_name = {entry["name"]: entry for entry in manifest["slices"]}

        self.assertIn("xabi_contract_base", slices_by_name)
        self.assertIn("xabi_contract_raise", slices_by_name)
        self.assertIn("xabi_contract_expiry", slices_by_name)
        self.assertIn("jorge_staff_xabi_expiry", slices_by_name)
        self.assertIn("jorge_staff_squizzi_wwy", slices_by_name)
        self.assertIn("control_athletic_family", slices_by_name)

        control = slices_by_name["control_athletic_family"]
        self.assertEqual(control["files"], ["real_control_athletic_family.bin"])
        self.assertEqual(control["expected"]["club_key_candidate"], "frame3:club:0x0052AEE2")

    def test_expected_fields_use_the_allowed_surface(self) -> None:
        manifest = load_manifest()
        allowed = {
            "full_name",
            "person_key",
            "wage",
            "start_date",
            "expiry_date",
            "working_with_youngsters",
            "club_key_candidate",
            "notes",
        }

        for slice_entry in manifest["slices"]:
            expected = slice_entry["expected"]
            self.assertTrue(set(expected.keys()).issubset(allowed))

    def test_slice_files_are_stable_across_reads(self) -> None:
        manifest = load_manifest()

        first_pass = {}
        second_pass = {}
        for slice_entry in manifest["slices"]:
            for file_name in slice_entry["files"]:
                path = FIXTURES / file_name
                first_pass[file_name] = path.read_bytes()
                second_pass[file_name] = path.read_bytes()

        self.assertEqual(first_pass, second_pass)

    def test_manifest_expected_people_and_relation_tags_are_present_in_slices(self) -> None:
        manifest = load_manifest()

        for slice_entry in manifest["slices"]:
            file_name = slice_entry["files"][0]
            blob = (FIXTURES / file_name).read_bytes()
            people = extract_inline_named_people(blob)

            expected = slice_entry["expected"]
            if "full_name" in expected:
                self.assertTrue(any(person["full_name"] == expected["full_name"] for person in people), file_name)
                if "person_key" in expected:
                    person = next(person for person in people if person["full_name"] == expected["full_name"])
                    self.assertEqual(person["person_key"], expected["person_key"], file_name)

            if "working_with_youngsters" in expected:
                person = next(person for person in people if person["full_name"] == expected["full_name"])
                tail = next(tail for tail in person["inline_secondary_tails"] if "working_with_youngsters_candidate_offset" in tail)
                candidate_offset = int(tail["working_with_youngsters_candidate_offset"])
                self.assertEqual(blob[candidate_offset], expected["working_with_youngsters"], file_name)

            observed_tags = {entry["tag"] for person in people for entry in person.get("relation_entries", [])}
            for relation_tag in slice_entry["recurring_relation_tags"]:
                self.assertIn(relation_tag["tag"], observed_tags, file_name)


if __name__ == "__main__":
    unittest.main()
