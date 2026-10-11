"""Tests use synthetic translation rows only, no copyrighted executable."""
import copy
import unittest

from audit_unicode_layout import (
    analyze, can_encode_cp936, logical_lines, review_row, text_width,
    PROBE_GRAPHEME_SAMPLE,
)


def row(vi, source="你好%N世界", ident="mock:7", call="Say"):
    return {"id": ident, "token": 7, "call": call, "argument": 1,
            "mode": "translate", "source": source, "vi": vi}


class UnicodeLayoutTests(unittest.TestCase):
    def test_control_sequences_not_rendered(self):
        lines = logical_lines("%s2%t4%z18%c1Xin chào%NĐúng rồi")
        self.assertEqual(lines, ["Xin chào", "Đúng rồi"])
        self.assertEqual(text_width(lines[0]), len("Xin chào"))

    def test_width_is_only_heuristic(self):
        self.assertEqual(text_width("A\u0301"), 1)
        self.assertEqual(text_width("á"), 1)
        self.assertEqual(text_width("中"), 2)
        self.assertEqual(text_width("á中"), 3)

    def test_legacy_encoding_incompatibility_is_reported(self):
        self.assertTrue(can_encode_cp936("A"))
        self.assertFalse(can_encode_cp936("ế"))
        detail = review_row(row("Trời ơi%Nđược mà"), "mock.json", width_cells=24)
        self.assertTrue(detail["legacy_cp936_incompatible"])
        self.assertEqual(detail["line_count"], 2)

    def test_preserves_line_break_semantics_and_controls(self):
        x = row("%s2%t4%z18%c1Lửa cháy%NViệt hóa",
                source="%s2%t4%z18%c1你好%N世界")
        d = review_row(x, "mock.json")
        self.assertNotIn("control_mismatch", d["flags"])
        x["vi"] = x["vi"].replace("%N", "%N2")
        d = review_row(x, "mock.json")
        self.assertIn("control_mismatch", d["flags"])

    def test_diagnostic_flags_are_not_pixel_claims(self):
        d = review_row(row("A" * 100, source="你好"), "mock.json",
                       width_cells=25, expansion=1.5)
        self.assertIn("width_heuristic", d["flags"])
        self.assertIn("longer_than_source_heuristic", d["flags"])

    def test_unicode_normalization_warning(self):
        d = review_row(row("Ca\u0301m ơn"), "mock.json")
        self.assertIn("non_nfc", d["flags"])
        d = review_row(row("Cám ơn"), "mock.json")
        self.assertNotIn("non_nfc", d["flags"])

    def test_literal_newline_is_diagnostic(self):
        d = review_row(row("Hai\nhàng"), "mock.json")
        self.assertIn("literal_newline", d["flags"])

    def test_report_counts_do_not_include_review(self):
        src = {"stage1.json": [
            row("%s1%t4%z18Chào nhé", source="%s1%t4%z18你好"),
            {"id": "mock:8", "token": 8, "mode": "review", "source": "名字", "vi": ""},
            {"id": "mock:9", "token": 9, "mode": "locked", "source": "flag", "vi": ""},
        ]}
        report = analyze(src, width_cells=20)
        self.assertEqual(report["counts"]["translated"], 1)
        self.assertEqual(report["counts"]["mode_review"], 1)
        self.assertEqual(report["counts"]["mode_locked"], 1)
        self.assertEqual(report["status"], "static_language_preflight_not_a_game_patch")
        self.assertTrue(report["font_probe_cases"][-1]["id"].startswith("synthetic-"))

    def test_full_accent_sample(self):
        chars = PROBE_GRAPHEME_SAMPLE
        for char in ("ă", "â", "ê", "ô", "ơ", "ư", "đ", "ắ", "ệ", "ộ", "ỡ", "ự"):
            self.assertIn(char, chars)
        self.assertFalse(can_encode_cp936("ỡ"))


if __name__ == "__main__":
    unittest.main()
