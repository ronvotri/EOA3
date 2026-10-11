"""Offline diagnostic ZIP tests use an invented PE32 binary, never game files."""
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from font_preview import make_html
from test_probe_game import fake_pe32
from windows_diagnostic_bundle import create_bundle


def mock_font_analyzer(sources, font_name, size_pt):
    return {
        "status": "local_windows_gdi_font_diagnostic_only",
        "font_requested": font_name,
        "font_selected": font_name,
        "size_pt": size_pt,
        "missing_glyph_candidates": [],
        "sample_extents": [],
    }


class WindowsBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "game"
        self.game.mkdir()
        self.exe = self.game / "AngelSLG.exe"
        self.exe.write_bytes(fake_pe32())
        (self.game / "Data").mkdir()
        (self.game / "Data" / "stage1.bin").write_bytes(b"dummy asset")
        (self.root / "translation_source" / "source").mkdir(parents=True)
        (self.root / "translation_source" / "translations").mkdir()
        self.fake_root = self.root / "translation_source"
        doc = {"tokens": [[5, "%s1%t2%z18你好%N世界"]]}
        rows = [{"id": "stage1:0", "token": 0, "call": "Say", "argument": 1,
                 "mode": "translate", "source": "%s1%t2%z18你好%N世界",
                 "vi": "%s1%t2%z18Xin chào%NThế giới"}]
        (self.fake_root / "source" / "stage1.json").write_text(
            json.dumps(doc), encoding="utf-8"
        )
        (self.fake_root / "translations" / "stage1.json").write_text(
            json.dumps(rows, ensure_ascii=False), encoding="utf-8"
        )

    def test_bundle_has_report_not_game_bytes(self):
        out = self.root / "report" / "EOA3-Diagnostics.zip"
        original_exe = self.exe.read_bytes()
        original_asset = (self.game / "Data" / "stage1.bin").read_bytes()
        result = create_bundle(self.exe, out, "Segoe UI", 16, self.fake_root,
                               mock_font_analyzer)
        self.assertEqual(result["path"], out)
        self.assertEqual(result["manifest"]["translation_count"], 1)
        self.assertEqual(result["manifest"]["status"],
                         "diagnostic_bundle_not_a_patch")
        with ZipFile(out) as z:
            self.assertEqual(z.namelist(), result["manifest"]["contents"])
            exe_report = json.loads(z.read("exe_preflight.json"))
            engine = json.loads(z.read("engine_callsite_slices.json"))
            self.assertEqual(engine["status"], "read_only_code_neighborhoods_not_disassembly_or_patch")
            self.assertEqual(engine["exe_sha256"], exe_report["sha256"])
            self.assertEqual(engine["candidate_count_by_api"]["TextOutA"], 1)
            self.assertEqual(exe_report["architecture"], "PE32")
            static_report = json.loads(z.read("unicode_layout_report.json"))
            self.assertEqual(static_report["counts"]["translated"], 1)
            self.assertEqual(json.loads(z.read("font_preflight.json"))
                             ["font_selected"], "Segoe UI")
            self.assertIn("Xin chào".encode("utf-8"),
                          z.read("font_preview.html"))
            for name in z.namelist():
                self.assertFalse(name.lower().endswith(".exe"))
                self.assertFalse(name.endswith(".bin"))
                self.assertNotIn(str(self.root).encode(), z.read(name))
        self.assertEqual(self.exe.read_bytes(), original_exe)
        self.assertEqual((self.game / "Data" / "stage1.bin").read_bytes(),
                         original_asset)

    def test_missing_font_still_produces_static_bundle(self):
        def fail_font(sources, font_name, size_pt):
            raise OSError("fake GDI failure")
        out = self.root / "report.zip"
        result = create_bundle(self.exe, out, source_root=self.fake_root,
                               font_analyzer=fail_font)
        self.assertEqual(result["manifest"]["font_status"],
                         "font_probe_unavailable")
        with ZipFile(out) as z:
            self.assertEqual(json.loads(z.read("font_preflight.json"))
                             ["reason"], "OSError")

    def test_rejects_wrong_exe_and_input_output_collision(self):
        with self.assertRaisesRegex(ValueError, "Output"):
            create_bundle(self.exe, self.exe, source_root=self.fake_root,
                          font_analyzer=mock_font_analyzer)
        renamed = self.root / "unknown.exe"
        renamed.write_bytes(fake_pe32())
        with self.assertRaisesRegex(ValueError, "AngelSLG"):
            create_bundle(renamed, self.root / "x.zip",
                          source_root=self.fake_root,
                          font_analyzer=mock_font_analyzer)

    def test_output_never_written_inside_game_folder(self):
        forbidden = self.game / "report.zip"
        with self.assertRaisesRegex(ValueError, "outside the game"):
            create_bundle(self.exe, forbidden,
                          source_root=self.fake_root,
                          font_analyzer=mock_font_analyzer)
        self.assertFalse(forbidden.exists())

    def test_html_escapes_untrusted_strings(self):
        report = {"status": "static_language_preflight_not_a_game_patch",
                  "font_probe_cases": [
                      {"id": "x<script>alert(1)</script>", "call": "Say",
                       "source": "<img src=x onerror=alert(1)>",
                       "vi": "Xin <script>đúng</script>%Ngiới"},
                  ]}
        html = make_html(report, 'A";background:red;')
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertNotIn("<img src=", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("font-family", html)
        self.assertIn("Xin &lt;script&gt;đúng&lt;/script&gt;", html)


if __name__ == "__main__":
    unittest.main()
