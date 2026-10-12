"""Synthetic regression tests for V9 control-table decoding and digest guards."""
import hashlib
import struct
import unittest
from audit_v9_glyph_real import (
    EXE_SHA, WINDOWS, CASE_EXPECTED, CHECK_BYTES, DIRECT_CALLS,
    decode_commands, verify_overlaps, windows_from_report,
)

def fake_dispatch():
    # Invented buffers: only the jump table and the little-endian case-index
    # structure match the observed V9 layout; these are NOT game snapshots.
    a=bytearray(512)
    b=bytearray(512)
    a[0x09:0x11]=bytes.fromhex(CHECK_BYTES[0x42AA09])
    a[0x11:0x18]=bytes.fromhex(CHECK_BYTES[0x42AA11])
    targets=(0x42aa18,0x42ab6b,0x42ac6e,0x42aa81,0x42aa2a,
             0x42aa49,0x42aadd,0x42abe7,0x42aaa5,0x42aac1,
             0x42ab1e,0x42aa1c)
    struct.pack_into("<12I",b,0x3d,*targets)
    b[0x6d:0x6d+86]=bytes([11])*86
    mapping={"%":0,"c":1,"C":1,"k":2,"K":2,"N":3,"n":3,
             "s":5,"S":5,"t":6,"T":6,"w":7,"W":7,"z":10,"Z":10}
    for ch,index in mapping.items():
        b[0x6d+ord(ch)-0x25]=index
    return {0x42AA00:bytes(a),0x42AE00:bytes(b)}

def fake_report():
    rows=[]
    for va,(size,_) in WINDOWS.items():
        raw=bytes(size)
        rows.append({"va":hex(va),"section":".text",
                     "byte_count":size,"truncated_to_section_boundary":False,
                     "bytes_hex":raw.hex(),"bytes_sha256":hashlib.sha256(raw).hexdigest()})
    return {"status":"read_only_v9_glyph_trace_not_disassembly_or_patch",
            "exe_sha256":EXE_SHA,"matches_documented_exe_sha256":True,
            "warnings":[],"samples":rows}

class V9RealAuditTests(unittest.TestCase):
    def test_table_dispatch_matches_all_known_controls(self):
        cmd=decode_commands(fake_dispatch())
        for ch,target in CASE_EXPECTED.items():
            self.assertEqual(cmd[ch],target)

    def test_invalid_jump_case_index_rejected(self):
        d=fake_dispatch()
        b=bytearray(d[0x42AE00])
        b[0x6d+ord("c")-0x25]=0xff
        d[0x42AE00]=bytes(b)
        with self.assertRaisesRegex(ValueError,"case index"):
            decode_commands(d)

    def test_corrupted_dispatch_instruction_rejected(self):
        d=fake_dispatch()
        b=bytearray(d[0x42AA00])
        b[0x11]=0x90
        d[0x42AA00]=bytes(b)
        with self.assertRaisesRegex(ValueError,"jump table signature"):
            decode_commands(d)

    def test_sample_guards_reject_corrupted_sha_and_missing_data(self):
        r=fake_report()
        found=windows_from_report(r,strict=False)
        self.assertEqual(len(found),13)
        with self.assertRaisesRegex(ValueError,"user V9 evidence"):
            windows_from_report(r)
        r["samples"][0]["bytes_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"Corrupted SHA"):
            windows_from_report(r,strict=False)
        r=fake_report()
        r["samples"].pop()
        with self.assertRaisesRegex(ValueError,"exactly 13"):
            windows_from_report(r,strict=False)

    def test_overlap_guards(self):
        a={0x1000:b"ABCDE",0x1003:b"DEFG"}
        self.assertEqual(verify_overlaps(a),2)
        a[0x1003]=b"XEFG"
        with self.assertRaisesRegex(ValueError,"Conflicting"):
            verify_overlaps(a)

if __name__=="__main__":
    unittest.main()
