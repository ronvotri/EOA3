"""Test code-neighborhood exporter using only invented PE bytes."""
import hashlib
import struct
import unittest

from probe_engine_calls import APIS, collect, bounded_va_evidence
from test_probe_game import fake_pe32, fake_pe64
from probe_game import parse_pe


class EngineCallsiteProbeTests(unittest.TestCase):
    def test_x86_textout_site_anchors_exact_signature_and_window(self):
        data = fake_pe32()
        before = hashlib.sha256(data).hexdigest()
        report = collect(data)
        self.assertEqual(report["exe_sha256"], before)
        self.assertFalse(report["matches_documented_exe_sha256"])
        self.assertEqual(report["status"], "read_only_code_neighborhoods_not_disassembly_or_patch")
        found = [x for x in report["candidate_call_sites"] if x["api"] == "TextOutA"]
        self.assertEqual(len(found), 1)
        site = found[0]
        self.assertEqual(site["site_va"], "0x401010")
        self.assertEqual(site["iat_va"], "0x401160")
        window = bytes.fromhex(site["code_window_hex"])
        assert_offset = site["site_offset_within_window"]
        self.assertEqual(window[assert_offset:assert_offset+6],
                         bytes.fromhex(site["call_bytes_hex"]))
        self.assertEqual(window[assert_offset:assert_offset+6],
                         b"\xff\x15" + struct.pack("<I", 0x401160))
        self.assertLessEqual(len(window), 96 + 6 + 48)
        self.assertEqual(hashlib.sha256(window).hexdigest(), site["code_window_sha256"])
        self.assertIsNone(report["reference_charset_context"])
        self.assertEqual(hashlib.sha256(data).hexdigest(), before)

    def test_non_executable_section_is_not_treated_as_code(self):
        data = bytearray(fake_pe32())
        # section characteristic field in the single synthetic section
        section_off = 0x98 + 0xE0
        struct.pack_into("<I", data, section_off+36, 0x40000040)
        report = collect(bytes(data))
        self.assertFalse(report["candidate_call_sites"])
        self.assertEqual(report["candidate_count_by_api"], {})

    def test_pe32_plus_is_explicitly_not_supported_for_x86_signatures(self):
        report = collect(fake_pe64())
        self.assertFalse(report["candidate_call_sites"])
        self.assertIn("unsupported_for_raw_x86_ff15_call_search", report["warnings"])

    def test_only_expected_imports_are_collected(self):
        self.assertIn("TextOutA", APIS)
        self.assertIn("CreateFontIndirectA", APIS)
        self.assertIn("MultiByteToWideChar", APIS)
        self.assertNotIn("CloseHandle", APIS)

    def test_read_only_dependent_va_sampling_and_section_type(self):
        source = fake_pe32()
        pe = parse_pe(source)
        site = bounded_va_evidence(source, pe, 0x401010, 12, True)
        self.assertEqual(site["byte_count"], 12)
        self.assertEqual(site["va"], "0x401010")
        self.assertEqual(site["bytes_sha256"], hashlib.sha256(bytes.fromhex(site["bytes_hex"])).hexdigest())
        self.assertIsNone(bounded_va_evidence(source, pe, 0x401010, 12, False))
        self.assertIsNone(bounded_va_evidence(source, pe, 0x4CE790, 12, True))
        self.assertIsNone(bounded_va_evidence(source, pe, 0x401010, 1000, True))

    def test_dependent_targets_are_guarded_by_whole_exe_sha(self):
        sample = fake_pe32()
        unrelated = collect(sample)
        self.assertEqual(unrelated["dependent_code_targets"], [])
        # Faking a matching expected hash still does not allow out-of-section
        # reads for the historical addresses on this small PE fixture.
        same = collect(sample, expected_sha256=hashlib.sha256(sample).hexdigest())
        self.assertEqual(same["dependent_code_targets"], [])
        self.assertIn("unmapped_dependent_target_length_helper_candidate", same["warnings"])

    def test_reference_hash_never_matches_unrelated_binary(self):
        sample = fake_pe32()
        report = collect(sample, expected_sha256="0" * 64)
        self.assertFalse(report["matches_documented_exe_sha256"])
        self.assertIsNone(report["reference_charset_context"])


if __name__ == "__main__":
    unittest.main()
