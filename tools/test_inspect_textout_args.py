"""Regression tests use invented byte windows, not user/game binaries."""
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from inspect_textout_args import SIGNATURES, attest_windows, summarize_zip
from test_analyze_windows_report import data


def fake_sites():
    calls = []
    for addr, rule in SIGNATURES.items():
        prefix = bytes.fromhex(rule["prefix"])
        before = bytearray(96)
        before[-len(prefix):] = prefix
        if rule["api"] == "CreateFontIndirectA":
            before[4:4+8] = bytes.fromhex("c745d090010000")
            before[16:20] = bytes.fromhex("c645d786")
        signature = b"\xff\x15" + struct.pack("<I", int(rule["iat"], 16))
        payload = bytes(before) + signature + b"\x90" * 48
        calls.append({
            "api": rule["api"], "site_va": addr,
            "iat_va": rule["iat"],
            "code_window_start_va": hex(int(addr, 16) - 96),
            "site_offset_within_window": 96,
            "code_window_hex": payload.hex(),
            "code_window_sha256": hashlib.sha256(payload).hexdigest(),
        })
    return {"candidate_call_sites": calls}


class TextOutArgumentsTests(unittest.TestCase):
    def test_exact_three_argument_patterns(self):
        result = attest_windows(fake_sites())
        self.assertEqual(result["verified_sites"], 3)
        self.assertTrue(all(r["verified"] for r in result["entries"]))
        self.assertEqual(result["entries"][0]["decoded_stack_arguments"]["byte_count"], 2)
        self.assertIn("0x4CE790",
                      result["entries"][1]["decoded_stack_arguments"]["byte_count"])
        self.assertEqual(result["entries"][2]["decoded_stack_arguments"]["lfCharSet_byte"], 134)

    def test_corrupt_code_and_digest_are_detected(self):
        data = fake_sites()
        data["candidate_call_sites"][0]["code_window_hex"] = "00" * 150
        result = attest_windows(data)
        self.assertEqual(result["verified_sites"], 2)
        self.assertFalse(result["entries"][0]["verified"])

    def test_wrong_font_charset_not_assumed(self):
        data = fake_sites()
        item = data["candidate_call_sites"][2]
        raw = bytearray.fromhex(item["code_window_hex"])
        raw[16:20] = b"\xc6\x45\xd7\x00"
        item["code_window_hex"] = raw.hex()
        item["code_window_sha256"] = hashlib.sha256(raw).hexdigest()
        result = attest_windows(data)
        self.assertFalse(result["entries"][2]["verified"])

    def test_refuses_unverified_sha_even_if_calls_match(self):
        docs = data()
        docs["engine_callsite_slices.json"] = {
            **fake_sites(),
            "status": "read_only_code_neighborhoods_not_disassembly_or_patch",
            "exe_sha256": "a"*64,
            "matches_documented_exe_sha256": False,
        }
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"fake.zip"
            with ZipFile(path, "w") as z:
                for key, value in docs.items():
                    z.writestr(key, json.dumps(value))
                z.writestr("font_preview.html", "Preview")
            with self.assertRaisesRegex(ValueError, "specifically documented"):
                summarize_zip(path)


if __name__ == "__main__":
    unittest.main()
