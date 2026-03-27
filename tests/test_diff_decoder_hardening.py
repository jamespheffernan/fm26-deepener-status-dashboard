from __future__ import annotations

import datetime as dt
import unittest

from fm_save_extract.binary import encode_date
from fm_save_extract.diff_decoders import decode_contracts_from_diff_frames, decode_staff_roles_from_diff_frames


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

    raise_frame[:32] = b"\x01" * 32
    expiry_frame[:32] = b"\x01" * 32

    return bytes(base), {"frame_raise": bytes(raise_frame), "frame_expiry": bytes(expiry_frame)}


def build_synthetic_staff_frames() -> dict[str, bytes]:
    before = bytearray(4096)
    after = bytearray(4096)
    name = b"Jorge Manuel Domingues Maria Vital"
    name_offset = 0x0100
    next_name_offset = 0x0400
    tail_start = 0x01F9
    family_start = tail_start + 7
    vector_start = family_start + 0x20
    relation_entries = [
        bytes.fromhex("0001033c4f00ffca0300000000000001"),
        bytes.fromhex("000103464f00ffc40300000000000002"),
    ]

    for frame in (before, after):
        frame[name_offset:name_offset + 4] = len(name).to_bytes(4, "little")
        frame[name_offset + 4:name_offset + 4 + len(name)] = name
        frame[name_offset + 4 + len(name):name_offset + 8 + len(name)] = encode_date(dt.date(1962, 8, 25))
        frame[next_name_offset:next_name_offset + 4] = len(b"Control Example Name").to_bytes(4, "little")
        frame[next_name_offset + 4:next_name_offset + 4 + len(b"Control Example Name")] = b"Control Example Name"
        frame[next_name_offset + 4 + len(b"Control Example Name"):next_name_offset + 8 + len(b"Control Example Name")] = encode_date(dt.date(1970, 1, 1))
        frame[tail_start:tail_start + 14] = bytes.fromhex("ff01ff0000000102401000000000")
        relation_start = name_offset + 4 + len(name) + 0x20
        for index, entry in enumerate(relation_entries):
            frame[relation_start + (index * 0x10):relation_start + ((index + 1) * 0x10)] = entry

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

    return {"frame_old": bytes(before), "frame_new": bytes(after)}


class DiffDecoderHardeningTests(unittest.TestCase):
    def test_decode_contracts_accepts_generic_labels_and_frame_order(self) -> None:
        base, frames = build_synthetic_contract_frames()

        contracts = decode_contracts_from_diff_frames(
            base,
            {
                "frame_expiry": frames["frame_expiry"],
                "frame_raise": frames["frame_raise"],
            },
        )

        self.assertEqual(len(contracts), 1)
        contract = contracts[0]
        self.assertEqual(contract["wage"], 205738)
        self.assertEqual(contract["start_date"], "2025-06-01")
        self.assertEqual(contract["expiry_date"], "2033-06-30")

    def test_decode_staff_roles_accepts_generic_labels_and_reversed_order(self) -> None:
        frames = build_synthetic_staff_frames()

        staff_roles = decode_staff_roles_from_diff_frames(
            {
                "frame_after": frames["frame_new"],
                "frame_before": frames["frame_old"],
            }
        )

        self.assertEqual(len(staff_roles), 1)
        role = staff_roles[0]
        self.assertEqual(role["staff_attributes"]["WorkingWithYoungsters"], 20)
        self.assertTrue(role["person_key"])
        self.assertEqual(role["vector_length"], 0x40)
        self.assertEqual(len(role["club_link_refs"]), 2)


if __name__ == "__main__":
    unittest.main()
