"""Read-only, exact-SHA audit of EOA3 ANSI substring-to-helper handoff.

Uses the previously received *seven-file* V7 Windows diagnostic ZIP. All
external bytes are authenticated by existing audit_v7_font_buffers verifier.
The parser, purpose of 0x41C790, and runtime dialogue path are NOT proven.

This script never accesses, executes, changes or redistributes game EXEs.
"""
import argparse
import json
import struct
from pathlib import Path

from analyze_windows_report import analyze_reports, read_zip
from audit_v7_font_buffers import verify_windows, EXPECTED, ensure
from probe_engine_calls import REFERENCE_EXE_SHA256

START = 0x42AC60
END = START + 384
ITERATOR_PURPOSE = "percent_iterator_context"

# Selected instruction groups from the SHA-locked V7 window. Do not store
# whole copyrighted code sections in the repository.
LANDMARKS = {
    0x42AD2F: "8b55c80fbe0285c07442",              # NUL termination test
    0x42AD3F: "83fa25750c",                          # ASCII percent branch
    0x42AD44: "8b45ec25ff00000085c0742b",          # conditional branch on local flag
    0x42AD50: "8b4dc851ff15b0214f008945c8",        # CharNextA and pointer update
    0x42AD5D: "8b55fc837a1c007413",                # optional character budget flag
    0x42AD66: "8b45cc83c0018945cc8b4dcc3b4df47c02eb02", # increment and compare
    0x42AD79: "ebb4",                                # back to 0x42AD2F
    0x42AD7B: "8b55c83b55f00f8691000000",          # no copied segment if not advanced
    0x42AD87: "8b45c82b45f0508b4df0518d95c8efffff52", # len=end-start; dest
    0x42ADA1: "8b45c82b45f0c68405c8efffff00",      # destination[len] = NUL
    0x42ADAF: "8b4dfc668b5128",                     # 16-bit property from object
    0x42ADB7: "8b45fc668b4830",                     # another 16-bit property
    0x42ADBF: "8d95c8efffff528b450c508b4d08518b15f886550052",
    0x42ADD5: "8b4dfc83c13c",                       # receiver = this+0x3C
}
CALLS = {
    0x42AD99: 0x4CD5F0,  # memcpy-like routine, not proven as system memcpy
    0x42ADDB: 0x41C790,  # consumer of NUL-terminated temporary string
}
IAT_CALLS = {
    0x42AD54: 0x4F21B0, # user32!CharNextA
}


def inspect_iterator(raw, start=START):
    """Statically verify byte-pattern/control-flow landmarks and E8 targets."""
    ensure(isinstance(raw, bytes) and len(raw) == END - START
           and start == START, "Unexpected V7 iterator window dimensions")
    for va, hexbytes in LANDMARKS.items():
        expected = bytes.fromhex(hexbytes)
        i = va - start
        ensure(raw[i:i+len(expected)] == expected,
               "Changed x86 iterator instructions at " + hex(va))
    for va, dest in CALLS.items():
        i = va - start
        opcode = raw[i:i+5]
        ensure(len(opcode) == 5 and opcode[0] == 0xE8
               and va+5+struct.unpack_from("<i", opcode, 1)[0] == dest,
               "Unexpected direct CALL target " + hex(va))
    for va, iat in IAT_CALLS.items():
        i = va - start
        ensure(raw[i:i+6] == b"\xff\x15"+struct.pack("<I",iat),
               "Unexpected imported CharNextA call")
    return {
        "status": "verified_static_ansi_substring_to_consumer_not_runtime_or_patch",
        "source_segment": {
            "pointer_start": "[ebp-0x10]",
            "pointer_current": "[ebp-0x38]",
            "end_conditions": ["NUL byte", "'%' byte when low flag is zero",
                               "optional character-count budget"],
            "char_step": "user32!CharNextA via IAT 0x4F21B0",
            "optional_character_limit": {
                "condition": "nonzero DWORD [object+0x1c]",
                "count": "one increment per CharNextA step (not per byte)",
                "limit": "signed compare against [ebp-0x0c]",
                "object_identity": "owner of this iterator, NOT established to be font object",
            },
        },
        "temporary_copy": {
            "call_va": "0x42ad99",
            "target_va": "0x4cd5f0",
            "source": "[ebp-0x10]",
            "destination": "[ebp-0x1038]",
            "byte_count": "current_pointer - start_pointer",
            "terminator": "explicit NUL stored at destination[byte_count]",
            "callee_role": "memcpy-like by argument layout; callee body not verified",
        },
        "next_consumer": {
            "call_va": "0x42addb", "target_va": "0x41c790",
            "receiver": "this+0x3c",
            "text_argument": "pointer to NUL-terminated temporary [ebp-0x1038]",
            "other_args": ["global pointer [0x5586f8]", "[ebp+8]", "[ebp+0xc]",
                           "two 16-bit values from this+0x30 and this+0x28"],
            "status": "direct x86 CALL verified; callee body not in V7",
        },
        "cautions": [
            "No complete ANGELSCRIPT loader-to-input pointer path is present in this V7 snippet.",
            "There is no verified link from 0x41C790 to 0x41A7B9/TextOutA yet.",
            "No explicit byte capacity check for the temporary destination is visible in this slice; upstream length bounds are unknown. Do not claim a confirmed overflow.",
            "A UTF-8 rewrite may change byte counts and CharNextA stepping; do not inject UTF-8 raw.",
            "The iterator object field +0x1C cannot be identified as the font row-width field +0x1C merely from equal offsets.",
        ],
    }


def inspect_docs(docs):
    meta = analyze_reports(docs)
    ensure(meta["game_exe"]["sha256"] == REFERENCE_EXE_SHA256,
           "Report is not for documented EOA3 EXE")
    follow = docs.get("engine_followup_evidence.json")
    ensure(follow is not None, "V7 seven-file report is required")
    # The existing verifier authenticates all four hashes and 720-byte
    # font-region overlap before we interpret this individual window.
    verify_windows(follow)
    rows = [r for r in follow["target_code_windows"]
            if r.get("purpose") == ITERATOR_PURPOSE]
    ensure(len(rows)==1 and rows[0].get("va","").lower() == hex(START),
           "Missing exact CharNextA iterator slice")
    raw = bytes.fromhex(rows[0]["bytes_hex"])
    result=inspect_iterator(raw)
    result["exe_sha256"] = REFERENCE_EXE_SHA256
    result["iterator_window_sha256"] = EXPECTED[ITERATOR_PURPOSE][2]
    result["next_research_target"] = "0x41C790 (text-consumer callee) before attempting a Unicode bridge"
    return result


def main():
    parser=argparse.ArgumentParser(description="Verify V7 ANSI substring handoff from existing report ZIP")
    parser.add_argument("report_zip",type=Path)
    parser.add_argument("--out",type=Path,default=None)
    args=parser.parse_args()
    try:
        result=inspect_docs(read_zip(args.report_zip))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    output=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(output,encoding="utf-8")
        print("Saved V7 ANSI handoff evidence:",args.out)
    else:
        print(output)


if __name__=="__main__":
    main()
