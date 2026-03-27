from __future__ import annotations

import unittest

from fm_save_extract.relation_resolution import resolve_relation


class RelationResolutionTests(unittest.TestCase):
    def test_fixture_backed_athletic_pattern_resolves_to_club_key(self) -> None:
        clubs = [
            {
                "club_key": "frame3:club:0x0052AEE2",
                "full_name": "Athletic Club",
                "short_name": "Athletic Club",
                "offset": 0x0052AEE2,
            },
            {
                "club_key": "frame3:club:0x00518E99",
                "full_name": "Futebol Clube do Porto",
                "short_name": "FC Porto",
                "offset": 0x00518E99,
            },
        ]
        entry = {
            "tag": "0x00080964",
            "tag_value": 526692,
            "ref_hex": "5000ff3f",
            "value": 4,
            "slot": 1,
        }

        resolved = resolve_relation(entry, clubs)

        self.assertEqual(resolved["relation_kind"], "club_employment")
        self.assertEqual(resolved["target_kind"], "club")
        self.assertEqual(resolved["club_key"], "frame3:club:0x0052AEE2")
        self.assertEqual(resolved["target_key"], "frame3:club:0x0052AEE2")

    def test_fixture_backed_athletic_pattern_falls_back_to_known_club_key_without_tables(self) -> None:
        entry = {
            "tag": "0x00010364",
            "tag_value": 66404,
            "ref_hex": "4e00ff3f",
            "value": 4,
            "slot": 2,
        }

        resolved = resolve_relation(entry, [])

        self.assertEqual(resolved["relation_kind"], "club_employment")
        self.assertEqual(resolved["target_kind"], "club")
        self.assertEqual(resolved["club_key"], "frame3:club:0x0052AEE2")
        self.assertEqual(resolved["target_key"], "frame3:club:0x0052AEE2")

    def test_non_catalogued_club_pattern_stays_unresolved(self) -> None:
        clubs = [
            {
                "club_key": "frame3:club:0x0052AEE2",
                "full_name": "Athletic Club",
                "short_name": "Athletic Club",
                "offset": 0x0052AEE2,
            }
        ]
        entry = {
            "tag": "0x00010364",
            "tag_value": 66404,
            "ref_hex": "4e00ff6a",
            "value": 4,
            "slot": 2,
        }

        resolved = resolve_relation(entry, clubs)

        self.assertEqual(resolved["relation_kind"], "club_employment")
        self.assertEqual(resolved["target_kind"], "club")
        self.assertIsNone(resolved["club_key"])
        self.assertIsNone(resolved["target_key"])


if __name__ == "__main__":
    unittest.main()
