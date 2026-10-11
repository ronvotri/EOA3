"""Static V7 palette-branch evidence + independent EOA3 source control-code audit.

This inspects an *already provided* seven-file V7 diagnostic ZIP and original
source/*.json. Every raw instruction comes from the verified V7 window and
EXE SHA. The branch's trigger codepoint (%c or otherwise) is NOT observed:
V7's snippet begins after the dispatcher; cross-corpus code frequencies are
contextual evidence, not a mapping of the source %c token to this branch.

READ ONLY. No executable, scripts, font files or game assets are changed.
"""
import argparse
from collections import Counter, defaultdict
import json
import re
import struct
from pathlib import Path

from analyze_windows_report import read_zip, analyze_reports
from audit_v7_font_buffers import verify_windows, EXPECTED, ensure
from probe_engine_calls import REFERENCE_EXE_SHA256

BASE = 0x42AC60
LENGTH = 384
PURPOSE = "percent_iterator_context"

# Independent, exact x86 landmarks from the SHA-locked original V7 window.
PALETTE_LANDMARKS = {
    0x42AC6E: "8d4df0518b55f083c202528d45e850",
    0x42AC85: "25ff00000085c07463",
    0x42AC8E: "837de800744d",
    0x42AC94: "8b4de881e10f00008079054983c9f0416bc903",
    0x42ACAA: "8b55d00fbe82462f520050",
    0x42ACB5: "8b4dd00fbe91452f520052",
    0x42ACC0: "8b45d00fbe88442f520051",
    0x42ACD3: "508b4dfc83c13c",
    0x42ACE1: "68feff0000",
    0x42ACF1: "8b55fc837a18007428",
    0x42AD18: "8b45fcc7401c01000000",
    0x42AD2F: "8b55c80fbe0285c0",
}
RELATIVE_CALLS = {
    0x42AC7D: 0x42A8A0, # parser/converter candidate
    0x42ACCB: 0x42AED0, # combines 3 values, exact role unverified
    0x42ACDA: 0x41AC20, # receives constructed value
    0x42ACEC: 0x41AC20, # receives 0xFFFE fallback
    0x42ACFC: 0x4288B0,
    0x42AD0B: 0x428A90,
}

CONTROL = re.compile(r"%([A-Za-z])([+-]?\d+)?")


def validate_palette_instructions(raw):
    """Classify only the instructions actually observed, not the dispatcher."""
    ensure(isinstance(raw, bytes) and len(raw) == LENGTH,
           "V7 palette window must be 384 bytes")
    for va, hex_bytes in PALETTE_LANDMARKS.items():
        token = bytes.fromhex(hex_bytes)
        offset = va - BASE
        ensure(raw[offset:offset+len(token)] == token,
               "Unexpected V7 palette x86 instruction at " + hex(va))
    for site, expected_target in RELATIVE_CALLS.items():
        offset = site - BASE
        encoded = raw[offset:offset+5]
        ensure(len(encoded) == 5 and encoded[:1] == b"\xe8"
               and site + 5 + struct.unpack_from("<i", encoded, 1)[0] == expected_target,
               "Unexpected V7 branch CALL destination " + hex(site))
    return {
        "status": "verified_static_palette_index_branch_not_token_mapping",
        "numeric_parse_call": {
            "site_va": "0x42ac7d",
            "target_va": "0x42a8a0",
            "text_pointer_offset_bytes": 2,
            "observed": "A pointer two bytes after current string position is passed to a parser-like helper.",
        },
        "palette_lookup": {
            "parsed_integer_location": "[ebp-0x18]",
            "index_operation": "signed remainder modulo 16, multiplied by 3",
            "triple_byte_addresses": ["0x522f44", "0x522f45", "0x522f46"],
            "triple_count_inferred_from_index": 16,
            "byte_load_type": "signed-byte MOVSX; palette data bytes not sampled",
        },
        "value_application": {
            "three_value_helper": "direct CALL 0x42aed0 at 0x42accb",
            "recipient": "object+0x3c, direct CALL 0x41ac20",
            "fallback_constant": "0x0000fffe",
            "branch_predicate": "helper 0x42a8a0 returns nonzero low byte; parsed integer equals zero takes fallback",
        },
        "continuation": {
            "calls": ["0x4288b0", "0x428a90"],
            "conditional_flag_write": "owner object+0x1c = 1 at 0x42ad1b",
            "follows_into": "CharNextA-driven ANSI substring loop at 0x42ad2f",
        },
        "limits": [
            "The branch's originating '%' command letter is not present in this V7 window.",
            "The triple-value helper at 0x42AED0 and application callee 0x41AC20 have not been disassembled; RGB/color is a strong hypothesis, not a proven visual output.",
            "Matching source %c frequency is circumstantial and cannot prove the branch implements %c.",
            "The palette's actual bytes/16 entries are not contained in the V7 report.",
            "No ANGELSCRIPT-to-this-routine call graph is established.",
        ],
    }


