"""Synthetic x86 only. No copyrighted game snippets or EXE in tests."""
import json
import struct
import unittest
from unittest.mock import patch

from audit_v7_text_handoff import (
    START, END, LANDMARKS, CALLS, IAT_CALLS,
    inspect_iterator, inspect_docs,
)


def fake_iterator():
    raw=bytearray(b"\x90"*(END-START))
    for va, hexbytes in LANDMARKS.items():
        signature=bytes.fromhex(hexbytes)
        raw[va-START:va-START+len(signature)]=signature
    for va, target in CALLS.items():
        instr=b"\xe8"+struct.pack("<i",target-(va+5))
        raw[va-START:va-START+5]=instr
    for va, target in IAT_CALLS.items():
        instr=b"\xff\x15"+struct.pack("<I",target)
        raw[va-START:va-START+6]=instr
    return bytes(raw)


class V7TextHandoffTests(unittest.TestCase):
    def test_verified_ansi_slice_to_text_consumer(self):
        result=inspect_iterator(fake_iterator())
        self.assertEqual(result["next_consumer"]["target_va"],"0x41c790")
        self.assertEqual(result["temporary_copy"]["target_va"],"0x4cd5f0")
        self.assertEqual(result["source_segment"]["char_step"],
                         "user32!CharNextA via IAT 0x4F21B0")
        self.assertIn("not per byte",result["source_segment"]["optional_character_limit"]["count"])
        self.assertIn("no verified link",result["cautions"][1].lower())
        self.assertEqual(result["status"],"verified_static_ansi_substring_to_consumer_not_runtime_or_patch")

    def test_changed_percent_branch_rejected(self):
        raw=bytearray(fake_iterator())
        raw[0x42AD41-START]^=0x01
        with self.assertRaisesRegex(ValueError,"iterator instructions"):
            inspect_iterator(bytes(raw))

    def test_changed_char_next_import_refused(self):
        raw=bytearray(fake_iterator())
        raw[0x42AD56-START]^=0x40
        with self.assertRaisesRegex(ValueError,"iterator instructions|CharNextA"):
            inspect_iterator(bytes(raw))

    def test_changed_copy_target_refused(self):
        raw=bytearray(fake_iterator())
        raw[0x42AD9A-START]^=0x40
        with self.assertRaisesRegex(ValueError,"direct CALL target"):
            inspect_iterator(bytes(raw))

    def test_changed_consumer_target_refused(self):
        raw=bytearray(fake_iterator())
        raw[0x42ADDC-START]^=0x40
        with self.assertRaisesRegex(ValueError,"direct CALL target"):
            inspect_iterator(bytes(raw))

    def test_wrong_window_dimensions_rejected(self):
        with self.assertRaisesRegex(ValueError,"dimensions"):
            inspect_iterator(fake_iterator()[:-1])
        with self.assertRaisesRegex(ValueError,"dimensions"):
            inspect_iterator(fake_iterator(),start=START+1)

    def test_report_must_pass_full_font_evidence_guard(self):
        # Use explicit mocks only at the ZIP integration boundary. Structural
        # instruction semantics above remain checked byte-for-byte.
        from probe_engine_calls import REFERENCE_EXE_SHA256
        sample={
            "engine_followup_evidence.json":{
                "target_code_windows":[{
                    "purpose":"percent_iterator_context","va":hex(START),
                    "bytes_hex":fake_iterator().hex(),
                }],
            },
        }
        with patch("audit_v7_text_handoff.analyze_reports", return_value={
            "game_exe":{"sha256":REFERENCE_EXE_SHA256},
        }),patch("audit_v7_text_handoff.verify_windows") as check:
            out=inspect_docs(sample)
            check.assert_called_once()
            self.assertTrue(out["next_research_target"].lower().startswith("0x41c790"))
        with patch("audit_v7_text_handoff.analyze_reports", return_value={
            "game_exe":{"sha256":"0"*64},
        }):
            with self.assertRaisesRegex(ValueError,"not for documented"):
                inspect_docs(sample)


if __name__=="__main__":
    unittest.main()
