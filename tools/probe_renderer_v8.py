"""Bounded V8 code/data collection to bridge ANSI text and GDI/DirectDraw.

This is a targeted, read-only, offline Windows diagnostic extension. VA probes
are enabled ONLY for the documented AngelSLG.exe SHA. Raw code snapshots are
not disassembly and are not full functions: they can straddle boundaries.
Nothing is executed or modified; no EXE, font or full local path is output.
"""
import hashlib
import json
from pathlib import Path

from probe_engine_calls import (
    REFERENCE_EXE_SHA256, MAX_TARGET_WINDOW_BYTES, bounded_va_evidence,
)
from probe_game import MAX_EXE_SIZE, parse_pe
from probe_text_callers import collect as collect_candidates

# Covers high-priority consumer, its continuation, the downstream font helpers,
# the numeric-property parser and a pre-dispatcher region overlapping V7.
CODE_TARGETS = (
    ("ansi_segment_consumer_0x41c790", 0x41C790, 512),
    ("ansi_segment_consumer_cont_0x41c990", 0x41C990, 512),
    ("font_mask_and_property_helpers_0x41abf0", 0x41ABF0, 512),
    ("surface_setup_and_gdi_0x41a600", 0x41A600, 512),
    ("numeric_command_parser_0x42a8a0", 0x42A8A0, 448),
    ("color_triple_combiner_0x42aed0", 0x42AED0, 320),
    ("command_dispatcher_before_v7_0x42aaf0", 0x42AAF0, 512),
)
PALETTE_TARGET = ("raw_triple_reference_table_0x522f44", 0x522F44, 48)
MAX_CODE_BYTES = sum(row[2] for row in CODE_TARGETS)
# We deliberately cap the xref categories and never claim a decoded callgraph.
CANDIDATE_RANGES = (
    ("ansi_text_consumer", 0x41C790, 0x41CB90),
    ("font_mask_and_color_setters", 0x41ABF0, 0x41ADF0),
    ("surface_gdi", 0x41A600, 0x41A800),
    ("numeric_parser", 0x42A8A0, 0x42AA60),
    ("triple_combiner", 0x42AED0, 0x42B010),
)


def _fragment(data, pe, purpose, va, count, executable):
    if not 1 <= count <= MAX_TARGET_WINDOW_BYTES:
        raise ValueError("V8 sample exceeds per-section cap: " + purpose)
    got = bounded_va_evidence(data, pe, va, count, executable)
    if got is None or got.get("byte_count") != count or got.get("truncated_to_section_boundary"):
        raise ValueError("V8 known EXE missing or truncating required fragment: " + purpose)
    got["purpose"] = purpose
    return got


def collect(data, expected_sha=REFERENCE_EXE_SHA256,
            targets=CODE_TARGETS, palette_target=PALETTE_TARGET,
            candidate_ranges=CANDIDATE_RANGES):
    digest = hashlib.sha256(data).hexdigest()
    result = {
        "schema_version": 1,
        "status": "read_only_v8_renderer_trace_code_fragments_not_disassembly_or_patch",
        "exe_sha256": digest,
        "matches_documented_exe_sha256": digest == expected_sha,
        "samples": [],
        "palette_reference_bytes": None,
        "candidate_calls": None,
        "warnings": [],
        "limitations": [
            "Raw x86 fragments can straddle function boundaries and do not prove dynamic data flow.",
            "E8 rel32 byte-pattern call candidates may be misaligned false positives.",
            "Byte triples at 0x522F44 are not proved RGB until a decoded color helper confirms it.",
            "The 0x41C790 consumer body is sampled but not automatically identified as dialogue rendering.",
            "No EXE or font files or personally identifying local paths are included.",
            "No game file is read except the explicitly selected EXE; the game is never launched or modified.",
        ],
    }
    if digest != expected_sha:
        result["warnings"].append("unknown_exe_sha_no_legacy_va_reads")
        return result
    if len(data) > MAX_EXE_SIZE:
        raise ValueError("Executable too large")
    pe = parse_pe(data)
    if pe["architecture"] != "PE32" or pe["imagebase"] != 0x400000:
        raise ValueError("Incorrect PE format/imagebase for known EOA3 build")
    if (sum(n for _, _, n in targets) > MAX_CODE_BYTES
            or len(targets) > len(CODE_TARGETS)):
        raise ValueError("V8 target byte budget exceeded")
    if len({name for name, _, _ in targets}) != len(targets):
        raise ValueError("Duplicate V8 code target name")
    for purpose, va, length in targets:
        result["samples"].append(_fragment(data, pe, purpose, va, length, True))
    result["palette_reference_bytes"] = _fragment(
        data, pe, palette_target[0], palette_target[1], palette_target[2], False
    )
    calls = collect_candidates(data, expected_sha=expected_sha,
                               target_ranges=candidate_ranges, iat_addresses=())
    result["candidate_calls"] = {
        "status": calls.get("status"),
        "candidate_count_by_region": calls.get("candidate_count_by_region", {}),
        "call_candidates": calls.get("call_candidates", []),
        "limitations": calls.get("limitations", []),
    }
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="V8 read-only EOA3 ANSI/glyph/renderer trace")
    parser.add_argument("exe", type=Path, help="Original AngelSLG.exe")
    parser.add_argument("--out", type=Path, default=Path("build/v8-renderer-trace.json"))
    args = parser.parse_args()
    exe = args.exe
    if not exe.is_file() or exe.name.lower() != "angelslg.exe":
        parser.error("Choose the original AngelSLG.exe")
    if exe.stat().st_size > MAX_EXE_SIZE:
        parser.error("Executable exceeds read-only analysis limit")
    if args.out.resolve().is_relative_to(exe.parent.resolve()):
        parser.error("Output cannot be inside game installation")
    try:
        result = collect(exe.read_bytes())
    except (ValueError, OSError, TypeError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n",encoding="utf-8")
    print("Saved V8 static renderer evidence:", args.out)
    print("Full EXE SHA matched:", result["matches_documented_exe_sha256"])


if __name__ == "__main__":
    main()
