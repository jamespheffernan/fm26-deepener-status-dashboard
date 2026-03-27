from __future__ import annotations

import unittest

from fm_save_extract.extractor import extract_world_state
from tests.test_fm_save_extract import (
    build_synthetic_contract_frames,
    build_synthetic_staff_frames,
    build_synthetic_frame,
)


class ExtractorReconciliationTests(unittest.TestCase):
    def test_extract_world_state_surfaces_inline_relation_entries_as_club_links(self) -> None:
        frame = build_synthetic_staff_frames()["squizzi_wwy"]

        bundle, _ = extract_world_state(frame)

        self.assertEqual(len(bundle.people), 2)
        owner = next(person for person in bundle.people if person["full_name"] == "Jorge Manuel Domingues Maria Vital")
        self.assertEqual(owner["alias_person_keys"], [owner["person_key"]])
        self.assertEqual(owner["relation_window"], {"start": 326, "end": 505})
        self.assertEqual(len(owner["relation_entries"]), 2)

        self.assertEqual(len(bundle.club_links), 2)
        first_link = bundle.club_links[0]
        self.assertEqual(first_link["person_key"], owner["person_key"])
        self.assertEqual(first_link["source"], "inline_relation_entry")
        self.assertEqual(first_link["tag"], "0x0001033C")
        self.assertEqual(first_link["relation_kind"], "staff_assignment")
        self.assertEqual(first_link["target_kind"], "team")
        self.assertEqual(first_link["value"], 3)
        self.assertIsNone(first_link["club_key"])
        self.assertIn("offset:0x00000146", first_link["evidence"])
        self.assertEqual(owner["typed_relation_summaries"][0]["relation_kind"], "staff_assignment")
        self.assertEqual(owner["typed_relation_summaries"][0]["target_kind"], "team")

    def test_extract_world_state_populates_contracts_from_diff_frames(self) -> None:
        base, diff_frames = build_synthetic_contract_frames()

        bundle, _ = extract_world_state(base, diff_frames=list(diff_frames.items()))

        self.assertEqual(len(bundle.contracts), 1)
        contract = bundle.contracts[0]
        self.assertTrue(contract["person_key"].startswith("frame3:person-name:0x"))
        self.assertEqual(contract["wage"], 205738)
        self.assertEqual(contract["start_date"], "2025-06-01")
        self.assertEqual(contract["expiry_date"], "2033-06-30")

    def test_extract_world_state_populates_staff_roles_from_diff_frames(self) -> None:
        diff_frames = build_synthetic_staff_frames()
        base = diff_frames["xabi_expiry"]

        bundle, _ = extract_world_state(base, diff_frames=list(diff_frames.items()))

        self.assertEqual(len(bundle.staff_roles), 1)
        role = bundle.staff_roles[0]
        self.assertEqual(role["person_key"], "frame3:person-name:0x00000104")
        self.assertEqual(role["staff_attributes"]["WorkingWithYoungsters"], 20)
        self.assertEqual(len(role["club_link_refs"]), 2)
        self.assertEqual(role["typed_link_refs"][0]["relation_kind"], "staff_assignment")
        self.assertEqual(role["typed_link_refs"][0]["target_kind"], "team")
        self.assertEqual(bundle.unresolved_candidates["club_link_count"], 2)

    def test_extract_world_state_assigns_alias_keys_to_canonical_people(self) -> None:
        bundle, _ = extract_world_state(build_synthetic_frame())

        for person in bundle.people:
            self.assertIn("alias_person_keys", person)
            self.assertTrue(person["alias_person_keys"])
            self.assertIn(person["person_key"], person["alias_person_keys"])


if __name__ == "__main__":
    unittest.main()
