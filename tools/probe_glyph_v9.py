"""EOA3 V9 — one bounded, read-only glyph lookup and command dispatcher probe.

Runs only against exact SHA of user's AngelSLG.exe. Does not execute, inject,
patch, or copy the binary; emits narrowly scoped machine-code excerpts only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from probe_game import parse_pe, MAX_EXE_SIZE
from probe_engine_calls import bounded_va_evidence

EXE_SHA256 = "2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf"
# V8 established exact calls to these glyph and style helpers. Read all at once.
TARGETS = (
    ("glyph_bitmap_and_cache_0x41c470", 0x41C470, 512),
    ("glyph_lookup_0x41c5b0", 0x41C5B0, 512),
    ("glyph_fallback_0x41c650", 0x41C650, 512),
    ("consumer_tail_0x41cb90", 0x41CB90, 512),
    ("glyph_painter_0x41ccc0", 0x41CCC0, 512),
    ("three_channel_packer_0x414380", 0x414380, 384),
    ("command_dispatcher_gap_0x42aa00", 0x42AA00, 512),
    ("command_switch_region_0x42ae00", 0x42AE00, 512),
    ("glyph_style_bit1_0x41ac80", 0x41AC80, 512),
    ("glyph_style_bit2_0x41b270", 0x41B270, 512),
    ("glyph_style_bit4_0x41b5e0", 0x41B5E0, 512),
    ("glyph_style_bit8_0x41b960", 0x41B960, 512),
    ("glyph_style_bit16_0x41be40", 0x41BE40, 512),
)
CODE_BUDGET = sum(n for _,_,n in TARGETS)
FILE_NAMES = ("manifest.json", "glyph_trace_v9.json")


def collect(data, expected_sha=EXE_SHA256, targets=TARGETS):
    actual_sha = hashlib.sha256(data).hexdigest()
    result = {
        "schema_version": 1,
        "status": "read_only_v9_glyph_trace_not_disassembly_or_patch",
        "exe_sha256": actual_sha,
        "matches_documented_exe_sha256": actual_sha == expected_sha,
        "samples": [], "warnings": [],
        "limitations": [
            "Static x86 snippets are not a complete callgraph or runtime Unicode proof.",
            "Some sample fragments overlap and may straddle function boundaries.",
            "Does not include game executable, any font, asset or local path.",
            "No modified game files and no playable Vietnamese patch are produced.",
        ],
    }
    if actual_sha != expected_sha:
        result["warnings"].append("unknown_exe_sha_no_historical_va_reads")
        return result
    if len(data) > MAX_EXE_SIZE:
        raise ValueError("File size exceeds safety limit")
    pe = parse_pe(data)
    if pe["architecture"] != "PE32" or pe["imagebase"] != 0x400000:
        raise ValueError("Unexpected known EXE architecture/imagebase")
    if (len(targets) != len(TARGETS) or
        sum(n for _, _, n in targets) > CODE_BUDGET or
        any(n < 1 or n > 512 for _, _, n in targets)):
        raise ValueError("Invalid V9 sample coverage or byte budget")
    if len({va for _,va,_ in targets}) != len(targets) or len({name for name,_,_ in targets}) != len(targets):
        raise ValueError("Duplicate V9 address or name")
    for name, va, n in targets:
        excerpt = bounded_va_evidence(data, pe, va, n, True)
        if excerpt is None or excerpt.get("byte_count") != n or excerpt.get("truncated_to_section_boundary"):
            raise ValueError("Missing/truncated V9 sample: " + name)
        excerpt["purpose"] = name
        result["samples"].append(excerpt)
    return result


def validate_report(report, expected_sha=EXE_SHA256):
    """Do not accept a reassuring success status with missing sample bodies."""
    if report.get("exe_sha256") != expected_sha or report.get("matches_documented_exe_sha256") is not True:
        return False
    if report.get("warnings") or len(report.get("samples", [])) != len(TARGETS):
        return False
    actual = {}
    for sample in report["samples"]:
        try:
            data = bytes.fromhex(sample["bytes_hex"])
            va = int(sample["va"], 16)
        except (ValueError, TypeError, KeyError):
            return False
        if va in actual or hashlib.sha256(data).hexdigest() != sample.get("bytes_sha256"):
            return False
        actual[va] = (len(data), sample.get("section"), sample.get("truncated_to_section_boundary"))
    return all(actual.get(va) == (n, ".text", False) for _,va,n in TARGETS)


def select_exe():
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    try:
        selection = filedialog.askopenfilename(title="Chọn AngelSLG.exe của Empire of Angels III",
                                               filetypes=[("EXE", "*.exe")])
    finally:
        root.destroy()
    if not selection:
        raise ValueError("No EXE selected")
    return Path(selection)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "build" / "EOA3-Glyph-V9.zip")
    args = parser.parse_args()
    try:
        exe = args.exe or select_exe()
        if not exe.is_file() or exe.name.lower() != "angelslg.exe":
            raise ValueError("Choose the original AngelSLG.exe")
        if exe.stat().st_size > MAX_EXE_SIZE:
            raise ValueError("EXE exceeds safety limit")
        out = args.out
        if out.resolve() == exe.resolve() or out.resolve().is_relative_to(exe.parent.resolve()):
            raise ValueError("Output MUST be outside game installation")
        report = collect(exe.read_bytes())
        if not validate_report(report):
            raise ValueError("EXE hash differs or V9 evidence incomplete; no ZIP was created")
        manifest = {
            "schema_version": 1,"status": "read_only_glyph_v9_not_a_patch",
            "exe_sha256": report["exe_sha256"],"window_count": len(report["samples"]),
            "contents": list(FILE_NAMES),
            "privacy_note": "Contains limited x86 snapshots from owned game; do not share publicly without review.",
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("manifest.json", json.dumps(manifest,indent=2)+"\n")
            z.writestr("glyph_trace_v9.json", json.dumps(report,ensure_ascii=False,indent=2)+"\n")
        print("V9 SUCCESS:", out)
        print("EXE SHA256:", report["exe_sha256"])
        print("No game data modified. This is NOT a translation patch.")
    except (OSError,ValueError,RuntimeError) as exc:
        parser.error(str(exc))

if __name__ == "__main__":
    main()
