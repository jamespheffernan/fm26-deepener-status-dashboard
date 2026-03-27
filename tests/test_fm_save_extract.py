from __future__ import annotations

import datetime as dt
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from fm_save_extract.binary import encode_date
from fm_save_extract.diff_decoders import (
    decode_contracts_from_diff_frames,
    decode_staff_roles_from_diff_frames,
    summarize_pairwise_diff_frames,
)
from fm_save_extract.inline_people import extract_inline_named_people
from fm_save_extract.extractor import extract_world_state
from fm_save_extract.models import NearbyValue, PersonCandidate, Preamble
from fm_save_extract.player_blocks import PREAMBLE_OFFSET, dedupe_candidates, display_value, enumerate_person_candidates, read_preamble


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def load_hex_fixture(name: str) -> bytes:
    return bytes.fromhex((FIXTURES / name).read_text(encoding="utf-8").strip())


def build_synthetic_frame() -> bytes:
    frame = bytearray(0x5000)
    frame[0:4] = encode_date(dt.date(2025, 1, 7))
    frame[0x1A:0x20] = b"2600 6"

    def write_u32(offset: int, value: int) -> None:
        frame[offset:offset + 4] = value.to_bytes(4, "little")

    write_u32(0x2C, 2028)
    write_u32(0x60, 65800)
    write_u32(0xBC, 131584)
    write_u32(0xF0, 258)

    club_window = load_hex_fixture("grenoble_club_window.hex")
    club_offset = 0x0200
    frame[club_offset:club_offset + len(club_window)] = club_window

    metadata_blob = b"Manager\x00AssistantManager\x00ContractReference\x00PersonReference\x00"
    metadata_offset = 0x0600
    frame[metadata_offset:metadata_offset + len(metadata_blob)] = metadata_blob

    full_name = b"Xabier Alonso Olano"
    inline_offset = 0x1000
    frame[inline_offset:inline_offset + 4] = len(full_name).to_bytes(4, "little")
    frame[inline_offset + 4:inline_offset + 4 + len(full_name)] = full_name
    frame[inline_offset - 8:inline_offset - 4] = encode_date(dt.date(2032, 6, 30))
    frame[inline_offset - 4:inline_offset] = encode_date(dt.date(2025, 6, 1))
    frame[inline_offset + 4 + len(full_name):inline_offset + 8 + len(full_name)] = encode_date(dt.date(1981, 11, 25))

    player_window = load_hex_fixture("haaland_block_original.hex")
    window_offset = 0x2000
    frame[window_offset:window_offset + len(player_window)] = player_window
    block_start = window_offset + PREAMBLE_OFFSET

    uid_offset = block_start + 0x0120
    write_u32(uid_offset, 29_179_241)
    write_u32(uid_offset + 4, 29_179_241)
    frame[block_start + 0x0080:block_start + 0x0084] = encode_date(dt.date(2000, 7, 21))
    frame[block_start + 0x0180:block_start + 0x0184] = (1168).to_bytes(4, "little")
    frame[block_start + 0x0188:block_start + 0x018C] = (434962).to_bytes(4, "little")
    frame[block_start + 0x0150:block_start + 0x015A] = bytes([0xFF, 16, 20, 15, 18, 17, 10, 12, 11, 0xFE])

    return bytes(frame)


def build_synthetic_contract_frames() -> tuple[bytes, dict[str, bytes]]:
    name = b"Xabier Alonso Olano"
    base = bytearray(4096)
    raise_frame = bytearray(4096)
    expiry_frame = bytearray(4096)
    name_offset = 1024

    for frame in (base, raise_frame, expiry_frame):
        frame[name_offset - 5:name_offset] = len(name).to_bytes(4, "little") + b"\x00"
        frame[name_offset:name_offset + len(name)] = name

    base[name_offset - 117:name_offset - 113] = (165_738).to_bytes(4, "little")
    raise_frame[name_offset - 117:name_offset - 113] = (205_738).to_bytes(4, "little")
    expiry_frame[name_offset - 117:name_offset - 113] = (205_738).to_bytes(4, "little")

    raise_frame[name_offset - 172:name_offset - 168] = encode_date(dt.date(2032, 6, 30))
    expiry_frame[name_offset - 172:name_offset - 168] = encode_date(dt.date(2033, 6, 30))
    base[name_offset - 172:name_offset - 168] = encode_date(dt.date(2032, 6, 30))

    for frame in (base, raise_frame, expiry_frame):
        frame[name_offset - 168:name_offset - 164] = encode_date(dt.date(2025, 6, 1))

    # Keep the frames mostly equal and force the raise save to move relative to base.
    raise_frame[:32] = b"\x01" * 32
    expiry_frame[:32] = b"\x01" * 32

    return bytes(base), {"xabi_raise": bytes(raise_frame), "xabi_expiry": bytes(expiry_frame)}


