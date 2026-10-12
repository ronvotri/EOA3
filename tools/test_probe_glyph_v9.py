"""Synthetic V9 tests; never use an actual game executable."""
import hashlib
import struct
import unittest

from probe_glyph_v9 import TARGETS, CODE_BUDGET, collect, validate_report


def fake_pe():
    data=bytearray(0x51000)
    data[:2]=b'MZ'
    struct.pack_into('<I',data,0x3c,0x80)
    data[0x80:0x84]=b'PE\0\0'
    struct.pack_into('<HHIIIHH',data,0x84,0x14c,1,0,0,0,0xe0,0x102)
    opt=0x98
    struct.pack_into('<H',data,opt,0x10b)
    struct.pack_into('<I',data,opt+28,0x400000)
    struct.pack_into('<I',data,opt+60,0x1000)
    struct.pack_into('<I',data,opt+92,0)
    struct.pack_into('<8sIIIIIIHHI',data,0x178,b'.text\0\0\0',0x50000,0x1000,0x50000,0x1000,0,0,0,0,0x60000020)
    data[0x1000:]=b'\x90'*0x50000
    return bytes(data)


class V9GlyphProbeTests(unittest.TestCase):
    def test_exact_target_set_and_budget(self):
        self.assertEqual(len(TARGETS),13)
        self.assertEqual(CODE_BUDGET,6528)
        self.assertEqual(TARGETS[1][1],0x41C5B0)
        self.assertEqual(TARGETS[6][1],0x42AA00)

    def test_wrong_exe_never_reads_historical_vas(self):
        data=fake_pe()
        report=collect(data)
        self.assertFalse(report['matches_documented_exe_sha256'])
        self.assertEqual(report['samples'],[])
        self.assertIn('unknown_exe_sha_no_historical_va_reads',report['warnings'])
        self.assertFalse(validate_report(report))

    def test_realistic_fake_pe_collects_only_expected_slices(self):
        data=fake_pe();sha=hashlib.sha256(data).hexdigest()
        report=collect(data,expected_sha=sha)
        self.assertTrue(report['matches_documented_exe_sha256'])
        self.assertEqual(len(report['samples']),13)
        self.assertEqual(sum(s['byte_count'] for s in report['samples']),CODE_BUDGET)
        self.assertTrue(all(s['section']=='.text' and not s['truncated_to_section_boundary'] for s in report['samples']))
        self.assertFalse(validate_report(report))
        tampered=dict(report)
        tampered['samples']=[dict(x) for x in report['samples']]
        tampered['samples'][0]['bytes_hex']='ff'+tampered['samples'][0]['bytes_hex'][2:]
        self.assertFalse(validate_report(tampered,expected_sha=sha))
        self.assertTrue(validate_report(report,expected_sha=sha))

    def test_truncated_section_and_bad_coverage_fail_closed(self):
        data=fake_pe();sha=hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(ValueError,'Missing/truncated'):
            collect(data,expected_sha=sha,targets=TARGETS[:-1]+(('unmapped',0x4fe000,512),))
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            collect(data,expected_sha=sha,targets=TARGETS[:-1]+(('duplicate',TARGETS[0][1],512),))
        with self.assertRaisesRegex(ValueError,'budget'):
            collect(data,expected_sha=sha,targets=TARGETS[:-1]+(('too_long',0x4fe000,513),))

if __name__=='__main__':
    unittest.main()
