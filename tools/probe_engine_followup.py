"""One-time, bounded follow-up evidence for two EOA3 font/surface helpers.

The previous V5 windows end exactly before the function at 0x41A7F0; they do
NOT contain either helper body. This module samples limited code around the
two known addresses on the exact documented EXE SHA, maps IAT import names
and reports possible E8 rel32 caller references. It NEVER patches or launches
the game, nor packages whole EXE or game assets.

All conclusions remain static: E8 byte scanning may match instruction operands.
Python 3.9+, standard library; 1 file in the existing ZIP.
"""
import hashlib
import json
from pathlib import Path

from probe_engine_calls import (REFERENCE_EXE_SHA256, bounded_va_evidence,
                                MAX_TARGET_WINDOW_BYTES)
from probe_game import parse_pe, MAX_EXE_SIZE
from probe_text_callers import collect as probe_caller_candidates

# Explicitly limited snippets. Overlap lets a later disassembler verify
# instruction boundaries without pretending any of these are proven ends.
TARGETS = (
    ("font_helper_one_0x41a7f0", 0x41A7F0, 288),
    ("font_helper_two_0x41a8c0", 0x41A8C0, 448),
    ("font_initializer_before_calls", 0x41AA00, 192),
    ("percent_iterator_context", 0x42AC60, 384),
)
TARGET_MAGIC = b"ANGELSCRIPT"
MAX_MAGIC_HITS = 8
MAX_RAW_XREFS = 32


def _file_offset_to_va(pe, file_offset):
    for sec in pe["sections"]:
        start = sec["file_offset"]
        if start <= file_offset < start + sec["file_size"]:
            return pe["imagebase"] + sec["rva"] + (file_offset - start)
    return None


def find_magic_references(data, pe):
    """Report string-marker offsets and raw VA-immediate references only."""
    markers = []
    next_at = 0
    while len(markers) < MAX_MAGIC_HITS:
        offset = data.find(TARGET_MAGIC, next_at)
        if offset < 0:
            break
        next_at = offset + len(TARGET_MAGIC)
        va = _file_offset_to_va(pe, offset)
        references = []
        if va is not None and va <= 0xFFFFFFFF:
            needle = va.to_bytes(4, "little")
            for sec in pe["sections"]:
                if not sec["executable"]:
                    continue
                raw = data[sec["file_offset"]:sec["file_offset"]+sec["file_size"]]
                cursor = 0
                while len(references) < MAX_RAW_XREFS:
                    position = raw.find(needle, cursor)
                    if position < 0:
                        break
                    cursor = position + 1
                    references.append(hex(pe["imagebase"]+sec["rva"]+position))
                if len(references) >= MAX_RAW_XREFS:
                    break
        markers.append({
            "file_offset": offset,
            "rva_mapped_va": hex(va) if va is not None else None,
            "raw_little_endian_va_occurrences_in_executable_sections": references,
            "interpretation": "VA literal-byte references only; not decoded instructions or confirmed loader references",
        })
    return markers


def collect_followup(data, expected_sha=REFERENCE_EXE_SHA256, targets=TARGETS):
    sha = hashlib.sha256(data).hexdigest()
    result = {
        "schema_version": 1,
        "status": "bounded_helper_caller_evidence_not_a_patch",
        "exe_sha256": sha,
        "matches_documented_exe_sha256": sha == expected_sha,
        "target_code_windows": [],
        "raw_call_reference_scan": None,
        "angelscript_marker_locations": [],
        "warnings": [],
        "limitations": [
            "Historical VA windows are collected only if whole EXE SHA-256 matches the verified build.",
            "Byte excerpts are bounded and may cross function boundaries; proper x86 disassembly is still required.",
            "Raw E8 rel32 CALLs and literal VA hits are candidates and may be false positives.",
            "ANGELSCRIPT magic absence in EXE does not prove the parser is absent (it may live in a DLL).",
            "No proof that the sampled font helpers are used by dialogue or tooltip rendering.",
            "No executable or game assets are included or modified. This report is not a Vietnamese font patch.",
        ],
    }
    if sha != expected_sha:
        result["warnings"].append("wrong_executable_sha_no_historical_va_reads")
        return result
    if len(data) > MAX_EXE_SIZE:
        raise ValueError("Executable exceeds analysis size limit")
    pe = parse_pe(data)
    if pe["architecture"] != "PE32" or pe["imagebase"] != 0x400000:
        raise ValueError("Expected documented EOA3 PE32/x86 ImageBase 0x400000")

    for name, va, limit in targets:
        if limit > MAX_TARGET_WINDOW_BYTES or limit < 1:
            raise ValueError("Target size exceeds bounded section reader cap: " + name)
        fragment = bounded_va_evidence(data, pe, va, limit, True)
        if fragment is None or fragment["byte_count"] != limit:
            result["warnings"].append("unmapped_or_truncated_code_target_" + name)
            continue
        fragment["purpose"] = name
        result["target_code_windows"].append(fragment)
    if sha == REFERENCE_EXE_SHA256 and len(result["target_code_windows"]) != len(targets):
        raise ValueError("Known EOA3 EXE must yield all requested font/helper windows; refusing incomplete report")
    xrefs = probe_caller_candidates(data, expected_sha=expected_sha)
    result["raw_call_reference_scan"] = {
        "status": xrefs["status"],
        "iat_api_names": xrefs.get("iat_api_names", []),
        "candidate_count_by_region": xrefs.get("candidate_count_by_region", {}),
        "call_candidates": xrefs.get("call_candidates", []),
        "warnings": xrefs.get("warnings", []),
    }
    result["angelscript_marker_locations"] = find_magic_references(data, pe)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Small EOA3 font-helper and text caller evidence (read-only)")
    parser.add_argument("exe", type=Path)
    parser.add_argument("--out", type=Path, default=Path("build/engine_followup_evidence.json"))
    args = parser.parse_args()
    if not args.exe.is_file() or args.exe.name.lower() != "angelslg.exe":
        parser.error("Choose the actual AngelSLG.exe")
    if args.exe.stat().st_size > MAX_EXE_SIZE:
        parser.error("Selected file exceeds the 8 MB safety limit")
    if args.out.resolve().is_relative_to(args.exe.parent.resolve()):
        parser.error("Cannot write output into game folder")
    try:
        result = collect_followup(args.exe.read_bytes())
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("Read-only engine follow-up:", args.out)
    print("Correct EXE SHA:", result["matches_documented_exe_sha256"])
    print("Code windows:", len(result["target_code_windows"]))


if __name__ == "__main__":
    main()
