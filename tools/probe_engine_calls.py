"""Collect small, bounded x86 code neighborhoods around imported text/encoding APIs.

READ ONLY. No executable is patched, disassembled or executed. The output is
a byte-evidence record for manual disassembly; FF 15 matches are *candidates*.
Do not infer function arguments or call graphs from these windows alone.
Python 3.9+, standard library.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from probe_game import MAX_EXE_SIZE, parse_pe

REFERENCE_EXE_SHA256 = "2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf"
APIS = (
    "TextOutA", "CreateFontIndirectA", "MultiByteToWideChar",
    "WideCharToMultiByte", "GetACP", "GetCPInfo", "CharNextA",
)
BEFORE = 96
AFTER = 48
MAX_MATCHES_PER_API = 32
MAX_WINDOWS = 128
MAX_TARGET_WINDOW_BYTES = 512  # largest documented V6 helper request: 448 bytes


def bounded_va_evidence(data, pe, va, length, executable):
    """Capture only a few bytes at a grounded RVA and inside its PE section."""
    base = pe["imagebase"]
    rva = va - base
    if rva < 0 or length < 1 or length > MAX_TARGET_WINDOW_BYTES:
        return None
    off = pe["_offset_for_rva"](rva)
    section = next((
        sec for sec in pe["sections"]
        if sec["executable"] == executable
        and sec["rva"] <= rva < sec["rva"] + sec["file_size"]
        and sec["file_offset"] + (rva - sec["rva"]) == off
    ), None)
    if off is None or section is None:
        return None
    available = min(length, section["file_size"] - (rva - section["rva"]), len(data) - off)
    if available < 1:
        return None
    raw = data[off:off+available]
    return {
        "va": hex(va), "section": section["name"], "file_offset": off,
        "bytes_hex": raw.hex(), "bytes_sha256": hashlib.sha256(raw).hexdigest(),
        "byte_count": len(raw), "truncated_to_section_boundary": len(raw) < length,
    }


def collect(data, expected_sha256=REFERENCE_EXE_SHA256):
    pe = parse_pe(data)
    sha = hashlib.sha256(data).hexdigest()
    base = pe["imagebase"]
    result = {
        "schema_version": 1,
        "status": "read_only_code_neighborhoods_not_disassembly_or_patch",
        "exe_sha256": sha,
        "matches_documented_exe_sha256": sha == expected_sha256,
        "architecture": pe["architecture"],
        "imagebase": hex(base),
        "window_radius_bytes": {"before": BEFORE, "after": AFTER},
        "candidate_call_sites": [],
        "reference_charset_context": None,
        "dependent_code_targets": [],
        "warnings": list(pe.get("import_parse_warnings", [])),
        "limitations": [
            "FF 15 references in executable sections are candidate x86 IAT CALLs, not complete disassembly.",
            "The reported byte windows can cross guessed function boundaries; do not infer calling conventions from them alone.",
            "No exact return/call graph or complete string-buffer origin is derived here.",
            "The charset context is included only if the executable matches the documented SHA-256.",
            "Small machine-code fragments are included for private analysis; review before sharing publicly.",
            "Additional helper/data excerpts are only extracted when full EXE SHA-256 matches the documented build.",
            "This diagnostic cannot safely patch a game or validate Vietnamese runtime rendering.",
        ],
    }
    if pe["architecture"] != "PE32":
        result["warnings"].append("unsupported_for_raw_x86_ff15_call_search")
        return result
    counts = Counter()
    for imp in pe["imports"]:
        api = imp["api"]
        if api not in APIS:
            continue
        iat_va = imp["iat_va"]
        if iat_va > 0xFFFFFFFF:
            continue
        signature = b"\xff\x15" + struct.pack("<I", iat_va)
        for sec in pe["sections"]:
            if not sec["executable"]:
                continue
            start, size = sec["file_offset"], sec["file_size"]
            if size <= 0 or start < 0 or start >= len(data):
                continue
            block = data[start:min(start + size, len(data))]
            seek = 0
            while True:
                where = block.find(signature, seek)
                if where < 0:
                    break
                seek = where + 1
                if counts[api] >= MAX_MATCHES_PER_API or len(result["candidate_call_sites"]) >= MAX_WINDOWS:
                    if "callsite_safety_budget_reached" not in result["warnings"]:
                        result["warnings"].append("callsite_safety_budget_reached")
                    continue
                left = max(0, where - BEFORE)
                right = min(len(block), where + len(signature) + AFTER)
                window = block[left:right]
                site_va = base + sec["rva"] + where
                result["candidate_call_sites"].append({
                    "api": api, "import_dll": imp["dll"],
                    "iat_va": hex(iat_va), "site_va": hex(site_va),
                    "site_file_offset": start + where,
                    "section": sec["name"], "code_window_start_va": hex(base + sec["rva"] + left),
                    "site_offset_within_window": where - left,
                    "call_bytes_hex": signature.hex(),
                    "code_window_hex": window.hex(),
                    "code_window_sha256": hashlib.sha256(window).hexdigest(),
                })
                counts[api] += 1
    result["candidate_call_sites"].sort(key=lambda r: (int(r["site_va"], 16), r["api"]))
    result["candidate_count_by_api"] = dict(sorted(counts.items()))
    if sha == expected_sha256:
        # These follow directly from two V4 TextOutA argument patterns.
        # The 0x4CE790 callee could compute a length, but V4 did NOT have its
        # body. The 0x4F2B38 pointer was used for a two-byte TextOutA call.
        # Do not label either one as strlen / literal text before inspection.
        dependent = [
            ("length_helper_candidate", 0x4CE790, 192, True),
            ("fixed_two_byte_string_pointer", 0x4F2B38, 16, False),
        ]
        for purpose, va, limit, code in dependent:
            excerpt = bounded_va_evidence(data, pe, va, limit, code)
            if excerpt is None:
                result["warnings"].append("unmapped_dependent_target_" + purpose)
            else:
                excerpt["purpose"] = purpose
                result["dependent_code_targets"].append(excerpt)
        # This instruction was found by the user's original PE scan; only
        # reuse the VA for the exact corresponding SHA-256 build.
        known_va = 0x41AA85
        rva = known_va - base
        target = pe["_offset_for_rva"](rva)
        section = next((
            s for s in pe["sections"]
            if s["executable"] and s["rva"] <= rva < s["rva"] + s["file_size"]
            and s["file_offset"] + (rva - s["rva"]) == target
        ), None)
        if target is not None and section is not None:
            rel = rva - section["rva"]
            left = max(0, rel - 48)
            right = min(section["file_size"], rel + 64)
            window = data[section["file_offset"] + left:section["file_offset"] + right]
            result["reference_charset_context"] = {
                "reference_va": hex(known_va),
                "actual_bytes_at_va": data[target:target + 4].hex(),
                "matches_prior_mov_charset_134_pattern": data[target:target + 4] == b"\xc6\x45\xd7\x86",
                "code_window_start_va": hex(base + section["rva"] + left),
                "reference_offset_within_window": rel - left,
                "code_window_hex": window.hex(),
                "interpretation": "Probable LOGFONT charset assignment (static bytes, no runtime proof)",
            }
        else:
            result["warnings"].append("reference_charset_va_unmapped")
    return result


def main():
    parser = argparse.ArgumentParser(description="Export bounded x86 GDI/import callsite evidence from AngelSLG.exe")
    parser.add_argument("exe", type=Path)
    parser.add_argument("--out", type=Path, default=Path("build/engine_callsite_slices.json"))
    args = parser.parse_args()
    if not args.exe.is_file() or args.exe.name.lower() != "angelslg.exe":
        parser.error("Please select the actual AngelSLG.exe file")
    if args.exe.stat().st_size > MAX_EXE_SIZE:
        parser.error("Executable is too large")
    data = args.exe.read_bytes()
    summary = collect(data)
    if args.out.resolve().is_relative_to(args.exe.parent.resolve()):
        parser.error("Do not write report inside the game folder")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Saved targeted code slices:", args.out)
    print("Reference EXE matched:", summary["matches_documented_exe_sha256"])
    print("Candidate callsites:", len(summary["candidate_call_sites"]))
    print("No game files were changed. Byte windows are not a disassembly.")


if __name__ == "__main__":
    main()
