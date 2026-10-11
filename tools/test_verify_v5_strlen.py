"""Synthetic-only tests; no proprietary game EXE or full helper bytes in repo."""
import hashlib
from unittest.mock import patch
import unittest

from verify_v5_strlen import (
    verify_helper, inspect_v5_docs, HELPER_FUNCTION_LENGTH,
    RET_OFFSETS, HELPER_VA, SPACE_VA,
)


def synthetic_strlen_shape():
    b = bytearray(192)
    anchors = {
        0x00: "8b4c2404f7c103000000",
        0x0C: "8a014184c0",
        0x20: "8b01bafffefe7e",
        0x53: "8d41ff8b4c24042bc1c3",
        0x5D: "8d41fe8b4c24042bc1c3",
        0x67: "8d41fd8b4c24042bc1c3",
        0x71: "8d41fc8b4c24042bc1c3",
        0x7B: "cccccccccc",
    }
    for offset, hexstr in anchors.items():
        part = bytes.fromhex(hexstr)
        b[offset:offset+len(part)] = part
    return bytes(b)


class V5StringHelperTests(unittest.TestCase):
    def test_structural_strlen_signatures_and_return_paths(self):
        b = synthetic_strlen_shape()
        self.assertEqual(len(b), 192)
        self.assertEqual(HELPER_FUNCTION_LENGTH, 123)
        self.assertEqual(tuple(b[x] for x in RET_OFFSETS), (0xC3,) * 4)
        with patch("verify_v5_strlen.HELPER_WINDOW_SHA256", hashlib.sha256(b).hexdigest()), \
             patch("verify_v5_strlen.HELPER_FUNCTION_SHA256", hashlib.sha256(b[:123]).hexdigest()):
            self.assertTrue(verify_helper(b))

    def test_mutation_rejected_even_when_digest_matches(self):
        b = bytearray(synthetic_strlen_shape())
        b[0x20] ^= 1
        raw = bytes(b)
        with patch("verify_v5_strlen.HELPER_WINDOW_SHA256", hashlib.sha256(raw).hexdigest()), \
             patch("verify_v5_strlen.HELPER_FUNCTION_SHA256", hashlib.sha256(raw[:123]).hexdigest()):
            self.assertFalse(verify_helper(raw))

    def test_truncated_helper_rejected(self):
        self.assertFalse(verify_helper(b"8b4c2404"))
        self.assertFalse(verify_helper(b""))

    def test_wrong_exe_sha_rejected_before_semantic_claims(self):
        from test_analyze_windows_report import data
        docs = data()
        docs["engine_callsite_slices.json"] = {
            "status": "read_only_code_neighborhoods_not_disassembly_or_patch",
            "exe_sha256": "a" * 64,
            "matches_documented_exe_sha256": True,
        }
        with self.assertRaisesRegex(ValueError, "Not the verified"):
            inspect_v5_docs(docs)

    def test_missing_dependent_targets_not_called_strlen(self):
        from test_analyze_windows_report import data
        from probe_engine_calls import REFERENCE_EXE_SHA256
        docs = data()
        docs["manifest.json"]["exe_sha256"] = REFERENCE_EXE_SHA256
        docs["exe_preflight.json"]["sha256"] = REFERENCE_EXE_SHA256
        docs["engine_callsite_slices.json"] = {
            "status": "read_only_code_neighborhoods_not_disassembly_or_patch",
            "exe_sha256": REFERENCE_EXE_SHA256,
            "matches_documented_exe_sha256": True,
            "dependent_code_targets": [],
        }
        with patch("verify_v5_strlen.attest_windows", return_value={"verified_sites": 3, "expected_sites": 3}):
            with self.assertRaisesRegex(ValueError, "Missing V5 dependent evidence"):
                inspect_v5_docs(docs)

    def test_tampered_auxiliary_evidence_rejected(self):
        from test_analyze_windows_report import data
        from probe_engine_calls import REFERENCE_EXE_SHA256
        docs = data()
        docs["manifest.json"]["exe_sha256"] = REFERENCE_EXE_SHA256
        docs["exe_preflight.json"]["sha256"] = REFERENCE_EXE_SHA256
        docs["engine_callsite_slices.json"] = {
            "status": "read_only_code_neighborhoods_not_disassembly_or_patch",
            "exe_sha256": REFERENCE_EXE_SHA256,
            "matches_documented_exe_sha256": True,
            "dependent_code_targets": [
                {"va": HELPER_VA, "bytes_hex": synthetic_strlen_shape().hex(),
                 "byte_count": 192, "bytes_sha256": "0" * 64,
                 "section": ".text", "truncated_to_section_boundary": False},
                {"va": SPACE_VA, "bytes_hex": (b"  \0\0" + b"X" * 12).hex(),
                 "byte_count": 16, "bytes_sha256": "0" * 64,
                 "section": ".rdata", "truncated_to_section_boundary": False},
            ],
        }
        with patch("verify_v5_strlen.attest_windows", return_value={"verified_sites": 3, "expected_sites": 3}):
            with self.assertRaisesRegex(ValueError, "evidence mismatch"):
                inspect_v5_docs(docs)

    def test_utf8_byte_length_differs_from_unicode_characters(self):
        word = "Việt"
        self.assertEqual(len(word), 4)
        self.assertEqual(len(word.encode("utf8")), 6)
        with self.assertRaises(UnicodeEncodeError):
            word.encode("cp936")


if __name__ == "__main__":
    unittest.main()
