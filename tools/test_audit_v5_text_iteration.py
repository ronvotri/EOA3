"""Synthetic x86 windows only: no game binary, fonts or copyrighted assets."""
import hashlib
import unittest

from audit_v5_text_iteration import (
    CHAR_LOOP_STEPS, TEXT_SEQUENCE, TEXTOUT_VAS, CHAR_NEXT_VA,
    audit_engine_evidence, stitch_evidence, exactly_at,
)


def fixture():
    # Two independently sampled TextOutA windows share a real overlap; the
    # integrity validator must reject disagreement even if each digest passes.
    segments = {
        0x41A700: bytearray(b"\x90" * 0xF0),
        0x42ACF0: bytearray(b"\x90" * 0xB0),
    }
    for address, opcode in {**CHAR_LOOP_STEPS, **TEXT_SEQUENCE}.items():
        base = 0x41A700 if address < 0x420000 else 0x42ACF0
        start = address-base
        segments[base][start:start+len(opcode)] = opcode
    sites = []
    for api, va, iat in (
        ("TextOutA", TEXTOUT_VAS[0], 0x4F2018),
        ("TextOutA", TEXTOUT_VAS[1], 0x4F2018),
        ("CharNextA", CHAR_NEXT_VA, 0x4F21B0),
    ):
        base = 0x41A700 if api == "TextOutA" else 0x42ACF0
        begin = va - 96
        raw = bytes(segments[base][begin-base:begin-base+150])
        # Both 150-byte snippets must fit inside our synthetic segments.
        assert len(raw) == 150, (hex(va), len(raw))
        signature = raw[96:102]
        assert signature == b"\xff\x15" + iat.to_bytes(4, "little")
        sites.append({
            "api": api, "site_va": hex(va), "iat_va": hex(iat),
            "code_window_start_va": hex(begin),
            "site_offset_within_window": 96,
            "code_window_hex": raw.hex(),
            "call_bytes_hex": signature.hex(),
            "code_window_sha256": hashlib.sha256(raw).hexdigest(),
        })
    return {
        "status": "read_only_code_neighborhoods_not_disassembly_or_patch",
        "exe_sha256": "a"*64,
        "matches_documented_exe_sha256": True,
        "candidate_call_sites": sites,
    }


class AnsiTextPathTests(unittest.TestCase):
    def test_confirm_ansi_percent_loop_without_claiming_script_parser(self):
        result = audit_engine_evidence(fixture(), expected_sha="a"*64)
        self.assertEqual(result["status"], "verified_static_ansi_iteration_evidence_not_a_patch")
        self.assertEqual(result["text_out"]["call_vas"], ["0x41a79a", "0x41a7b9"])
        self.assertEqual(result["char_iteration"]["call_va"], "0x42ad54")
        self.assertIn("ANGELSCRIPT", result["char_iteration"]["unverified"])
        self.assertIn("not proven", result["encoding_risk"][2])

    def test_sha_guard_rejects_unrelated_build(self):
        sample = fixture()
        with self.assertRaisesRegex(ValueError, "verified AngelSLG"):
            audit_engine_evidence(sample)
        sample["matches_documented_exe_sha256"] = False
        with self.assertRaisesRegex(ValueError, "verified AngelSLG"):
            audit_engine_evidence(sample, expected_sha="a"*64)

    def test_overlapping_windows_must_agree(self):
        sample = fixture()
        row = sample["candidate_call_sites"][1]
        raw = bytearray.fromhex(row["code_window_hex"])
        raw[8] ^= 0x01  # in the overlap with the first TextOutA window
        row["code_window_hex"] = raw.hex()
        row["code_window_sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "Conflicting overlapping"):
            audit_engine_evidence(sample, expected_sha="a"*64)

    def test_percent_branch_changed_is_rejected(self):
        sample = fixture()
        row = sample["candidate_call_sites"][2]
        raw = bytearray.fromhex(row["code_window_hex"])
        i = 0x42AD41 - int(row["code_window_start_va"],16)
        self.assertEqual(raw[i], 0x25)
        raw[i] = 0x24
        row["code_window_hex"] = raw.hex()
        row["code_window_sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "differ from documented"):
            audit_engine_evidence(sample, expected_sha="a"*64)

    def test_tampered_window_digest_and_site_are_rejected(self):
        sample = fixture()
        sample["candidate_call_sites"][0]["code_window_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "invalid offsets/digest"):
            audit_engine_evidence(sample, expected_sha="a"*64)
        sample = fixture()
        sample["candidate_call_sites"][0]["site_offset_within_window"] = 97
        with self.assertRaisesRegex(ValueError, "invalid offsets/digest"):
            audit_engine_evidence(sample, expected_sha="a"*64)

    def test_duplicate_callsite_refused(self):
        sample = fixture()
        sample["candidate_call_sites"].append(dict(sample["candidate_call_sites"][0]))
        with self.assertRaisesRegex(ValueError, "Missing or duplicated"):
            audit_engine_evidence(sample, expected_sha="a"*64)

    def test_stitched_byte_map_contains_call_and_ret(self):
        sample = fixture()
        combined = stitch_evidence(sample["candidate_call_sites"])
        self.assertTrue(exactly_at(combined, 0x41A7E9, bytes.fromhex("c21400")))
        self.assertTrue(exactly_at(combined, 0x42AD3F, bytes.fromhex("83fa25")))


if __name__ == "__main__":
    unittest.main()
