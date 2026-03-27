from __future__ import annotations

import json
import unittest
from pathlib import Path

from fm_save_extract.extractor import extract_world_state


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
MANIFEST_PATH = FIXTURES / "real_slice_manifest.json"


def load_manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_slice(name: str) -> tuple[dict[str, object], bytes]:
    manifest = load_manifest()
    entry = next(slice_entry for slice_entry in manifest["slices"] if slice_entry["name"] == name)
    file_name = entry["files"][0]
    return entry, (FIXTURES / file_name).read_bytes()


class RealSliceExtractionTests(unittest.TestCase):
    def test_real_xabi_contract_family_decodes_expected_values(self) -> None:
        base_entry, base = load_slice("xabi_contract_base")
        _, wage_frame = load_slice("xabi_contract_raise")
        expiry_entry, expiry_frame = load_slice("xabi_contract_expiry")

        bundle, _ = extract_world_state(
            base,
            diff_frames=[
                ("xabi_raise", wage_frame),
                ("xabi_expiry", expiry_frame),
            ],
        )

        self.assertEqual(len(bundle.contracts), 1)
        contract = bundle.contracts[0]
        self.assertEqual(contract["person_key"], base_entry["expected"]["person_key"])
        self.assertEqual(contract["wage"], expiry_entry["expected"]["wage"])
        self.assertEqual(contract["start_date"], expiry_entry["expected"]["start_date"])
        self.assertEqual(contract["expiry_date"], expiry_entry["expected"]["expiry_date"])
        self.assertIsNone(contract["club_key"])

        xabi = next(person for person in bundle.people if person["full_name"] == base_entry["expected"]["full_name"])
        self.assertEqual(contract["person_key"], xabi["person_key"])
        unknown_links = [
            link
            for link in bundle.club_links
            if link["person_key"] == xabi["person_key"] and link["relation_kind"] == "unknown"
        ]
        self.assertTrue(unknown_links)
        self.assertIn("tag", unknown_links[0])
        self.assertIn("ref_hex", unknown_links[0])
        self.assertIn("value", unknown_links[0])
        self.assertIn("slot", unknown_links[0])
        self.assertIn("offset", unknown_links[0])

    def test_real_jorge_staff_family_preserves_owner_and_wwy(self) -> None:
        before_entry, before = load_slice("jorge_staff_xabi_expiry")
        after_entry, after = load_slice("jorge_staff_squizzi_wwy")

        bundle, _ = extract_world_state(
            before,
            diff_frames=[
                ("xabi_expiry", before),
                ("squizzi_wwy", after),
            ],
        )

        self.assertEqual(len(bundle.staff_roles), 1)
        role = bundle.staff_roles[0]
        self.assertEqual(role["person_key"], after_entry["expected"]["person_key"])
        self.assertEqual(
            role["staff_attributes"]["WorkingWithYoungsters"],
            after_entry["expected"]["working_with_youngsters"],
        )
        self.assertEqual(len(role["club_link_refs"]), 2)
        self.assertEqual(len(role["typed_link_refs"]), 2)
        self.assertTrue(all(link["relation_kind"] == "staff_assignment" for link in role["typed_link_refs"]))
        self.assertTrue(all(link["target_kind"] == "team" for link in role["typed_link_refs"]))

        owner = next(person for person in bundle.people if person["full_name"] == before_entry["expected"]["full_name"])
        self.assertEqual(owner["person_key"], role["person_key"])

    def test_real_athletic_control_slice_emits_resolved_club_links(self) -> None:
        control_entry, control = load_slice("control_athletic_family")

        bundle, _ = extract_world_state(control)

        resolved_links = [
            link
            for link in bundle.club_links
            if link["club_key"] == control_entry["expected"]["club_key_candidate"]
        ]
        self.assertTrue(resolved_links)
        self.assertTrue(
            any(
                link["tag"] == "0x00080964"
                and link["ref_hex"] == "5000ff3f"
                and link["relation_kind"] == "club_employment"
                and link["target_kind"] == "club"
                for link in resolved_links
            )
        )

        owner = next(person for person in bundle.people if person["full_name"] == control_entry["expected"]["full_name"])
        self.assertTrue(
            any(
                summary["club_key"] == control_entry["expected"]["club_key_candidate"]
                and summary["relation_kind"] == "club_employment"
                for summary in owner["typed_relation_summaries"]
            )
        )


if __name__ == "__main__":
    unittest.main()
