"""Artificial x86 window + artificial source scripts: no game binary bundled."""
import json
import struct
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from audit_v7_palette_commands import (
    BASE, LENGTH, PALETTE_LANDMARKS, RELATIVE_CALLS,
    validate_palette_instructions, summarize_source_controls, inspect_docs,
)


def palette_fixture():
    out = bytearray(b"\x90" * LENGTH)
    for va, encoded in PALETTE_LANDMARKS.items():
        data = bytes.fromhex(encoded)
        offset = va-BASE
        out[offset:offset+len(data)] = data
    for va, target in RELATIVE_CALLS.items():
        offset = va-BASE
        out[offset:offset+5] = b"\xe8" + struct.pack("<i",target-(va+5))
    return bytes(out)


class PaletteControlAuditTests(unittest.TestCase):
    def test_16_entry_palette_index_not_proven_color_command(self):
        result=validate_palette_instructions(palette_fixture())
        self.assertEqual(result["palette_lookup"]["triple_count_inferred_from_index"],16)
        self.assertEqual(result["numeric_parse_call"]["text_pointer_offset_bytes"],2)
        self.assertEqual(result["value_application"]["fallback_constant"],"0x0000fffe")
        self.assertIn("not present",result["limits"][0])
        self.assertIn("not a proven visual output",result["limits"][1])
        self.assertEqual(result["status"],
                         "verified_static_palette_index_branch_not_token_mapping")

    def test_corrupt_signed_mod16_signature_fails(self):
        raw=bytearray(palette_fixture())
        raw[0x42ACA6-BASE] ^= 1
        with self.assertRaisesRegex(ValueError,"x86 instruction"):
            validate_palette_instructions(bytes(raw))

    def test_change_helper_destination_rejected(self):
        raw=bytearray(palette_fixture())
        raw[0x42ACCC-BASE] ^= 1
        with self.assertRaisesRegex(ValueError,"CALL destination"):
            validate_palette_instructions(bytes(raw))

    def test_callee_that_sets_sentinel_must_be_same(self):
        raw=bytearray(palette_fixture())
        raw[0x42ACED-BASE] ^= 1
        with self.assertRaisesRegex(ValueError,"CALL destination"):
            validate_palette_instructions(bytes(raw))

    def test_truncated_window_rejected(self):
        with self.assertRaisesRegex(ValueError,"384 bytes"):
            validate_palette_instructions(palette_fixture()[:-1])

    def test_control_frequency_is_evidence_not_a_claim_of_token_mapping(self):
        with TemporaryDirectory() as root:
            base=Path(root)
            a={"tokens":[[5,"%s2%t4%z18%c1你好%N"],[5,"%c1Another"],[2,"ignored"]]}
            b={"tokens":[[5,"%s8%t1%z20Text %c1"],[5,"No control"],[5,"%N"]]}
            (base/"stage1.json").write_text(json.dumps(a,ensure_ascii=False),encoding="utf-8")
            (base/"stage2.json").write_text(json.dumps(b,ensure_ascii=False),encoding="utf-8")
            summary=summarize_source_controls(base,expected_files=2)
            self.assertEqual(summary["text_tokens"],5)
            self.assertEqual(summary["control_occurrences"]["%c"],3)
            self.assertEqual(summary["control_occurrences"]["%N"],2)
            self.assertEqual(summary["numeric_values"]["%c"],{"1":3})
            self.assertEqual(summary["numeric_values"]["%s"],{"2":1,"8":1})
            with self.assertRaisesRegex(ValueError,"corpus count"):
                summarize_source_controls(base,expected_files=40)

    def test_integration_requires_existing_full_v7_hash_checks(self):
        from probe_engine_calls import REFERENCE_EXE_SHA256
        data={"engine_followup_evidence.json":{
            "target_code_windows":[{"purpose":"percent_iterator_context",
                                     "va":hex(BASE),"byte_count":LENGTH,
                                     "bytes_hex":palette_fixture().hex()}]}}
        corpus={"source_json_files":40,"text_tokens":4236,
                "control_occurrences":{"%c":1634},
                "numeric_values":{"%c":{"1":1634}}}
        with patch("audit_v7_palette_commands.analyze_reports",return_value={
            "game_exe":{"sha256":REFERENCE_EXE_SHA256}
        }),patch("audit_v7_palette_commands.verify_windows") as verify,\
             patch("audit_v7_palette_commands.summarize_source_controls",return_value=corpus):
            res=inspect_docs(data,Path("unread"))
            verify.assert_called_once()
            self.assertEqual(res["source_corpus"]["numeric_values"]["%c"]["1"],1634)
            self.assertIn("remains unknown",res["relationship_to_source"])
        with patch("audit_v7_palette_commands.analyze_reports",return_value={
            "game_exe":{"sha256":"0"*64}
        }):
            with self.assertRaisesRegex(ValueError,"Unrecognized"):
                inspect_docs(data,Path("unread"))


if __name__ == "__main__":
    unittest.main()
