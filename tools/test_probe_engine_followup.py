"""Synthetic PE tests for bounded, SHA-locked code follow-up collection."""
import hashlib
import unittest
from unittest.mock import patch

from probe_engine_followup import (
    TARGET_MAGIC, TARGETS, collect_followup, find_magic_references, MAX_MAGIC_HITS
)
from probe_game import parse_pe
from probe_engine_calls import bounded_va_evidence, MAX_TARGET_WINDOW_BYTES
from test_probe_game import fake_pe32


class EngineFollowupTests(unittest.TestCase):
    def test_mismatched_sha_exposes_no_historical_windows_or_candidates(self):
        result=collect_followup(fake_pe32())
        self.assertFalse(result["matches_documented_exe_sha256"])
        self.assertEqual(result["target_code_windows"], [])
        self.assertIsNone(result["raw_call_reference_scan"])
        self.assertEqual(result["angelscript_marker_locations"], [])
        self.assertIn("wrong_executable_sha_no_historical_va_reads", result["warnings"])
        self.assertIn("not_a_patch", result["status"])

    def test_only_bounded_helper_addresses_are_requested(self):
        self.assertEqual([hex(x[1]) for x in TARGETS],
                         ["0x41a7f0","0x41a8c0","0x41aa00","0x42ac60"])
        self.assertLess(sum(x[2] for x in TARGETS), 1600)
        self.assertEqual({x[0] for x in TARGETS},
                         {"font_helper_one_0x41a7f0","font_helper_two_0x41a8c0",
                          "font_initializer_before_calls","percent_iterator_context"})

    def test_exact_hash_on_sample_reports_unmapped_targets_not_game_damage(self):
        sample=fake_pe32()
        report=collect_followup(sample, expected_sha=hashlib.sha256(sample).hexdigest())
        self.assertTrue(report["matches_documented_exe_sha256"])
        self.assertEqual(report["target_code_windows"], [])
        self.assertEqual(len([w for w in report["warnings"]
                              if w.startswith("unmapped_or_truncated_code_target_")]),4)
        self.assertEqual(report["raw_call_reference_scan"]["status"],
                         "bounded_raw_rel32_call_candidate_scan_not_disassembly")
        self.assertTrue(any("false positives" in s for s in report["limitations"]))

    def test_magic_marker_is_only_heuristic_and_has_valid_mapped_va(self):
        sample=bytearray(fake_pe32())
        pos=0x250
        sample[pos:pos+len(TARGET_MAGIC)]=TARGET_MAGIC
        metadata=parse_pe(bytes(sample))
        markers=find_magic_references(bytes(sample), metadata)
        match=[m for m in markers if m["file_offset"] == pos]
        self.assertEqual(len(match),1)
        self.assertEqual(match[0]["rva_mapped_va"],"0x401050")
        self.assertIn("not decoded instructions", match[0]["interpretation"])

    def test_magic_marker_count_has_budget(self):
        sample=bytearray(fake_pe32())
        for i in range(14):
            offset=0x200+i*13
            sample[offset:offset+len(TARGET_MAGIC)]=TARGET_MAGIC
        out=find_magic_references(bytes(sample),parse_pe(bytes(sample)))
        self.assertEqual(len(out),MAX_MAGIC_HITS)

    def test_all_four_actual_v6_lengths_are_allowed_and_exact(self):
        sample = fake_pe32()
        sha = hashlib.sha256(sample).hexdigest()
        targets = (
            ("first_288", 0x401010, 288),
            ("second_448", 0x401070, 448),
            ("init_192", 0x4010D0, 192),
            ("loop_384", 0x401130, 384),
        )
        report = collect_followup(sample, expected_sha=sha, targets=targets)
        self.assertEqual(len(report["target_code_windows"]), 4)
        self.assertEqual(
            [w["byte_count"] for w in report["target_code_windows"]],
            [288, 448, 192, 384])
        for item in report["target_code_windows"]:
            actual = bytes.fromhex(item["bytes_hex"])
            self.assertEqual(hashlib.sha256(actual).hexdigest(), item["bytes_sha256"])
            self.assertFalse(item["truncated_to_section_boundary"])

    def test_reader_cap_and_section_boundary_enforced(self):
        sample = fake_pe32()
        metadata = parse_pe(sample)
        self.assertEqual(MAX_TARGET_WINDOW_BYTES, 512)
        self.assertEqual(
            bounded_va_evidence(sample, metadata, 0x401010, 448, True)["byte_count"], 448)
        self.assertIsNone(
            bounded_va_evidence(sample, metadata, 0x401010, 513, True))
        self.assertIsNone(
            bounded_va_evidence(sample, metadata, 0x401010, 448, False))
        with self.assertRaisesRegex(ValueError, "bounded section reader cap"):
            collect_followup(
                sample, expected_sha=hashlib.sha256(sample).hexdigest(),
                targets=(("over_cap", 0x401010, 513),))

    def test_known_exe_fails_closed_if_required_helper_window_missing(self):
        sample = fake_pe32()
        sha = hashlib.sha256(sample).hexdigest()
        # Treat this synthetic file as a known build to exercise the safety
        # branch: historically matched addresses must not silently vanish.
        with patch("probe_engine_followup.REFERENCE_EXE_SHA256", sha):
            with self.assertRaisesRegex(ValueError, "refusing incomplete report"):
                collect_followup(sample, expected_sha=sha)

    def test_no_executable_modified_during_bounded_read(self):
        sample=fake_pe32()
        before=hashlib.sha256(sample).hexdigest()
        collect_followup(sample,expected_sha=before)
        self.assertEqual(hashlib.sha256(sample).hexdigest(),before)


if __name__=="__main__":
    unittest.main()
