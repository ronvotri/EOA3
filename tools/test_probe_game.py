"""Synthetic PE fixtures: tests never use or distribute copyrighted game files."""
import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from probe_game import analyze_bytes, parse_pe, file_inventory


def fake_pe32(with_imports=True):
    out = bytearray(0x900)
    out[:2] = b"MZ"
    struct.pack_into("<I", out, 0x3C, 0x80)
    out[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", out, 0x84, 0x14C, 1, 0, 0, 0, 0xE0, 0x102)
    opt = 0x98
    struct.pack_into("<H", out, opt, 0x10B)
    struct.pack_into("<I", out, opt+16, 0x1000)
    struct.pack_into("<I", out, opt+28, 0x400000)
    struct.pack_into("<I", out, opt+60, 0x200)
    struct.pack_into("<I", out, opt+92, 16)
    struct.pack_into("<8sIIIIIIHHI", out, opt+0xE0, b".text\0\0\0",
                     0x500, 0x1000, 0x500, 0x200, 0, 0, 0, 0, 0x60000020)
    if with_imports:
        struct.pack_into("<II", out, opt+104, 0x1100, 0x80)
        struct.pack_into("<IIIII", out, 0x300, 0x1140, 0, 0, 0x1180, 0x1160)
        struct.pack_into("<I", out, 0x340, 0x11A0)
        struct.pack_into("<I", out, 0x360, 0x11A0)
        out[0x380:0x38A] = b"GDI32.dll\0"
        struct.pack_into("<H", out, 0x3A0, 0)
        out[0x3A2:0x3AB] = b"TextOutA\0"
        out[0x210:0x216] = b"\xFF\x15" + struct.pack("<I", 0x401160)
    font = "宋体".encode("cp936")
    out[0x470:0x470+len(font)] = font
    return bytes(out)


def fake_pe64():
    out = bytearray(0x800)
    out[:2] = b"MZ"
    struct.pack_into("<I", out, 0x3C, 0x80)
    out[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", out, 0x84, 0x8664, 1, 0, 0, 0, 0xF0, 0x2022)
    opt = 0x98
    struct.pack_into("<H", out, opt, 0x20B)
    struct.pack_into("<I", out, opt+16, 0x1000)
    struct.pack_into("<Q", out, opt+24, 0x140000000)
    struct.pack_into("<I", out, opt+60, 0x200)
    struct.pack_into("<I", out, opt+108, 0)
    struct.pack_into("<8sIIIIIIHHI", out, opt+0xF0, b".text\0\0\0",
                     0x300, 0x1000, 0x300, 0x200, 0, 0, 0, 0, 0x60000020)
    return bytes(out)


class Eoa3ProbeTests(unittest.TestCase):
    def test_pe32_imports_calls_and_font_names(self):
        sample = fake_pe32()
        before = hashlib.sha256(sample).hexdigest()
        report = analyze_bytes(sample)
        self.assertEqual(report["architecture"], "PE32")
        self.assertEqual(report["imagebase"], "0x400000")
        self.assertEqual(report["sha256"], before)
        self.assertEqual(report["status"], "static_diagnostic_only_not_a_patch")
        self.assertEqual(report["gdi_and_encoding_imports"][0]["api"], "TextOutA")
        self.assertEqual(report["gdi_and_encoding_imports"][0]["iat_va"], 0x401160)
        self.assertIn("0x401010", report["potential_x86_iat_calls"][0]["candidate_call_vas"])
        self.assertIn(0x470, report["font_name_byte_offsets"]["Songti_GBK"])
        self.assertEqual(report["historical_va_hints"]["charset_134_historical"]
                         ["status"], "unverified_historical_hint_only")

    def test_import_directory_size_excludes_null_descriptor(self):
        # This reproduces the user's "Import descriptor limit exceeded":
        # Size=20 documents one DLL, while the final zero descriptor follows.
        sample = bytearray(fake_pe32())
        struct.pack_into("<I", sample, 0x98 + 108, 20)
        before = hashlib.sha256(sample).hexdigest()
        report = analyze_bytes(bytes(sample))
        self.assertEqual(report["sha256"], before)
        self.assertEqual(report["gdi_and_encoding_imports"][0]["api"], "TextOutA")
        info = report["import_table_diagnostics"]
        self.assertTrue(info["null_terminated"])
        self.assertEqual(info["descriptors_read"], 1)
        self.assertIn("import_directory_size_does_not_include_null_terminator",
                      info["warnings"])

    def test_missing_import_terminator_reports_warning_not_game_failure(self):
        sample = bytearray(fake_pe32())
        # The next descriptor is damaged; retain valid first DLL and report
        # partial import coverage instead of losing the whole analysis.
        struct.pack_into("<IIIII", sample, 0x314,
                         0xFFFFFFFF, 1, 2, 0xFFFFFFFF, 0xFFFFFFFF)
        report = analyze_bytes(bytes(sample))
        self.assertIn("TextOutA",
                      [x["api"] for x in report["gdi_and_encoding_imports"]])
        info = report["import_table_diagnostics"]
        self.assertFalse(info["null_terminated"])
        self.assertIn("import_descriptor_invalid_dll_name", info["warnings"])
        self.assertEqual(report["status"], "static_diagnostic_only_not_a_patch")

    def test_empty_import_directory_does_not_invent_drawing_apis(self):
        sample = bytearray(fake_pe32())
        struct.pack_into("<II", sample, 0x98 + 104, 0, 0)
        report = analyze_bytes(bytes(sample))
        self.assertFalse(report["import_table_diagnostics"]["present"])
        self.assertEqual(report["gdi_and_encoding_imports"], [])

    def test_pe64_without_imports(self):
        report = analyze_bytes(fake_pe64())
        self.assertEqual(report["architecture"], "PE32+")
        self.assertEqual(report["imagebase"], "0x140000000")
        self.assertEqual(report["gdi_and_encoding_imports"], [])
        self.assertEqual(report["potential_x86_iat_calls"], [])

    def test_malformed_input_rejected(self):
        for sample in (b"", b"\0" * 4096, b"MZ" + b"\0" * 10):
            with self.assertRaises(ValueError):
                parse_pe(sample)
        damaged = bytearray(fake_pe32())
        damaged[0x80:0x84] = b"FAIL"
        with self.assertRaises(ValueError):
            parse_pe(bytes(damaged))

    def test_read_only_game_inventory(self):
        with tempfile.TemporaryDirectory() as path:
            root = Path(path)
            (root / "Data").mkdir()
            for filename in ("stage1.bin", "stage2.bin", "DataBase.bin"):
                (root / "Data" / filename).write_bytes(b"test original")
            (root / "all_sys.tsw").write_bytes(b"index")
            (root / "all_sys.act").write_bytes(b"archive")
            before = {
                str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob("*") if p.is_file()
            }
            report = analyze_bytes(fake_pe32(), root)
            self.assertEqual(report["installation"]["data_bin_count"], 3)
            self.assertTrue(report["installation"]["known_ui_names"]["all_sys.tsw"])
            after = {
                str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob("*") if p.is_file()
            }
            self.assertEqual(before, after)

    def test_file_inventory_not_found(self):
        with tempfile.TemporaryDirectory() as p:
            self.assertEqual(file_inventory(Path(p) / "not-installed"), {"present": False})


if __name__ == "__main__":
    unittest.main()
