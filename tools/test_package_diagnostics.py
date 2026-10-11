"""Package tests use fake 40-file script collection and harmless dummy tools."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from package_diagnostics import SCRIPTS, package


class PackageDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "source").mkdir()
        (self.root / "translations").mkdir()
        for i in range(40):
            (self.root/"source"/("stage%d.json" % i)).write_text("{}")
            (self.root/"translations"/("stage%d.json" % i)).write_text("[]")
        for name in SCRIPTS:
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# mock diagnostic tool\n", encoding="utf-8")
        self.out = self.root / "build" / "diagnostic-tool.zip"

    def test_contains_only_tools_and_script_jsons(self):
        result = package(self.root, self.out)
        self.assertEqual(result["source_scripts"], 40)
        self.assertEqual(result["file_count"], len(SCRIPTS)+80+2)
        with ZipFile(self.out) as z:
            entries = z.namelist()
            self.assertIn("EOA3-KiemTra-Windows.cmd", entries)
            self.assertIn("tools/windows_diagnostic_bundle.py", entries)
            self.assertIn("README-KIEMTRA.txt", entries)
            self.assertIn("source/stage1.json", entries)
            self.assertIn("translations/stage1.json", entries)
            self.assertFalse(any(n.lower().endswith((".exe",".dll",".ttf",".otf",".bin"))
                                 for n in entries))
            self.assertFalse(any("DISPLAY_NAMES_DRAFT" in n for n in entries))
            manifest = json.loads(z.read("MANIFEST.json"))
            self.assertEqual(manifest["source_scripts"], 40)
            self.assertFalse(manifest["includes_game_executable"])
            self.assertEqual(
                manifest["file_sha256"]["source/stage0.json"],
                hashlib.sha256(b"{}").hexdigest()
            )
            self.assertTrue(all(not n.startswith("/") and ".." not in Path(n).parts for n in entries))

    def test_missing_translation_is_rejected(self):
        (self.root/"translations"/"stage19.json").unlink()
        with self.assertRaisesRegex(ValueError, "translation"):
            package(self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_wrong_number_of_sources_is_rejected(self):
        (self.root/"source"/"stage19.json").unlink()
        with self.assertRaisesRegex(ValueError, "40"):
            package(self.root, self.out)

    def test_output_inside_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "source"):
            package(self.root, self.root/"source"/"bad.zip")
        self.assertFalse((self.root/"source"/"bad.zip").exists())


if __name__ == "__main__":
    unittest.main()
