"""Mock GDI tests run on Linux CI; the real font inspection is Windows-only."""
import unittest
from unittest.mock import patch

from windows_font_probe import required_characters, analyze_font, create_font_prober


def sample_rows():
    return {"mock.json": [
        {"id":"mock:0","token":0,"call":"Say","argument":1,"mode":"translate",
         "source":"%s2%t4%z18你好%N世界","vi":"%s2%t4%z18Chào đấy%NĐẹp"},
        {"id":"mock:1","token":1,"call":"MessageBox","argument":1,"mode":"review",
         "source":"中国","vi":""},
    ]}


class FontProbeTests(unittest.TestCase):
    def test_glyph_collection_excludes_markup_and_review(self):
        chars = required_characters(sample_rows())
        for ch in ("đ", "Đ", "ẹ", "â", "ơ", "ư"):
            self.assertIn(ch, chars)
        self.assertNotIn("%", chars)
        self.assertNotIn("中", chars)
        self.assertNotIn("国", chars)
        self.assertNotIn("2", chars)

    def test_fails_safely_outside_windows(self):
        with patch("windows_font_probe.platform.system", return_value="Linux"):
            with self.assertRaisesRegex(OSError, "Windows GDI"):
                create_font_prober("Segoe UI", 16)

    def test_fake_gdi_measurement_and_cleanup(self):
        closed = []
        fake = {
            "missing": lambda ch: ch == "đ",
            "pixels": lambda s: len(s) * 10,
            "face": "Mock font",
            "dpi": 96,
            "close": lambda: closed.append(True),
        }
        with patch("windows_font_probe.create_font_prober", return_value=fake):
            report = analyze_font(sample_rows(), "Mock font", 16)
        self.assertEqual(report["status"], "local_windows_gdi_font_diagnostic_only")
        self.assertEqual(report["font_selected"], "Mock font")
        self.assertTrue(any(x["char"] == "đ" for x in report["missing_glyph_candidates"]))
        self.assertTrue(report["sample_extents"])
        self.assertEqual(closed, [True])

    def test_checks_font_name_only_on_windows(self):
        with patch("windows_font_probe.platform.system", return_value="Linux"):
            with self.assertRaises(OSError):
                create_font_prober("", 16)


if __name__ == "__main__":
    unittest.main()
