"""Verify V7 font buffer/helper evidence from existing seven-file ZIP, read-only.

All addresses are exclusive to the documented SHA-256. This checks actual
fragment bytes and x86 instruction landmarks; neither executes nor patches
the game and does not identify a live glyph cache or dialogue renderer.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from analyze_windows_report import read_zip, analyze_reports
from probe_engine_calls import REFERENCE_EXE_SHA256

EXPECTED = {
    "font_helper_one_0x41a7f0": (0x41A7F0, 288, "9f29b85bb1e35faf527cee3f21c49e9c66fd44ef28a0cd90e7a17f61022a975a"),
    "font_helper_two_0x41a8c0": (0x41A8C0, 448, "b923f94dbbff30d90a33baa4f213d5e8506e203504d6c816e7365b5545f2495c"),
    "font_initializer_before_calls": (0x41AA00, 192, "c77f4c74d992577de33eac62708e0f33122402c94b8121f986ab039c85aba337"),
    "percent_iterator_context": (0x42AC60, 384, "e9ae3aa27d9d2531fb99d4a6ede2efb4668359e9fd1806c900e7a741a213ea86"),
}
CONTIG_START, CONTIG_END = 0x41A7F0, 0x41AABF
CONTIG_SHA256 = "617d8ff85d59b8178facb4a29c39281ab62a565e2cad8a68d322c72c9ed38ff0"
# Only short x86 landmarks; original binary/function bodies are not checked in.
MARKERS = {
    0x41A7F0:"558bec83ec78", 0x41A815:"6a406a40",
    0x41A824:"0faf450cd1e0", 0x41A836:"894118",
    0x41A84A:"8988d00f0000", 0x41A856:"8982d40f0000",
    0x41A86E:"c20800", 0x41A880:"558bec83ec44",
    0x41A8C0:"558bec83ec7c", 0x41A8F4:"c1f803",
    0x41A935:"69c0d0070000", 0x41A947:"8981c00f0000",
    0x41A96D:"817dc4d0070000", 0x41A97C:"66c7444a200000",
    0x41A9A2:"69c0d0070000", 0x41A9C3:"c3",
    0x41A9D0:"558bec83ec44", 0x41AA10:"558bec81ec80000000",
    0x41AA1F:"837d0c40", 0x41AA42:"ff1510204f00",
    0x41AAAB:"ff1520204f00", 0x42AD3F:"83fa25",
    0x42AD54:"ff15b0214f00", 0x42AD99:"e852280a00",
}
DIRECT_CALLS = {
    0x41A810:0x41A880, 0x41A81C:0x41A600,
    0x41A82B:0x41EF10, 0x41A863:0x41ABF0,
    0x41A89C:0x41EF60, 0x41A8E0:0x41A9D0,
    0x41A93C:0x41EF10, 0x41A9B5:0x4CD930,
    0x41A9F2:0x41EF60,
}
KNOWN_IATS = {
    "0x4f2010":"DeleteObject", "0x4f2014":"GetPixel",
    "0x4f2018":"TextOutA", "0x4f2020":"CreateFontIndirectA",
    "0x4f2028":"SelectObject", "0x4f2158":"lstrcpy",
    "0x4f21b0":"CharNextA",
}


def ensure(condition, explanation):
    if not condition:
        raise ValueError(explanation)


def verify_windows(follow, expected=EXPECTED, contiguous_sha=CONTIG_SHA256):
    ensure(follow.get("status") == "bounded_helper_caller_evidence_not_a_patch",
           "Wrong V7 followup status")
    ensure(follow.get("exe_sha256") == REFERENCE_EXE_SHA256
           and follow.get("matches_documented_exe_sha256") is True,
           "Wrong original game EXE hash")
    windows = follow.get("target_code_windows", [])
    ensure(isinstance(windows, list) and len(windows) == len(expected),
           "V7 did not collect every required helper window")
    mapped, details, seen = {}, {}, set()
    for row in windows:
        purpose = row.get("purpose")
        ensure(purpose in expected and purpose not in seen,
               "Unexpected/duplicated V7 helper record")
        seen.add(purpose)
        va, length, required_digest = expected[purpose]
        try:
            payload = bytes.fromhex(row["bytes_hex"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("Invalid V7 machine-code hex") from exc
        digest = hashlib.sha256(payload).hexdigest()
        ensure(row.get("va","").lower() == hex(va)
               and row.get("byte_count") == length and len(payload) == length,
               "Missing/truncated V7 helper bytes")
        ensure(row.get("section") == ".text"
               and row.get("truncated_to_section_boundary") is False,
               "V7 helper bytes outside executable section")
        ensure(digest == required_digest and row.get("bytes_sha256") == digest,
               "V7 helper bytes SHA-256 mismatch")
        for i, byte in enumerate(payload):
            pos = va + i
            if pos in mapped:
                ensure(mapped[pos] == byte, "Overlapping V7 code windows disagree")
            mapped[pos] = byte
        details[purpose] = {"va":hex(va), "bytes":length, "sha256":digest}
    contiguous = bytes(mapped[va] for va in range(CONTIG_START, CONTIG_END+1)
                       if va in mapped)
    ensure(len(contiguous) == CONTIG_END-CONTIG_START+1
           and hashlib.sha256(contiguous).hexdigest() == contiguous_sha,
           "Unverified 720-byte continuous font subsystem")
    for va, token in MARKERS.items():
        pattern = bytes.fromhex(token)
        ensure(all(mapped.get(va+i) == b for i,b in enumerate(pattern)),
               "Unexpected x86 instruction pattern at " + hex(va))
    for va, target in DIRECT_CALLS.items():
        op = bytes(mapped.get(va+i, -1) for i in range(5))
        ensure(op[0] == 0xE8
               and va+5+struct.unpack_from("<i",op,1)[0] == target,
               "Unexpected x86 CALL target at " + hex(va))
    return details


def inspect_docs(docs):
    game = analyze_reports(docs)["game_exe"]
    follow = docs.get("engine_followup_evidence.json")
    ensure(game["sha256"] == REFERENCE_EXE_SHA256 and follow is not None,
           "Expected verified EXE and V7 followup evidence")
    verified = verify_windows(follow)
    iats = {(item.get("iat_va") or "").lower():item.get("api")
            for item in (follow.get("raw_call_reference_scan") or {}).get("iat_api_names",[])}
    for va, api in KNOWN_IATS.items():
        ensure(iats.get(va) == api, "Unexpected GDI/CRT import at " + va)
    markers = follow.get("angelscript_marker_locations",[])
    ensure(any(item.get("file_offset")==1005272
               and item.get("rva_mapped_va")=="0x4f56d8" for item in markers),
           "Unexpected ANGELSCRIPT marker address")
    return {
        "status":"verified_static_v7_font_buffers_not_playable_patch",
        "exe_sha256":REFERENCE_EXE_SHA256,
        "verified_code_windows":verified,
        "contiguous_font_region":{"start_va":hex(CONTIG_START),
                                  "end_va":hex(CONTIG_END),
                                  "size_bytes":720,
                                  "sha256":CONTIG_SHA256},
        "first_helper":{
            "entry_va":"0x41a7f0","end_ret_va":"0x41a86e",
            "surface_setup":"CALL 0x41A600 with 64 and 64 (purpose not verified)",
            "buffer_size_formula":"2 * width * height",
            "buffer_address_field":"this+0x18",
            "width_field":"this+0xfd0", "height_field":"this+0xfd4",
            "remaining_unverified_helper":"0x41abf0",
        },
        "second_helper":{
            "entry_va":"0x41a8c0","end_ret_va":"0x41a9c3",
            "row_byte_width_formula":"ceil(width/8) for nonnegative widths",
            "allocation_size_formula":"2000 * height * row_byte_width",
            "buffer_address_field":"this+0xfc0",
            "slot_count":2000,"slot_width_bits":16,
            "slot_table":"this+0x20 to this+0xfbe",
            "allocation_zeroing":"memset-like 0x4CD930 call",
            "interpretation":"Memory layout has 2000 entries, not proven to mean 2000 characters.",
        },
        "font_constructor":{
            "entry_va":"0x41aa10", "size_upper_bound":64,
            "old_hfont_dispose":"gdi32.DeleteObject",
            "constructor":"gdi32.CreateFontIndirectA",
            "weight":400,"charset":134,
        },
        "text_iterator":{
            "char_next_api":"user32.CharNextA",
            "percent_byte_test":"0x42ad3f",
            "byte_substring_copy":"0x42ad99 copies a segment followed by NUL terminator",
            "interpretation":"Not proven to be ANGELSCRIPT dialogue/control-code parser.",
        },
        "limits":[
            "The 2000 slots may be a cache; exact meanings/pixel format are not established.",
            "Allocator/free/memset helper names are suggested by calls, not verified from their full bodies.",
            "No live DirectDraw/HFONT/glyph behavior has been observed at runtime.",
            "The ANGELSCRIPT parser-to-TextOutA chain remains unverified.",
            "No EXE, source script, font or translation was modified.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description="Verify static EOA3 font buffer layout in V7 ZIP")
    p.add_argument("report_zip",type=Path)
    p.add_argument("--out",type=Path,default=None)
    args=p.parse_args()
    try:
        report=inspect_docs(read_zip(args.report_zip))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        p.error(str(exc))
    summary=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(summary,encoding="utf-8")
        print("Saved verified V7 code evidence:",args.out)
    else:
        print(summary)


if __name__ == "__main__":
    main()