def build_synthetic_staff_frames() -> dict[str, bytes]:
    before = bytearray(4096)
    after = bytearray(4096)
    family_start = 0x0200
    vector_start = family_start + 0x20

    before[family_start:family_start + 7] = bytes.fromhex("02 40 10 00 00 00 00")
    after[family_start:family_start + 7] = bytes.fromhex("02 40 10 00 00 00 00")

    vector = bytearray(
        [
            0x22, 0x1E, 0x40, 0x1E, 0x1E, 0x1E, 0x40, 0x1E,
            0x1E, 0x0C, 0x07, 0x06, 0x0D, 0x08, 0x10, 0x05,
            0x02, 0x0F, 0x07, 0x03, 0x07, 0x05, 0x06, 0x49,
            0x0C, 0x0D, 0x08, 0x0D, 0x0D, 0x11, 0x12, 0x03,
            0x06, 0x10, 0x03, 0x0A, 0x19, 0x5E, 0x1F, 0x2E,
            0x2B, 0x55, 0x0F, 0x17, 0x23, 0x23, 0x23, 0x24,
            0x23, 0x19, 0x0A, 0x2E, 0x33, 0x0A, 0x0A, 0x4B,
            0x32, 0x0F, 0x2D, 0x19, 0x32, 0x0A, 0x00, 0x00,
        ]
    )
    before[vector_start:vector_start + len(vector)] = vector

    after_vector = bytearray(vector)
    after_vector[0x16] = 0x14
    after_vector[0x17] = 0x4B
    after_vector[0x25] = 0x5F
    after_vector[0x26] = 0x1E
    after_vector[0x27] = 0x2D
    after_vector[0x28] = 0x2D
    after_vector[0x2B] = 0x19
    after_vector[0x2F] = 0x23
    after[vector_start:vector_start + len(after_vector)] = after_vector

    return {"xabi_expiry": bytes(before), "squizzi_wwy": bytes(after)}


