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

    def test_audited_cutscene_overlay(self):
        row = next(r for r in self.rows if r["call"] == "SP_AddAction"
                   and r["argument"] == 3 and r["mode"] == "review")
        row["mode"] = "translate"
        row["vi"] = row["source"].replace("爱尔达大陆", "lục địa Elda")
        self.assertIn(row["token"], validate_rows(self.doc, self.rows))
        row["vi"] = "Không có mã điều khiển."
        with self.assertRaises(ValueError):
            validate_rows(self.doc, self.rows)

    def test_only_description_arguments_permitted(self):
        doc = read(ROOT / "source/DataBase.json")
        rows = read(ROOT / "translations/DataBase.json")
        for call in ("AddSkillData", "AddItemData"):
            name = next(r for r in rows if r["call"] == call
                        and r["argument"] == 1 and r["mode"] == "review")
            name["mode"] = "translate"
            name["vi"] = "Tên đã đổi"
            with self.assertRaises(ValueError):
                validate_rows(doc, rows)
            name["mode"], name["vi"] = "review", ""
            description = next(r for r in rows if r["call"] == call
                               and r["argument"] == 2 and r["mode"] == "review")
            description["mode"] = "translate"
            description["vi"] = "Mô tả đã dịch"
            self.assertIn(description["token"], validate_rows(doc, rows))
            description["mode"], description["vi"] = "review", ""

    def test_wrong_overlay_argument_stays_restricted(self):
        row = next(r for r in self.rows if r["call"] == "SP_AddAction"
                   and r["mode"] == "review")
        row["argument"] = 2
        row["mode"] = "translate"
        row["vi"] = row["source"].replace("爱尔达大陆", "lục địa Elda")
        with self.assertRaises(ValueError):
            validate_rows(self.doc, self.rows)

if __name__ == "__main__":
    unittest.main()
