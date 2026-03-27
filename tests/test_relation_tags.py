from __future__ import annotations

import unittest

from fm_save_extract.relation_tags import classify_relation_entry


class RelationTagTests(unittest.TestCase):
    def test_classify_club_employment_families(self) -> None:
        cases = [
            {
                "tag": "0x00080964",
                "tag_value": 526692,
                "ref_hex": "5000ff70",
                "value": 4,
                "slot": 1,
            },
            {
                "tag": "0x00010364",
                "tag_value": 66404,
                "ref_hex": "4e00ff6a",
                "value": 4,
                "slot": 2,
            },
        ]

        for entry in cases:
            with self.subTest(entry=entry["tag"]):
                result = classify_relation_entry(entry)
                self.assertEqual(result["relation_kind"], "club_employment")
                self.assertEqual(result["target_kind"], "club")
                self.assertEqual(result["pattern_key"], f"tag:{entry['tag']}")
                self.assertGreaterEqual(result["confidence"], 0.9)
                self.assertEqual(result.get("target_hint"), "club employment")

    def test_classify_staff_assignment_families(self) -> None:
        cases = [
            {
                "tag": "0x0001033C",
                "tag_value": 66364,
                "ref_hex": "4f00ffca",
                "value": 3,
                "slot": 1,
            },
            {
                "tag": "0x00010346",
                "tag_value": 66374,
                "ref_hex": "4f00ffc4",
                "value": 3,
                "slot": 2,
            },
        ]

        for entry in cases:
            with self.subTest(entry=entry["tag"]):
                result = classify_relation_entry(entry)
                self.assertEqual(result["relation_kind"], "staff_assignment")
                self.assertEqual(result["target_kind"], "team")
                self.assertEqual(result["pattern_key"], f"tag:{entry['tag']}")
                self.assertGreaterEqual(result["confidence"], 0.85)
                self.assertEqual(result.get("target_hint"), "staff/team assignment")

    def test_classify_contract_reference_candidate_family(self) -> None:
        entry = {
            "tag": "0x00030164",
            "tag_value": 196964,
            "ref_hex": "4f00ff2d",
            "value": 21,
            "slot": 8,
        }

        result = classify_relation_entry(entry)

        self.assertEqual(result["relation_kind"], "contract_reference")
        self.assertEqual(result["target_kind"], "contract")
        self.assertEqual(result["pattern_key"], "tag:0x00030164")
        self.assertGreaterEqual(result["confidence"], 0.8)
        self.assertEqual(result.get("target_hint"), "contract reference")

    def test_classify_unknown_fallback(self) -> None:
        entry = {
            "tag": "0x00ABCDEF",
            "tag_value": 11259375,
            "ref_hex": "deadbeef",
            "value": 99,
            "slot": 7,
        }

        result = classify_relation_entry(entry)

        self.assertEqual(result["relation_kind"], "unknown")
        self.assertEqual(result["target_kind"], "unknown")
        self.assertEqual(result["pattern_key"], "tag:0x00ABCDEF")
        self.assertLess(result["confidence"], 0.2)
        self.assertNotIn("target_hint", result)


if __name__ == "__main__":
    unittest.main()
