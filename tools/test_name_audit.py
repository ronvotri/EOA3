import copy
import unittest

from audit_names import DRAFT_PATH, DB_PATH, read, verify_draft, reference_report


class NameAuditTests(unittest.TestCase):
    def setUp(self):
        self.draft = read(DRAFT_PATH)
        self.database = read(DB_PATH)

    def test_complete_display_only_draft(self):
        self.assertEqual(dict(verify_draft(self.draft, self.database)),
                         {"AddGroundData": 14, "AddSkillData": 63, "AddItemData": 58, "AddClassData": 360, "AddRaceData": 12, "AddUserBank": 28, "AddCard": 38})
        self.assertTrue(all(r["mode"] == "review" for r in self.database
                            if r["token"] in {x["token"] for x in self.draft["entries"]}))

    def test_cannot_silently_change_source(self):
        draft = copy.deepcopy(self.draft)
        draft["entries"][0]["source"] = "wrong reference"
        with self.assertRaises(ValueError):
            verify_draft(draft, self.database)

    def test_cannot_promote_unverified_name(self):
        db = copy.deepcopy(self.database)
        tok = self.draft["entries"][0]["token"]
        next(r for r in db if r["token"] == tok)["mode"] = "translate"
        with self.assertRaises(ValueError):
            verify_draft(self.draft, db)

    def test_draft_must_not_be_deployed(self):
        draft = copy.deepcopy(self.draft)
        draft["status"] = "approved"
        with self.assertRaises(ValueError):
            verify_draft(draft, self.database)

    def test_reject_missing_coverage(self):
        draft = copy.deepcopy(self.draft)
        draft["entries"].pop()
        with self.assertRaises(ValueError):
            verify_draft(draft, self.database)

    def test_duplicate_class_names_have_one_translation(self):
        seen = {}
        classes = [x for x in self.draft["entries"] if x["call"] == "AddClassData"]
        self.assertEqual(len(classes), 360)
        for row in classes:
            name = row["source"].strip()
            if name in seen:
                self.assertEqual(seen[name], row["vi_draft"])
            else:
                seen[name] = row["vi_draft"]
        self.assertEqual(len(seen), 95)

    def test_static_scan_has_explicit_uncertainty(self):
        report = reference_report(self.database)
        self.assertEqual(report["review_rows_scanned"], 573)
        self.assertEqual(report["files_scanned"], 40)
        self.assertIn("does NOT prove", report["caution"])


if __name__ == "__main__":
    unittest.main()