class FMSaveExtractTests(unittest.TestCase):
    def test_real_haaland_window_decodes_preamble_and_finishing(self) -> None:
        window = load_hex_fixture("haaland_block_original.hex")
        preamble = read_preamble(window, PREAMBLE_OFFSET)

        self.assertIsNotNone(preamble)
        assert preamble is not None
        self.assertEqual(preamble.home_rep, 8904)
        self.assertEqual(preamble.current_rep, 9459)
        self.assertEqual(preamble.world_rep, 10000)
        self.assertEqual(preamble.ca, 195)
        self.assertEqual(preamble.pa, 195)

        finishing_raw = window[PREAMBLE_OFFSET + 0x11]
        self.assertEqual(finishing_raw, 91)
        self.assertEqual(display_value(finishing_raw, 17), 18)

    def test_modified_window_flips_finishing_display_value(self) -> None:
        original = load_hex_fixture("haaland_block_original.hex")
        modified = load_hex_fixture("haaland_block_modified.hex")

        self.assertEqual(original[PREAMBLE_OFFSET + 0x11], 91)
        self.assertEqual(modified[PREAMBLE_OFFSET + 0x11], 5)
        self.assertEqual(display_value(modified[PREAMBLE_OFFSET + 0x11], 17), 1)

    def test_dedupe_candidates_prefers_higher_confidence_when_blocks_overlap(self) -> None:
        base_candidate = PersonCandidate(
            block_start=0x1000,
            preamble=Preamble(home_rep=100, current_rep=150, world_rep=200, ca=100, pa=120),
            positions={"ST": 20},
            attributes_raw={"Finishing": 91},
            attributes_display={"Finishing": 18},
            uid=123,
            uid_candidates=[NearbyValue(offset=0x1100, value=123)],
            dob="2000-07-21",
            dob_candidates=[NearbyValue(offset=0x1080, value="2000-07-21")],
            personality=None,
            name_refs={"first_name_ids": [1], "surname_ids": [2]},
            confidence=0.55,
            evidence=["low"],
        )
        better_candidate = PersonCandidate(
            block_start=0x1000 + 8,
            preamble=Preamble(home_rep=100, current_rep=150, world_rep=200, ca=100, pa=120),
            positions={"ST": 20},
            attributes_raw={"Finishing": 91},
            attributes_display={"Finishing": 18},
            uid=456,
            uid_candidates=[NearbyValue(offset=0x1108, value=456)],
            dob="2000-07-21",
            dob_candidates=[NearbyValue(offset=0x1088, value="2000-07-21")],
            personality=None,
            name_refs={"first_name_ids": [1], "surname_ids": [2]},
            confidence=0.90,
            evidence=["high"],
        )

        deduped = dedupe_candidates([base_candidate, better_candidate])
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].uid, 456)

    def test_extract_world_state_from_synthetic_frame_emits_expected_outputs(self) -> None:
        frame = build_synthetic_frame()
        bundle, _ = extract_world_state(frame)

        self.assertEqual(bundle.game_info["header_counts"]["clubs"], 65800)
        self.assertTrue(bundle.clubs)
        self.assertEqual(bundle.clubs[0]["full_name"], "Grenoble Foot 38")
        self.assertTrue(bundle.people)
        self.assertTrue(bundle.players)

        haaland = next(
            person for person in bundle.people if "known_player:haaland" in person["evidence"]
        )
        self.assertEqual(haaland["uid"], 29179241)
        self.assertEqual(haaland["dob"], "2000-07-21")
        self.assertEqual(haaland["person_key"], "uid:29179241")
        xabi = next(
            person for person in bundle.people if person.get("full_name") == "Xabier Alonso Olano"
        )
        self.assertEqual(xabi["dob"], "1981-11-25")
        self.assertEqual(xabi["source"], "inline_name_dob")
        self.assertIn("contract_clusters", bundle.unresolved_candidates)
        self.assertIn("staff_clusters", bundle.unresolved_candidates)
        self.assertEqual(bundle.unresolved_candidates["inline_name_people_count"], 1)

    def test_enumerate_person_candidates_finds_known_hybrid_block(self) -> None:
        candidates = enumerate_person_candidates(build_synthetic_frame())

        self.assertTrue(candidates)
        self.assertTrue(any(candidate.known_match == "haaland" for candidate in candidates))

    def test_extract_inline_named_people_finds_full_name_dob_anchor(self) -> None:
        people = extract_inline_named_people(build_synthetic_frame())

        self.assertEqual(len(people), 1)
        self.assertEqual(people[0]["full_name"], "Xabier Alonso Olano")
        self.assertEqual(people[0]["dob"], "1981-11-25")
        self.assertIsNotNone(people[0]["inline_post_dob"])
        self.assertIn("nearby_date:2032-06-30", " ".join(people[0]["evidence"]))

    def test_cli_writes_full_world_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            frame_path = Path(temp_dir) / "synthetic_frame.bin"
            frame_path.write_bytes(build_synthetic_frame())

            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "fm_save_extract",
                    "--input",
                    str(frame_path),
                    "--raw",
                    "--output-dir",
                    temp_dir,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            expected = [
                "game_info.json",
                "clubs.json",
                "people.json",
                "players.json",
                "staff_roles.json",
                "club_links.json",
                "contracts.json",
                "unresolved_candidates.json",
            ]
            for filename in expected:
                self.assertTrue((Path(temp_dir) / filename).exists(), filename)

            people = json.loads((Path(temp_dir) / "people.json").read_text(encoding="utf-8"))
            self.assertTrue(people)

    def test_decode_contracts_from_diff_frames_finds_wage_and_expiry(self) -> None:
        base, diff_frames = build_synthetic_contract_frames()
        contracts = decode_contracts_from_diff_frames(base, diff_frames)

        self.assertEqual(len(contracts), 1)
        contract = contracts[0]
        self.assertEqual(contract["wage"], 205738)
        self.assertEqual(contract["start_date"], "2025-06-01")
        self.assertEqual(contract["expiry_date"], "2033-06-30")

    def test_decode_staff_roles_from_diff_frames_promotes_working_with_youngsters(self) -> None:
        staff_roles = decode_staff_roles_from_diff_frames(build_synthetic_staff_frames())

        self.assertEqual(len(staff_roles), 1)
        self.assertEqual(staff_roles[0]["staff_attributes"]["WorkingWithYoungsters"], 20)
        self.assertEqual(staff_roles[0]["vector_length"], 0x40)
        self.assertEqual(staff_roles[0]["changed_bytes"][0]["relative_offset"], 0x16)

    def test_summarize_pairwise_diff_frames_tracks_sequential_edits(self) -> None:
        base, contract_frames = build_synthetic_contract_frames()
        del base
        diff_frames = [
            ("xabi_raise", contract_frames["xabi_raise"]),
            ("xabi_expiry", contract_frames["xabi_expiry"]),
            ("squizzi_wwy", build_synthetic_staff_frames()["squizzi_wwy"]),
        ]

        summaries = summarize_pairwise_diff_frames(diff_frames)

        self.assertEqual(len(summaries), 2)
        self.assertIn("Xabier", summaries[0]["common_name"]["text"])
        self.assertTrue(summaries[0]["changed_bytes"])


if __name__ == "__main__":
    unittest.main()
