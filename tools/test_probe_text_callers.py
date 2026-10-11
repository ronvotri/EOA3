"""Test bounded x86 CALL candidate scanning using artificial PE32 bytes only."""
import hashlib
import struct
import unittest

from probe_text_callers import collect, MAX_PER_REGION
from test_probe_game import fake_pe32


def fixture(n=1):
    out = bytearray(fake_pe32())
    # All 5-byte CALLs in this synthetic .text target the same in-section VA.
    # This is deliberately not a full disassembler; output is candidate-only.
    for i in range(n):
        pos = 0x220 + i*5
        source_va = 0x401000+(pos-0x200)
        dest = 0x401400
        struct.pack_into("<Bi", out, pos, 0xE8, dest-(source_va+5))
    return bytes(out)


def scan(data):
    return collect(data, expected_sha=hashlib.sha256(data).hexdigest(),
                   target_ranges=(("test_candidate_function_region",0x4013F0,0x401410),),
                   iat_addresses=(0x401160,))


class TextCallerProbeTests(unittest.TestCase):
    def test_known_iat_and_direct_candidate_addresses(self):
        data=fixture()
        original_sha=hashlib.sha256(data).hexdigest()
        report=scan(data)
        self.assertEqual(report["exe_sha256"], original_sha)
        self.assertEqual(report["status"], "bounded_raw_rel32_call_candidate_scan_not_disassembly")
        self.assertEqual(len(report["call_candidates"]), 1)
        found=report["call_candidates"][0]
        self.assertEqual(found["candidate_call_va"], "0x401020")
        self.assertEqual(found["candidate_target_va"], "0x401400")
        self.assertEqual(found["target_region"], "test_candidate_function_region")
        self.assertEqual(report["iat_api_names"], [
            {"iat_va":"0x401160", "dll":"GDI32.dll", "api":"TextOutA"}
        ])
        self.assertEqual(hashlib.sha256(data).hexdigest(),original_sha)

    def test_unknown_sha_produces_no_legacy_address_xrefs(self):
        report=collect(fixture())
        self.assertEqual(report["status"],"unrecognized_executable_no_legacy_address_probe")
        self.assertFalse(report["call_candidates"])
        self.assertFalse(report["iat_api_names"])

    def test_candidates_are_bounded_and_never_claim_proof(self):
        data=fixture(75)
        result=scan(data)
        self.assertEqual(len(result["call_candidates"]),MAX_PER_REGION)
        self.assertEqual(result["candidate_count_by_region"]["test_candidate_function_region"],MAX_PER_REGION)
        self.assertTrue(any("false positives" in item for item in result["limitations"]))
        self.assertTrue(any("NOT verified function entries" in item for item in result["limitations"]))

    def test_false_positive_instruction_alignment_is_explicitly_unverified(self):
        data=bytearray(fixture())
        # An E8 sequence embedded in data/text inside an executable section
        # may be misidentified. Scanner must label it only as a candidate.
        struct.pack_into("<Bi", data, 0x240, 0xE8, 0x401400-(0x401040+5))
        result=scan(bytes(data))
        self.assertEqual(len(result["call_candidates"]),2)
        self.assertTrue(all("candidate" in row["candidate_call_va"] or "candidate" in row
                            for row in result["call_candidates"]))


if __name__=="__main__":
    unittest.main()
