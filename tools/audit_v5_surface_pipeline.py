"""Identify the DirectDraw-compatible GDI surface path from existing V5 ZIP.

Static machine-code evidence only: compare individually hashed x86 windows,
vtable argument conventions and local rel32 calls. No game EXE, font, game
assets, or runtime execution is required. A surface vtable signature is NOT
proof of live DirectDraw object identity without a runtime inspection.
"""
import argparse
import json
import struct
from pathlib import Path

from analyze_windows_report import analyze_reports, read_zip
from audit_v5_text_iteration import stitch_evidence, exactly_at
from probe_engine_calls import REFERENCE_EXE_SHA256

TEXTOUT_SITES = (0x41A79A, 0x41A7B9)
FONT_SITE = 0x41AAAB

# Exact, short x86 instruction sequences from V5; no executable region.
SURFACE_LANDMARKS = {
    0x41A73A: bytes.fromhex("8d45f850"),               # LEA HDC out; push it
    0x41A744: bytes.fromhex("8b45fc8b48048b0152ff5044"), # vtable +0x44
    0x41A750: bytes.fromhex("85c07579"),               # HRESULT == 0 success path
    0x41A79A: bytes.fromhex("ff1518204f00"),           # TextOutA
    0x41A7B9: bytes.fromhex("ff1518204f00"),           # TextOutA
    0x41A7D1: bytes.fromhex("8b55fc8b42048b4dfc8b51048b0a50ff5168"), # +0x68
    0x41A7E9: bytes.fromhex("c21400"),                 # RET 0x14
}
FONT_LANDMARKS = {
    0x41AA72: bytes.fromhex("c745d090010000"),         # LOGFONTA lfWeight = 400
    0x41AA85: bytes.fromhex("c645d786"),               # LOGFONTA lfCharSet=134
    0x41AA99: bytes.fromhex("8b5508528d45dc50"),     # lfFaceName destination
    0x41AAAB: bytes.fromhex("ff1520204f00"),           # CreateFontIndirectA IAT
    0x41AAB1: bytes.fromhex("8b55fc8982cc0f0000"),   # this->+0xfcc = HFONT
    0x41AAC5: bytes.fromhex("e826fdffff"),             # rel32: 0x41a7f0
    0x41AACD: bytes.fromhex("e8eefdffff"),             # rel32: 0x41a8c0
    0x41AAD8: bytes.fromhex("c20800"),                 # RET 0x08
}


def rel32_destination(view, call_va):
    opcode = bytes(view.get(call_va+i, -1) for i in range(5))
    if len(opcode) != 5 or opcode[0] != 0xE8:
        raise ValueError("Missing direct x86 rel32 CALL at " + hex(call_va))
    return call_va + 5 + struct.unpack_from("<i", opcode, 1)[0]


def audit_engine(engine, expected_sha=REFERENCE_EXE_SHA256):
    if (engine.get("status") != "read_only_code_neighborhoods_not_disassembly_or_patch"
            or engine.get("exe_sha256") != expected_sha
            or not engine.get("matches_documented_exe_sha256")):
        raise ValueError("V5 evidence does not match documented AngelSLG.exe")
    records = engine.get("candidate_call_sites", [])
    subset = []
    for api, va in [("TextOutA", *TEXTOUT_SITES[:1]),
                    ("TextOutA", *TEXTOUT_SITES[1:]),
                    ("CreateFontIndirectA", FONT_SITE)]:
        hits = [r for r in records if r.get("api") == api
                and r.get("site_va", "").lower() == hex(va)]
        if len(hits) != 1:
            raise ValueError("Missing or duplicate GDI callsite: " + hex(va))
        if int(hits[0]["iat_va"], 16) != (0x4F2018 if api == "TextOutA" else 0x4F2020):
            raise ValueError("Unexpected IAT slot for " + api)
        subset.append(hits[0])
    view = stitch_evidence(subset)
    if not all(exactly_at(view, va, signature) for va, signature in SURFACE_LANDMARKS.items()):
        raise ValueError("DirectDraw-compatible GetDC/ReleaseDC code signature differs")
    if not all(exactly_at(view, va, signature) for va, signature in FONT_LANDMARKS.items()):
        raise ValueError("Font creation/store/helper-call signature differs")
    calls = {
        hex(va): hex(rel32_destination(view, va))
        for va in (0x41AAC5, 0x41AACD)
    }
    if calls != {"0x41aac5": "0x41a7f0", "0x41aacd": "0x41a8c0"}:
        raise ValueError("Unexpected font setup subroutine targets")
    return {
        "schema_version": 1,
        "status": "verified_static_gdi_surface_compatibility_not_runtime_or_patch",
        "exe_sha256": expected_sha,
        "surface_candidate": {
            "surface_ptr": "DWORD [DWORD [ebp-4] + 4]",
            "vtable_getdc_compatible": {
                "call_va": "0x41a74d", "vtable_offset": "0x44",
                "argument": "out HDC at [ebp-8]", "hresult_checked_zero": True,
            },
            "gdi_operations": ["TextOutA 0x41a79a", "TextOutA 0x41a7b9"],
            "vtable_releasedc_compatible": {
                "call_va": "0x41a7e0", "vtable_offset": "0x68",
                "argument": "HDC value from [ebp-8]",
            },
            "matching_interface": "IDirectDrawSurface GetDC / ReleaseDC vtable layout",
            "confidence": "strong x86 static ABI match; object type and active surface not runtime-verified",
        },
        "font_initialization": {
            "font_api": "CreateFontIndirectA at 0x41aaab",
            "logfonta_charset": 134, "logfonta_weight": 400,
            "saved_hfont": "this+0xFCC",
            "following_direct_calls": calls,
            "interpretation": "two helper routines are invoked after storing the newly created HFONT",
            "unknowns": [
                "Whether routines 0x41A7F0 and 0x41A8C0 construct a glyph atlas",
                "Where ANGELSCRIPT text is converted into renderable bytes",
                "Which DirectDraw surface is used and how its pixels reach the screen",
            ],
        },
        "next_investigation": [
            "Inspect caller and implementations of 0x41A7F0 and 0x41A8C0.",
            "Confirm this->+0xFCC is an HFONT used by the text drawing surface.",
            "Locate the original ANGELSCRIPT string buffer and control-code parser.",
            "Never replace TextOutA with TextOutW without encoding and length conversion.",
        ],
    }


def audit_zip(path):
    docs = read_zip(path)
    summary = analyze_reports(docs)
    if summary["game_exe"]["sha256"] != REFERENCE_EXE_SHA256:
        raise ValueError("Unknown AngelSLG.exe variant")
    engine = docs.get("engine_callsite_slices.json")
    if engine is None:
        raise ValueError("Need existing V4 or V5 six-file diagnostic ZIP")
    return audit_engine(engine)


def main():
    parser = argparse.ArgumentParser(description="Audit existing EOA3 V5 GDI/DirectDraw-compatible code")
    parser.add_argument("report_zip", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    try:
        result = audit_zip(args.report_zip)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
        print("Wrote static surface/font evidence:", args.out)
    else:
        print(encoded)


if __name__ == "__main__":
    main()
