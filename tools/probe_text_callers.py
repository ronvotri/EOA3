"""Read-only x86 relative-CALL xrefs and exact IAT names near EOA3 text routines.

This is an investigation helper, not an automatic call graph/disassembler.
Opcode E8 bytes inside other instructions can yield false positives, so every
result is a *candidate* awaiting proper instruction-boundary disassembly.
No executable, game resources, or original user paths are written to reports.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from probe_game import MAX_EXE_SIZE, parse_pe
from probe_engine_calls import REFERENCE_EXE_SHA256

# Ranges are exploratory based on already captured x86 windows.
# They are NOT function entry boundaries and do not establish caller identity.
TARGET_RANGES = (
    ("draw_text_region", 0x41A600, 0x41A7EA),
    ("font_setup_region", 0x41AA00, 0x41AADB),
    ("percent_char_iterator_region", 0x42AC00, 0x42AE18),
    ("known_byte_strlen_function", 0x4CE790, 0x4CE80B),
)
KNOWN_IATS = (
    0x4F2018, 0x4F201C, 0x4F2020, 0x4F2024,
    0x4F2028, 0x4F202C, 0x4F21B0,
)
MAX_PER_REGION = 64
MAX_RESULTS = 160


def collect(data, expected_sha=REFERENCE_EXE_SHA256):
    sha = hashlib.sha256(data).hexdigest()
    if sha != expected_sha:
        return {
            "status": "unrecognized_executable_no_legacy_address_probe",
            "exe_sha256": sha,
            "matches_documented_exe_sha256": False,
            "call_candidates": [], "iat_api_names": [],
            "warnings": ["historical_code_vas_not_used_for_unrecognized_build"],
        }
    pe = parse_pe(data)
    if pe["architecture"] != "PE32" or pe["imagebase"] != 0x400000:
        raise ValueError("Expected PE32 with imagebase 0x400000 for known build")

    iats = {i["iat_va"]: {"iat_va": hex(i["iat_va"]), "dll": i["dll"], "api": i["api"]}
            for i in pe["imports"] if i["iat_va"] in KNOWN_IATS}
    mapped_iats = [iats.get(va, {"iat_va": hex(va), "status": "not_import_mapped"})
                   for va in KNOWN_IATS]
    candidates = []
    counts = Counter()
    for sec in pe["sections"]:
        if not sec["executable"]:
            continue
        base, size = sec["file_offset"], sec["file_size"]
        if size < 5 or base < 0 or base >= len(data):
            continue
        raw = data[base:min(base+size, len(data))]
        for off in range(len(raw)-4):
            if raw[off] != 0xE8:
                continue
            rel = struct.unpack_from("<i", raw, off + 1)[0]
            site_va = pe["imagebase"] + sec["rva"] + off
            target = site_va + 5 + rel
            matching = [(label, low, high) for label, low, high in TARGET_RANGES
                        if low <= target < high]
            if not matching:
                continue
            label = matching[0][0]
            if counts[label] >= MAX_PER_REGION or len(candidates) >= MAX_RESULTS:
                continue
            before = raw[max(0, off-12):off]
            after = raw[off+5:min(len(raw), off+13)]
            candidates.append({
                "candidate_call_va": hex(site_va), "candidate_target_va": hex(target),
                "target_region": label, "section": sec["name"],
                "call_bytes_hex": raw[off:off+5].hex(),
                "before_bytes_hex": before.hex(),
                "after_bytes_hex": after.hex(),
                "site_file_offset": base+off,
            })
            counts[label] += 1
    candidates.sort(key=lambda x: int(x["candidate_call_va"], 16))
    return {
        "schema_version": 1,
        "status": "bounded_raw_rel32_call_candidate_scan_not_disassembly",
        "exe_sha256": sha, "matches_documented_exe_sha256": True,
        "iat_api_names": mapped_iats,
        "call_candidates": candidates,
        "candidate_count_by_region": dict(sorted(counts.items())),
        "warnings": list(pe.get("import_parse_warnings", [])),
        "limitations": [
            "E8 rel32 byte-pattern hits are not instruction-boundary validated; false positives are possible.",
            "Ranges contain candidate regions, NOT verified function entries.",
            "No call graph or ANGELSCRIPT-to-TextOutA relationship is proven.",
            "The result includes only tiny machine-code context fragments, not a game binary.",
            "No game executable was modified, loaded, or run.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only candidate x86 CALL xrefs around EOA3 text paths")
    parser.add_argument("exe", type=Path, help="The original AngelSLG.exe")
    parser.add_argument("--out", type=Path, default=Path("build/text_callers_candidates.json"))
    args = parser.parse_args()
    if not args.exe.is_file() or args.exe.name.lower() != "angelslg.exe":
        parser.error("Expected the actual AngelSLG.exe")
    if args.exe.stat().st_size > MAX_EXE_SIZE:
        parser.error("EXE exceeds probe size limit")
    if args.out.resolve().is_relative_to(args.exe.parent.resolve()):
        parser.error("Do not write report inside the game directory")
    try:
        result = collect(args.exe.read_bytes())
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("Saved bounded candidate call references:", args.out)
    print("Matches documented executable:", result["matches_documented_exe_sha256"])
    print("Raw CALL candidates:", len(result["call_candidates"]))


if __name__ == "__main__":
    main()
