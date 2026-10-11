"""Synthetic diagnostics archive tests. No actual copyrighted game executable."""
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from analyze_windows_report import analyze_reports, read_zip, REQUIRED_FILES


def data():
    exe_hash = "a" * 64
    return {
        "manifest.json": {
            "status": "diagnostic_bundle_not_a_patch",
            "exe_sha256": exe_hash, "translation_count": 1881,
            "review_count": 574,
            "font_status": "local_windows_gdi_font_diagnostic_only",
        },
        "exe_preflight.json": {
            "status": "static_diagnostic_only_not_a_patch",
            "exe_filename": "AngelSLG.exe", "sha256": exe_hash,
            "architecture": "PE32", "file_size": 1232896,
            "imagebase": "0x400000", "entry_rva": "0xcfec2",
            "installation": {"data_bin_count": 40},
            "gdi_and_encoding_imports": [
                {"api": "TextOutA"}, {"api": "CreateFontIndirectA"},
                {"api": "MultiByteToWideChar"},
            ],
            "import_table_diagnostics": {
                "descriptors_read": 9, "null_terminated": True,
                "warnings": ["import_directory_size_does_not_include_null_terminator"],
            },
            "potential_x86_iat_calls": [
                {"api": "TextOutA", "candidate_call_vas": ["0x41a79a", "0x41a7b9"]},
                {"api": "CreateFontIndirectA", "candidate_call_vas": ["0x41aaab"]},
            ],
            "historical_va_hints": {
                "charset_134_historical": {"bytes_hex_at_location": "c645d786c645d8"},
            },
            "font_name_byte_offsets": {"Songti_GBK": [992532]},
        },
        "unicode_layout_report.json": {
            "status": "static_language_preflight_not_a_game_patch",
            "counts": {
                "translated": 1881, "mode_review": 574,
                "rows_with_unencodable_cp936": 1788,
            },
            "warning_counts": {
                "width_heuristic": 240,
                "longer_than_source_heuristic": 120,
            },
            "unencodable_cp936_codepoints": [{"character": "đ"}] * 74,
        },
        "font_preflight.json": {
            "status": "local_windows_gdi_font_diagnostic_only",
            "font_requested": "Segoe UI", "font_selected": "Segoe UI",
            "size_pt": 16, "dpi": 96,
            "required_unique_nonspace_characters": 165,
            "missing_glyph_candidates": [],
            "sample_extents": [
                {"id": "stage1:1149", "call": "SP_AddAction",
                 "source_line_px": [446, 523], "vi_line_px": [768, 593]},
                {"id": "stage20:3681", "call": "SetStageName",
                 "source_line_px": [107], "vi_line_px": [268]},
            ],
        },
    }


