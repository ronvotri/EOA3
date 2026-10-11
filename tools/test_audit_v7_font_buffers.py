"""Synthetic x86 snippets only: no original game code or executable in tests."""
import hashlib
import unittest

from audit_v7_font_buffers import (
    CONTIG_START, CONTIG_END, EXPECTED, MARKERS, DIRECT_CALLS,
    REFERENCE_EXE_SHA256, verify_windows,
)


def sample():
    memory = {va:0x90 for va in range(CONTIG_START,CONTIG_END+1)}
    memory.update({va:0x90 for va in range(0x42AC60,0x42ADE0)})
    for va, signature in MARKERS.items():
        for offset, value in enumerate(bytes.fromhex(signature)):
            memory[va+offset]=value
    for va, target in DIRECT_CALLS.items():
        call=b"\xe8"+(target-va-5).to_bytes(4,"little",signed=True)
        for offset, value in enumerate(call):
            memory[va+offset]=value
    items,expected={},{}
    rows=[]
    for name,(va,size,_) in EXPECTED.items():
        chunk=bytes(memory[address] for address in range(va,va+size))
        sha=hashlib.sha256(chunk).hexdigest()
        expected[name]=(va,size,sha)
        rows.append({
            "purpose":name,"va":hex(va),"byte_count":size,
            "section":".text","truncated_to_section_boundary":False,
            "bytes_hex":chunk.hex(),"bytes_sha256":sha,
        })
    region=bytes(memory[va] for va in range(CONTIG_START,CONTIG_END+1))
    report={
        "status":"bounded_helper_caller_evidence_not_a_patch",
        "exe_sha256":REFERENCE_EXE_SHA256,
        "matches_documented_exe_sha256":True,
        "target_code_windows":rows,
    }
    return report,expected,hashlib.sha256(region).hexdigest()


class FontBufferAuditTests(unittest.TestCase):
    def test_all_four_windows_and_contiguous_overlaps(self):
        report,expected,sha=sample()
        result=verify_windows(report,expected,sha)
        self.assertEqual(len(result),4)
        self.assertEqual(result["font_helper_two_0x41a8c0"]["bytes"],448)

    def test_missing_or_duplicate_window_fails_closed(self):
        report,expected,sha=sample()
        report["target_code_windows"].pop()
        with self.assertRaisesRegex(ValueError,"every required"):
            verify_windows(report,expected,sha)
        report,expected,sha=sample()
        report["target_code_windows"][0]["purpose"]="font_helper_two_0x41a8c0"
        with self.assertRaisesRegex(ValueError,"Unexpected/duplicated"):
            verify_windows(report,expected,sha)

    def test_mismatched_full_exe_sha_rejected(self):
        report,expected,sha=sample()
        report["exe_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"Wrong original"):
            verify_windows(report,expected,sha)

    def test_tampered_window_sha_or_section_rejected(self):
        report,expected,sha=sample()
        report["target_code_windows"][0]["bytes_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            verify_windows(report,expected,sha)
        report,expected,sha=sample()
        report["target_code_windows"][0]["section"]=".rdata"
        with self.assertRaisesRegex(ValueError,"executable section"):
            verify_windows(report,expected,sha)

    def test_mutated_x86_call_refused_after_valid_rehash(self):
        report,expected,sha=sample()
        address=0x41A81C
        original=report["target_code_windows"]
        for row in original:
            start=int(row["va"],16)
            if start<=address<start+row["byte_count"]:
                blob=bytearray.fromhex(row["bytes_hex"])
                blob[address-start+1]^=1
                row["bytes_hex"]=blob.hex()
                row["bytes_sha256"]=hashlib.sha256(blob).hexdigest()
                expected[row["purpose"]]=(start,len(blob),row["bytes_sha256"])
        stitched={}
        for row in original:
            start=int(row["va"],16)
            for off,byte in enumerate(bytes.fromhex(row["bytes_hex"])):
                stitched[start+off]=byte
        full=bytes(stitched[a] for a in range(CONTIG_START,CONTIG_END+1))
        with self.assertRaisesRegex(ValueError,"CALL target"):
            verify_windows(report,expected,hashlib.sha256(full).hexdigest())


if __name__=="__main__":
    unittest.main()
