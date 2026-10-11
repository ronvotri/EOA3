"""Synthetic machine-code snippets only; no original game bytes or assets."""
import hashlib
import unittest

from audit_v5_surface_pipeline import (
    audit_engine, rel32_destination, SURFACE_LANDMARKS, FONT_LANDMARKS,
)


def fixture():
    segments = {
        0x41A700: bytearray(b"\x90" * 0xF0),
        0x41AA4B: bytearray(b"\x90" * 150),
    }
    for va, instr in {**SURFACE_LANDMARKS, **FONT_LANDMARKS}.items():
        base = 0x41A700 if va < 0x41AA00 else 0x41AA4B
        start = va - base
        assert 0 <= start <= len(segments[base]) - len(instr)
        segments[base][start:start+len(instr)] = instr
    records = []
    for api, va, iat in (
        ("TextOutA", 0x41A79A, 0x4F2018),
        ("TextOutA", 0x41A7B9, 0x4F2018),
        ("CreateFontIndirectA", 0x41AAAB, 0x4F2020),
    ):
        base = 0x41A700 if api == "TextOutA" else 0x41AA4B
        raw = bytes(segments[base][va-96-base:va+54-base])
        assert len(raw) == 150
        assert raw[96:102] == b"\xff\x15" + iat.to_bytes(4, "little")
        records.append({
            "api": api, "site_va": hex(va), "iat_va": hex(iat),
            "code_window_start_va": hex(va-96),
            "site_offset_within_window": 96,
            "code_window_hex": raw.hex(),
            "code_window_sha256": hashlib.sha256(raw).hexdigest(),
            "call_bytes_hex": raw[96:102].hex(),
        })
    return {
        "status": "read_only_code_neighborhoods_not_disassembly_or_patch",
        "exe_sha256": "a"*64, "matches_documented_exe_sha256": True,
        "candidate_call_sites": records,
    }


class GdiSurfaceAuditTests(unittest.TestCase):
    def test_expected_getdc_releasedc_and_font_helper_targets(self):
        summary = audit_engine(fixture(), expected_sha="a"*64)
        self.assertEqual(summary["status"], "verified_static_gdi_surface_compatibility_not_runtime_or_patch")
        self.assertEqual(summary["surface_candidate"]["vtable_getdc_compatible"]["vtable_offset"], "0x44")
        self.assertEqual(summary["surface_candidate"]["vtable_releasedc_compatible"]["vtable_offset"], "0x68")
        self.assertEqual(summary["font_initialization"]["saved_hfont"], "this+0xFCC")
        self.assertEqual(summary["font_initialization"]["following_direct_calls"],
                         {"0x41aac5":"0x41a7f0", "0x41aacd":"0x41a8c0"})
        self.assertIn("not runtime-verified", summary["surface_candidate"]["confidence"])

    def test_corrupt_vtable_offset_rejected_even_with_valid_digest(self):
        d = fixture()
        row = d["candidate_call_sites"][0]
        raw = bytearray.fromhex(row["code_window_hex"])
        target_offset = 0x41A74F - int(row["code_window_start_va"],16)
        self.assertEqual(raw[target_offset], 0x44)
        raw[target_offset] = 0x48
        row["code_window_hex"] = raw.hex()
        row["code_window_sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "DirectDraw-compatible"):
            audit_engine(d, expected_sha="a"*64)

    def test_corrupt_font_charset_rejected_even_with_valid_digest(self):
        d = fixture()
        row = d["candidate_call_sites"][2]
        raw = bytearray.fromhex(row["code_window_hex"])
        at = 0x41AA88 - int(row["code_window_start_va"],16)
        self.assertEqual(raw[at], 0x86)
        raw[at] = 0x00
        row["code_window_hex"] = raw.hex()
        row["code_window_sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "Font"):
            audit_engine(d, expected_sha="a"*64)

    def test_digest_tamper_or_overlap_disagreement_rejected(self):
        d = fixture()
        d["candidate_call_sites"][0]["code_window_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "invalid offsets/digest"):
            audit_engine(d, expected_sha="a"*64)
        d = fixture()
        row = d["candidate_call_sites"][1]
        raw = bytearray.fromhex(row["code_window_hex"])
        raw[0] ^= 0x10
        row["code_window_hex"] = raw.hex()
        row["code_window_sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "Conflicting overlapping"):
            audit_engine(d, expected_sha="a"*64)

    def test_wrong_build_and_missing_site_rejected(self):
        d = fixture()
        with self.assertRaisesRegex(ValueError, "does not match"):
            audit_engine(d)
        d = fixture()
        d["candidate_call_sites"].pop()
        with self.assertRaisesRegex(ValueError, "Missing or duplicate"):
            audit_engine(d, expected_sha="a"*64)

    def test_rel32_inspects_only_direct_call_at_address(self):
        # A wrong opcode cannot be interpreted as a code reference.
        with self.assertRaisesRegex(ValueError, "Missing direct"):
            rel32_destination({0x5000+i: 0x90 for i in range(5)}, 0x5000)


if __name__ == "__main__":
    unittest.main()