class RealReportInspectionTests(unittest.TestCase):
    def test_evidence_matches_and_not_runtime_proof(self):
        report = analyze_reports(data())
        self.assertEqual(report["status"], "evidence_summary_not_a_game_patch")
        self.assertTrue(report["pe_imports"]["null_terminated"])
        self.assertEqual(
            report["pe_imports"]["historical_x86_iat_candidate_matches"]["TextOutA"],
            ["0x41a79a", "0x41a7b9"]
        )
        self.assertTrue(report["pe_imports"]["charset_134_bytes_at_historical_location"])
        self.assertEqual(report["font_probe"]["missing_glyph_candidate_count"], 0)
        self.assertEqual(report["translation_preflight"]["unencodable_cp936_rows"], 1788)
        self.assertEqual(report["measured_desktop_font_samples_sorted_by_ratio"][0]
                         ["id"], "stage20:3681")
        self.assertIn("remain unverified", report["limits"][1])

    def test_mismatched_hash_or_unrelated_executable_is_rejected(self):
        docs = data()
        docs["exe_preflight.json"]["sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            analyze_reports(docs)
        docs = data()
        docs["exe_preflight.json"]["exe_filename"] = "bad.exe"
        with self.assertRaisesRegex(ValueError, "AngelSLG"):
            analyze_reports(docs)

    def test_inconsistent_translation_totals_are_rejected(self):
        docs = data()
        docs["manifest.json"]["translation_count"] = 0
        with self.assertRaisesRegex(ValueError, "Translation total differs"):
            analyze_reports(docs)
        docs = data()
        docs["manifest.json"]["font_status"] = "missing"
        with self.assertRaisesRegex(ValueError, "Font status differs"):
            analyze_reports(docs)

    def test_missing_font_does_not_claim_zero_missing_glyphs(self):
        docs = data()
        docs["font_preflight.json"] = {"status": "font_probe_unavailable"}
        docs["manifest.json"]["font_status"] = "font_probe_unavailable"
        report = analyze_reports(docs)
        self.assertIsNone(report["font_probe"]["missing_glyph_candidate_count"])
        self.assertFalse(report["measured_desktop_font_samples_sorted_by_ratio"])

    def test_optional_engine_windows_verify_sha_and_scope(self):
        docs = data()
        docs["engine_callsite_slices.json"] = {
            "status": "read_only_code_neighborhoods_not_disassembly_or_patch",
            "exe_sha256": "a"*64,
            "matches_documented_exe_sha256": False,
            "candidate_count_by_api": {"TextOutA": 2},
        }
        summary = analyze_reports(docs)
        self.assertTrue(summary["engine_code_slice_evidence"]["present"])
        self.assertEqual(summary["engine_code_slice_evidence"]["candidate_count_by_api"]["TextOutA"], 2)
        docs["engine_callsite_slices.json"]["exe_sha256"] = "b"*64
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            analyze_reports(docs)

    def test_six_member_zip_is_backward_compatible_and_hash_checked(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"diag-v4.zip"
            docs = data()
            docs["engine_callsite_slices.json"] = {
                "status": "read_only_code_neighborhoods_not_disassembly_or_patch",
                "exe_sha256": "a"*64,
                "candidate_count_by_api": {"TextOutA": 2},
                "matches_documented_exe_sha256": False,
            }
            with ZipFile(path, "w") as z:
                for key, value in docs.items():
                    z.writestr(key, json.dumps(value))
                z.writestr("font_preview.html", "<p>Preview</p>")
            parsed = read_zip(path)
            self.assertEqual(len(parsed), 5)
            self.assertTrue(analyze_reports(parsed)["engine_code_slice_evidence"]["present"])

    def test_eight_member_v8_zip_accepts_new_evidence_and_validates_sha(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"diag-v8.zip"
            docs = data()
            docs["engine_callsite_slices.json"] = {
                "status": "read_only_code_neighborhoods_not_disassembly_or_patch",
                "exe_sha256": "a"*64,
                "matches_documented_exe_sha256": False,
            }
            docs["engine_followup_evidence.json"] = {
                "status": "bounded_helper_caller_evidence_not_a_patch",
                "exe_sha256": "a"*64,
                "matches_documented_exe_sha256": False,
                "target_code_windows": [],
                "raw_call_reference_scan": None,
                "angelscript_marker_locations": [],
            }
            docs["renderer_trace_v8.json"] = {
                "status": "read_only_v8_renderer_trace_code_fragments_not_disassembly_or_patch",
                "exe_sha256": "a"*64,
                "matches_documented_exe_sha256": False,
                "samples": [], "palette_reference_bytes": None,
                "candidate_calls": None,
            }
            with ZipFile(path, "w") as z:
                for name, item in docs.items():
                    z.writestr(name, json.dumps(item))
                z.writestr("font_preview.html","<p>font preview test</p>")
            result = analyze_reports(read_zip(path))["renderer_trace_v8"]
            self.assertTrue(result["present"])
            self.assertFalse(result["known_exe_matched"])
            self.assertEqual(result["bounded_code_windows"], 0)
            docs["renderer_trace_v8.json"]["exe_sha256"] = "b"*64
            with self.assertRaisesRegex(ValueError, "V8 renderer trace SHA-256"):
                analyze_reports(docs)
            docs["renderer_trace_v8.json"]["exe_sha256"] = "a"*64
            docs["renderer_trace_v8.json"]["matches_documented_exe_sha256"] = True
            with self.assertRaisesRegex(ValueError, "incomplete V8"):
                analyze_reports(docs)

    def test_seven_member_v6_zip_validates_followup_sha_and_counts(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"diag-v6.zip"
            docs = data()
            docs["engine_callsite_slices.json"] = {
                "status": "read_only_code_neighborhoods_not_disassembly_or_patch",
                "exe_sha256": "a"*64,
                "matches_documented_exe_sha256": False,
            }
            docs["engine_followup_evidence.json"] = {
                "status": "bounded_helper_caller_evidence_not_a_patch",
                "exe_sha256": "a"*64,
                "matches_documented_exe_sha256": False,
                "target_code_windows": [],
                "raw_call_reference_scan": None,
                "angelscript_marker_locations": [],
            }
            with ZipFile(path, "w") as z:
                for name, content in docs.items():
                    z.writestr(name, json.dumps(content))
                z.writestr("font_preview.html", "<p>QA only</p>")
            parsed = read_zip(path)
            self.assertEqual(len(parsed), 6)
            follow = analyze_reports(parsed)["engine_followup_evidence"]
            self.assertTrue(follow["present"])
            self.assertEqual(follow["target_windows_read"], 0)
            docs["engine_followup_evidence.json"]["exe_sha256"] = "b"*64
            with self.assertRaisesRegex(ValueError, "Followup EXE SHA"):
                analyze_reports(docs)

    def test_zip_is_never_extracted_and_rejects_unexpected_files(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"diag.zip"
            with ZipFile(path, "w") as z:
                for key, value in data().items():
                    z.writestr(key, json.dumps(value))
                z.writestr("font_preview.html", "<h1>No game file</h1>")
            report = read_zip(path)
            self.assertEqual(len(report), 4)
            self.assertFalse((Path(root)/"font_preview.html").exists())
            with ZipFile(path, "a") as z:
                z.writestr("AngelSLG.exe", b"malicious")
            with self.assertRaisesRegex(ValueError, "Unexpected ZIP members"):
                read_zip(path)


if __name__ == "__main__":
    unittest.main()
