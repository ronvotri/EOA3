"""Synthetic-only V8 static audit tests; no game EXE or raw V8 samples."""
import hashlib
import struct
import unittest
from audit_v8_renderer_trace import (
    EXE_SHA, WINDOWS, LANDMARKS, CALLS, TRIPLES, PALETTE_SHA,
    samples, verify_x86, overlaps, palette
)

def fake_windows():
    out={base:bytearray(n) for base,(n,_) in WINDOWS.items()}
    def write(va,data):
        for base,b in out.items():
            if base<=va and va+len(data)<=base+len(b):
                b[va-base:va-base+len(data)]=data
                return
        raise AssertionError("uncovered synthetic site "+hex(va))
    for va,hx in LANDMARKS.items():
        write(va,bytes.fromhex(hx))
    for site,target in CALLS.items():
        write(site,b"\xe8"+struct.pack("<i",target-site-5))
    return {va:bytes(x) for va,x in out.items()}

def fake_report(raw):
    return {"exe_sha256":EXE_SHA,"matches_documented_exe_sha256":True,
      "warnings":[], "samples":[
      {"va":hex(base),"bytes_hex":data.hex(),"byte_count":len(data),
       "bytes_sha256":hashlib.sha256(data).hexdigest(),
       "section":".text","truncated_to_section_boundary":False}
      for base,data in raw.items()]}

class RealV8AuditSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.raw=fake_windows()

    def test_known_sites_and_synthetic_layout(self):
        verify_x86(self.raw)
        self.assertEqual(len(WINDOWS),7)
        self.assertEqual(len(CALLS),16)
        self.assertEqual(samples(fake_report(self.raw),verify_historical=False),self.raw)
        with self.assertRaisesRegex(ValueError,"Wrong known V8 window"):
            samples(fake_report(self.raw))

    def test_wrong_exe_and_truncated_window_rejected(self):
        r=fake_report(self.raw)
        r["exe_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"Unknown EXE SHA"):
            samples(r,verify_historical=False)
        r=fake_report(self.raw)
        r["samples"][0]["bytes_hex"]=r["samples"][0]["bytes_hex"][:-2]
        with self.assertRaisesRegex(ValueError,"Truncated"):
            samples(r,verify_historical=False)

    def test_wrong_instruction_and_direct_call_rejected(self):
        d={a:bytearray(b) for a,b in self.raw.items()}
        d[0x41C790][0x41C7E4-0x41C790]^=1
        with self.assertRaisesRegex(ValueError,"Bad instruction"):
            verify_x86(d)
        d={a:bytearray(b) for a,b in self.raw.items()}
        d[0x42AED0][0x42AEE6-0x42AED0]^=1
        with self.assertRaisesRegex(ValueError,"Wrong relative call"):
            verify_x86(d)

    def test_v7_overlap_matches_both_regions(self):
        old={
          0x41A7F0:self.raw[0x41A600][-16:]+bytes(272),
          0x42AC60:self.raw[0x42AAF0][-144:]+bytes(240)}
        self.assertEqual(overlaps(self.raw,old),2)
        damaged=bytearray(old[0x42AC60]);damaged[2]^=1
        old[0x42AC60]=bytes(damaged)
        with self.assertRaisesRegex(ValueError,"overlap mismatch"):
            overlaps(self.raw,old)

    def test_palette_matches_16_three_byte_triples(self):
        raw=bytes(k for row in TRIPLES for k in row)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),PALETTE_SHA)
        p={"va":"0x522f44","section":".data","byte_count":48,
          "bytes_hex":raw.hex(),"bytes_sha256":PALETTE_SHA,
          "truncated_to_section_boundary":False}
        self.assertEqual(palette(p),TRIPLES)
        p["bytes_hex"]="ff"+raw.hex()[2:]
        with self.assertRaisesRegex(ValueError,"palette SHA"):
            palette(p)

if __name__=="__main__":
    unittest.main()