def summarize_source_controls(source_dir, expected_files=40):
    """Count the literal commands in the original script corpus without edits."""
    source_dir = Path(source_dir)
    paths = sorted(source_dir.glob("*.json"))
    ensure(len(paths) == expected_files,
           "Original EOA3 source corpus count mismatch")
    kinds = Counter()
    numeric = defaultdict(Counter)
    token5 = 0
    for path in paths:
        obj = json.loads(path.read_text(encoding="utf-8"))
        for token in obj["tokens"]:
            if not (isinstance(token, list) and len(token) == 2):
                continue
            kind, data = token
            if kind != 5 or not isinstance(data, str):
                continue
            token5 += 1
            for match in CONTROL.finditer(data):
                letter, value = match.groups()
                kinds["%"+letter] += 1
                if value is not None:
                    numeric["%"+letter][int(value)] += 1
    return {
        "source_json_files": len(paths), "text_tokens": token5,
        "control_occurrences": dict(sorted(kinds.items())),
        "numeric_values": {
            key: {str(n): count for n, count in sorted(values.items())}
            for key, values in sorted(numeric.items())
        },
        "basis": "only original source/*.json strings, not edited Vietnamese translations",
    }


def inspect_docs(docs, source_dir, expected_files=40):
    meta = analyze_reports(docs)
    ensure(meta["game_exe"]["sha256"] == REFERENCE_EXE_SHA256,
           "Unrecognized EOA3 executable SHA")
    follow = docs.get("engine_followup_evidence.json")
    ensure(follow is not None, "Required V7 font/iterator evidence missing")
    verify_windows(follow)
    rows = [r for r in follow["target_code_windows"]
            if r.get("purpose") == PURPOSE]
    ensure(len(rows) == 1 and rows[0].get("va","").lower() == hex(BASE)
           and rows[0].get("byte_count") == LENGTH,
           "Expected one exact V7 palette context window")
    summary = validate_palette_instructions(bytes.fromhex(rows[0]["bytes_hex"]))
    summary["exe_sha256"] = REFERENCE_EXE_SHA256
    summary["source_corpus"] = summarize_source_controls(source_dir, expected_files)
    summary["relationship_to_source"] = (
        "There are %c control codes in source scripts and a 16-entry "
        "palette-indexing branch in machine code; the branch's triggering "
        "letter remains unknown from V7."
    )
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Audit the V7 numeric palette branch and source control codes without changing game files"
    )
    parser.add_argument("report_zip", type=Path)
    parser.add_argument("--source-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "source")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        summary = inspect_docs(read_zip(args.report_zip), args.source_dir)
    except (OSError, TypeError, KeyError, ValueError) as exc:
        parser.error(str(exc))
    output = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print("Saved verified palette/control evidence:", args.out)
    else:
        print(output)


if __name__ == "__main__":
    main()
