"""Read-only argument evidence from the six-file EOA3 V4 diagnostic ZIP.

Locks every interpretation to exact PE SHA, IAT signature, callsite VA and
surrounding bytes. No executable is loaded, patched, run or redistributed.
The static evidence does NOT prove that a call renders on-screen dialogue.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from analyze_windows_report import analyze_reports, read_zip
from probe_engine_calls import REFERENCE_EXE_SHA256

SIGNATURES = {
    "0x41a79a": {
        "api": "TextOutA",
        "prefix": "6a0268382b4f006a006a008b4df851",
        "iat": "0x4f2018",
        "meaning": {
            "hdc": "DWORD [ebp-0x08]",
            "x": 0, "y": 0, "string": "VA 0x4F2B38 (contents not present in V4)",
            "byte_count": 2,
            "note": "Fixed-length two-byte drawing; not proof that this is the game's dialogue renderer.",
        },
    },
    "0x41a7b9": {
        "api": "TextOutA",
        "prefix": "8b551452e8e73f0b0083c404508b4514506a006a008b4df851",
        "iat": "0x4f2018",
        "meaning": {
            "hdc": "DWORD [ebp-0x08]",
            "x": 0, "y": 0,
            "string": "DWORD [ebp+0x14] (pointer to 8-bit bytes)",
            "byte_count": "EAX returned by local helper called at VA 0x4CE790",
            "note": "Helper computes a length/value, but its body is not in V4; cannot label it strlen yet.",
        },
    },
    "0x41aaab": {
        "api": "CreateFontIndirectA",
        "prefix": "8d4dc051",
        "iat": "0x4f2020",
        "meaning": {
            "logfont_pointer": "address [ebp-0x40]",
            "lfCharSet_byte": 134,
            "lfWeight": 400,
            "lfFaceName_destination": "address [ebp-0x24] (LOGFONTA +28)",
            "note": "Static LOGFONTA layout evidence; not proof of the font applied to each dialogue.",
        },
    },
}
FONT_CHARSET_SEQ = bytes.fromhex("c645d786")
FONT_WEIGHT_SEQ = bytes.fromhex("c745d090010000")


def attest_windows(report):
    expected_count = 3
    matched = []
    results = []
    for addr, check in SIGNATURES.items():
        candidates = [item for item in report.get("candidate_call_sites", [])
                      if item.get("site_va", "").lower() == addr and item.get("api") == check["api"]]
        record = {
            "site_va": addr, "api": check["api"], "verified": False,
            "reason": "missing_or_duplicate_callsite", "decoded_stack_arguments": None,
        }
        if len(candidates) != 1:
            results.append(record)
            continue
        row = candidates[0]
        try:
            snippet = bytes.fromhex(row["code_window_hex"])
            i = row["site_offset_within_window"]
            iat = int(row["iat_va"], 16)
            original_site = int(row["site_va"], 16)
            base = int(row["code_window_start_va"], 16)
            signature = b"\xff\x15" + struct.pack("<I", iat)
            prefix = bytes.fromhex(check["prefix"])
            integrity = (
                hashlib.sha256(snippet).hexdigest() == row["code_window_sha256"]
                and 0 <= i <= len(snippet) - 6
                and base + i == original_site
                and snippet[i:i+6] == signature
                and snippet[i-len(prefix):i] == prefix
                and hex(iat) == check["iat"]
            )
            if addr == "0x41aaab":
                # LF weight and charset use exact EBP-based offsets
                # relative to the start of the LOGFONTA object.
                integrity = integrity and FONT_CHARSET_SEQ in snippet[:i] and FONT_WEIGHT_SEQ in snippet[:i]
            if not integrity:
                record["reason"] = "incomplete_or_changed_machine_code_pattern"
            else:
                record["verified"] = True
                record["reason"] = "exact_bytes_and_hash_match"
                record["decoded_stack_arguments"] = check["meaning"]
                matched.append(addr)
        except (ValueError, KeyError, TypeError, OverflowError):
            record["reason"] = "invalid_record"
        results.append(record)
    return {
        "status": "static_argument_pattern_evidence_only",
        "expected_sites": expected_count, "verified_sites": len(matched),
        "entries": results,
        "limitations": [
            "Matching byte sequences are not proof the game reaches the call at runtime.",
            "Both observed TextOutA callsites use (x=0,y=0); they may draw to an offscreen DC.",
            "No body of the helper at 0x4CE790 and no contents of the constant at 0x4F2B38 are in V4.",
            "No codepage/ANGELSCRIPT-to-buffer relationship is established.",
            "DO NOT replace TextOutA with TextOutW or patch EXE based on these patterns alone.",
        ],
    }


def summarize_zip(path):
    docs = read_zip(path)
    metadata = analyze_reports(docs)
    engine = docs.get("engine_callsite_slices.json")
    if engine is None:
        raise ValueError("This is the older five-file V3 ZIP, not V4")
    if engine.get("exe_sha256") != REFERENCE_EXE_SHA256 or not engine.get("matches_documented_exe_sha256"):
        raise ValueError("Expected the specifically documented AngelSLG.exe SHA-256")
    return {
        "schema_version": 1, "exe_sha256": metadata["game_exe"]["sha256"],
        "analysis": attest_windows(engine),
        "recommendation": "Inspect 0x4CE790 helper body and the two-byte constant at 0x4F2B38 before planning a reversible Unicode proof-of-concept.",
    }


def main():
    parser = argparse.ArgumentParser(description="Validate TextOutA argument patterns in V4 diagnostic ZIP")
    parser.add_argument("report_zip", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    try:
        result = summarize_zip(args.report_zip)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print("Static stack-argument evidence saved:", args.out)
    else:
        print(output)


if __name__ == "__main__":
    main()
