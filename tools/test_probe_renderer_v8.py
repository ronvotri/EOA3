"""Synthetic EOA3 PE32 with fabricated .rdata, no game assets or EXE bytes."""
import hashlib
import struct
import unittest

from test_probe_game import fake_pe32
from probe_renderer_v8 import (
    CODE_TARGETS, PALETTE_TARGET, MAX_CODE_BYTES, collect,
)


def artificial_two_section_pe():
    data=bytearray(fake_pe32())
    # Construct a second valid, non-executable section in spare PE header space.
    struct.pack_into("<H",data,0x86,2)
    struct.pack_into("<8sIIIIIIHHI",data,0x1A0,
                     b".rdata\0\0", 0x200, 0x2000, 0x200, 0x700,
                     0,0,0,0,0x40000040)
    return bytes(data)


def sample_targets():
    # All seven V8 request lengths can fit within the synthetic 0x500-byte
    # .text, even though the actual VAs are intentionally not used in tests.
    return tuple((name, 0x401000+i*0x18, n) for i,(name,_,n) in enumerate(CODE_TARGETS))


class V8RendererProbeTests(unittest.TestCase):
    def test_code_budget_grounded_in_exact_seven_requests(self):
        self.assertEqual(len(CODE_TARGETS),7)
        self.assertEqual([n for _,_,n in CODE_TARGETS],
                         [512,512,512,512,448,320,512])
        self.assertEqual(MAX_CODE_BYTES,3328)
        self.assertEqual(PALETTE_TARGET[1:],(0x522F44,48))
        self.assertEqual(CODE_TARGETS[0][1],0x41C790)

    def test_known_sha_collects_seven_code_and_palette_windows(self):
        data=artificial_two_section_pe()
        before=hashlib.sha256(data).hexdigest()
        report=collect(
            data,expected_sha=before,
            targets=sample_targets(),
            palette_target=("synthetic_palette",0x402000,48),
            candidate_ranges=(),
        )
        self.assertTrue(report["matches_documented_exe_sha256"])
        self.assertEqual(len(report["samples"]),7)
        self.assertEqual([s["byte_count"] for s in report["samples"]],
                         [t[2] for t in sample_targets()])
        self.assertEqual(report["palette_reference_bytes"]["section"],".rdata")
        self.assertEqual(report["palette_reference_bytes"]["byte_count"],48)
        self.assertFalse(report["warnings"])
        self.assertEqual(hashlib.sha256(data).hexdigest(),before)
        self.assertTrue(all(hashlib.sha256(bytes.fromhex(s["bytes_hex"])).hexdigest()
                            == s["bytes_sha256"] for s in report["samples"]))

    def test_wrong_sha_never_attempts_historical_vas(self):
        data=artificial_two_section_pe()
        report=collect(data)
        self.assertFalse(report["matches_documented_exe_sha256"])
        self.assertEqual(report["samples"],[])
        self.assertIsNone(report["palette_reference_bytes"])
        self.assertIsNone(report["candidate_calls"])
        self.assertIn("unknown_exe_sha_no_legacy_va_reads",report["warnings"])

    def test_required_missing_window_fails_instead_of_success(self):
        data=artificial_two_section_pe()
        sha=hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(ValueError,"missing or truncating"):
            collect(data,expected_sha=sha,
                    targets=(("outside_section",0x403000,512),),
                    palette_target=("synthetic_palette",0x402000,48),
                    candidate_ranges=())
        with self.assertRaisesRegex(ValueError,"missing or truncating"):
            collect(data,expected_sha=sha,
                    targets=(("one",0x401001,512),),
                    palette_target=("synthetic_palette",0x402000,48),
                    candidate_ranges=()) if False else collect(
                        data,expected_sha=sha,
                        targets=(("one",0x401401,512),),
                        palette_target=("synthetic_palette",0x402000,48),
                        candidate_ranges=())

    def test_rejects_budget_overrun_and_duplicate_targets(self):
        data=artificial_two_section_pe()
        sha=hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(ValueError,"budget"):
            collect(data,expected_sha=sha,
                    targets=CODE_TARGETS+(("extra",0x401000,1),),
                    palette_target=("synthetic_palette",0x402000,48),
                    candidate_ranges=())
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            collect(data,expected_sha=sha,
                    targets=(("same",0x401000,64),("same",0x401020,64)),
                    palette_target=("synthetic_palette",0x402000,48),
                    candidate_ranges=())

    def test_no_code_sample_exceeds_512_or_nonexec_data_mapped_as_executable(self):
        data=artificial_two_section_pe()
        sha=hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(ValueError,"per-section cap"):
            collect(data,expected_sha=sha,
                    targets=(("too_long",0x401000,513),),
                    palette_target=("synthetic_palette",0x402000,48),
                    candidate_ranges=())
        with self.assertRaisesRegex(ValueError,"missing or truncating"):
            collect(data,expected_sha=sha,
                    targets=(("rdata_not_executable",0x402000,48),),
                    palette_target=("synthetic_palette",0x402000,48),
                    candidate_ranges=())


if __name__=="__main__":
    unittest.main()
