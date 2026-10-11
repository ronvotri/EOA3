import copy
import unittest
from scripts import ROOT, read, validate_rows, pack

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.doc = read(ROOT / "source/stage1.json")
        self.rows = read(ROOT / "translations/stage1.json")

    def test_unicode_translation_and_controls(self):
        row = next(r for r in self.rows if "发生什么事了吗" in r["source"])
        row["vi"] = row["source"].replace("发生什么事了吗", "Có chuyện gì xảy ra vậy")
        result = validate_rows(self.doc, self.rows)
        self.assertIn(row["token"], result)
        with self.assertRaises(UnicodeEncodeError):
            pack(self.doc, result)
        row["vi"] = "Có chuyện gì xảy ra vậy?"
        with self.assertRaises(ValueError):
            validate_rows(self.doc, self.rows)

    def test_locked_and_missing(self):
        row = next(r for r in self.rows if r["mode"] == "locked")
        row["vi"] = "Changed"
        with self.assertRaises(ValueError):
            validate_rows(self.doc, self.rows)
        row["vi"] = ""
        with self.assertRaises(ValueError):
            validate_rows(self.doc, self.rows[:-1])

if __name__ == "__main__":
    unittest.main()
