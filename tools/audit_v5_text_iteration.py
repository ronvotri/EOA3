"""Audit ANSI character iteration and neighboring TextOutA windows from V4/V5 ZIP.

No EXE needed: verifies original report metadata, exact callsite bytes, SHA-256
of each bounded code window, and byte-for-byte consistency where windows
overlap. This is STATIC evidence only; it never claims CharNextA is the
ANGELSCRIPT control-code parser.
"""
import argparse
import hashlib
import json
from pathlib import Path

from analyze_windows_report import analyze_reports, read_zip
from probe_engine_calls import REFERENCE_EXE_SHA256

CHAR_NEXT_VA = 0x42AD54
TEXTOUT_VAS = (0x41A79A, 0x41A7B9)

# Exact byte landmarks adjacent to the observed x86 loop (not disassembly).
CHAR_LOOP_STEPS = {
    0x42AD2F: bytes.fromhex("8b55c80fbe0285c07442"),
    0x42AD3F: bytes.fromhex("83fa25750c8b45ec25ff00000085c0742b"),
    0x42AD50: bytes.fromhex("8b4dc851"),
    0x42AD54: bytes.fromhex("ff15b0214f00"),
    0x42AD5A: bytes.fromhex("8945c8"),
    0x42AD79: bytes.fromhex("ebb4"),
}
TEXT_SEQUENCE = {
    0x41A79A: bytes.fromhex("ff1518204f00"),
    0x41A7B9: bytes.fromhex("ff1518204f00"),
    0x41A7E9: bytes.fromhex("c21400"),
}


def validated_window(item):
    if not isinstance(item, dict):
        raise ValueError("Code window must be an object")
    start = int(item["code_window_start_va"], 16)
    site = int(item["site_va"], 16)
    relative = item["site_offset_within_window"]
    raw = bytes.fromhex(item["code_window_hex"])
    if (
        site != start + relative
        or relative < 0
        or relative + 6 > len(raw)
        or len(raw) > 150
        or hashlib.sha256(raw).hexdigest() != item["code_window_sha256"]
        or raw[relative:relative+6] != bytes.fromhex(item["call_bytes_hex"])
    ):
        raise ValueError("Code window has invalid offsets/digest/signature at " + hex(site))
    return start, raw


def stitch_evidence(items):
    """Merge bounded, independently hashed pieces; refuse overlap disagreement."""
    index = {}
    for item in items:
        start, raw = validated_window(item)
        for offset, value in enumerate(raw):
            va = start + offset
            if va in index and index[va] != value:
                raise ValueError("Conflicting overlapping byte-window evidence at " + hex(va))
            index[va] = value
    return index


def exactly_at(memory, va, expected):
    return all(memory.get(va+i) == value for i, value in enumerate(expected))


def audit_engine_evidence(engine, expected_sha=REFERENCE_EXE_SHA256):
    if engine.get("status") != "read_only_code_neighborhoods_not_disassembly_or_patch":
        raise ValueError("Not a code window diagnostic")
    if engine.get("exe_sha256") != expected_sha or not engine.get("matches_documented_exe_sha256"):
        raise ValueError("Not the verified AngelSLG.exe build")
    sites = engine.get("candidate_call_sites", [])
    interesting = [
        row for row in sites
        if row.get("api") in ("TextOutA", "CharNextA")
    ]
    addresses = [(row.get("api"), int(row.get("site_va", "0"), 16)) for row in interesting]
    for api, addr in (("TextOutA", TEXTOUT_VAS[0]), ("TextOutA", TEXTOUT_VAS[1]),
                      ("CharNextA", CHAR_NEXT_VA)):
        if addresses.count((api, addr)) != 1:
            raise ValueError("Missing or duplicated required callsite: "+api+" "+hex(addr))

    view = stitch_evidence(interesting)
    char_next = next(r for r in interesting if r["api"] == "CharNextA")
    if int(char_next["iat_va"], 16) != 0x4F21B0:
        raise ValueError("Unexpected CharNextA IAT pointer")
    has_loop_landmarks = all(exactly_at(view, addr, signature)
                             for addr, signature in CHAR_LOOP_STEPS.items())
    has_text_sequence = all(exactly_at(view, addr, signature)
                            for addr, signature in TEXT_SEQUENCE.items())
    if not has_loop_landmarks or not has_text_sequence:
        raise ValueError("Observed x86 text-loop bytes differ from documented build")
    if not all(int(item["iat_va"], 16) == 0x4F2018
               for item in interesting if item["api"] == "TextOutA"):
        raise ValueError("TextOutA IAT differs from documented build")

    # This is a code-path observation, not proof that all strings flow here.
    return {
        "schema_version": 1,
        "status": "verified_static_ansi_iteration_evidence_not_a_patch",
        "exe_sha256": expected_sha,
        "text_out": {
            "call_vas": [hex(va) for va in TEXTOUT_VAS],
            "iat_va": "0x4f2018",
            "both_calls_in_contiguous_code_windows": True,
            "next_observed_return": "0x41a7e9",
            "return_instruction": "ret 0x14",
            "note": "Shared continuous code and a subsequent RET, but no caller-to-ANGELSCRIPT proof.",
        },
        "char_iteration": {
            "call_va": hex(CHAR_NEXT_VA), "iat_va": "0x4f21b0",
            "byte_test_va": "0x42ad3f",
            "byte_test": "cmp byte 0x25 (ASCII percent sign) followed by conditional branch",
            "pointer_step": "CharNextA(pointer), stores returned pointer",
            "loop_back_branch_va": "0x42ad79",
            "interpretation": "ANSI/multibyte-aware traversal is present in a separate observed routine",
            "unverified": "Whether this is processing ANGELSCRIPT controls %N/%s/%t/%z",
        },
        "encoding_risk": [
            "CharNextA operates on ANSI codepage bytes, not UTF-8 codepoints.",
            "A translated data record must not be forced into cp936 using replacement of Vietnamese accents.",
            "Raw UTF-8 injection into the original ANSI processing path is not proven safe.",
            "Changing TextOutA to TextOutW alone would misinterpret LPCSTR and byte length.",
        ],
    }


def audit_zip(path):
    docs = read_zip(path)
    metadata = analyze_reports(docs)
    if metadata["game_exe"]["sha256"] != REFERENCE_EXE_SHA256:
        raise ValueError("Unknown executable hash")
    engine = docs.get("engine_callsite_slices.json")
    if engine is None:
        raise ValueError("V4/V5 diagnostic ZIP (six files) is required")
    return audit_engine_evidence(engine)


def main():
    parser = argparse.ArgumentParser(
        description="Verify CharNextA percent handling and nearby TextOutA bytes from EOA3 V5 ZIP"
    )
    parser.add_argument("report_zip", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    try:
        report = audit_zip(args.report_zip)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print("Saved read-only ANSI text evidence:", args.out)
    else:
        print(payload)


if __name__ == "__main__":
    main()
