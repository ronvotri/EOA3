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
