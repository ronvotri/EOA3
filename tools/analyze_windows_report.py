"""Validate an EOA3 Windows diagnostic ZIP and summarize its evidence.

This tool reads reports only. It does NOT open any game executable, modify the
game, or prove that Windows can render the text inside AngelSLG.exe.
"""
import argparse
import json
import re
from pathlib import Path
from zipfile import BadZipFile, ZipFile

REQUIRED_FILES = {
    "manifest.json", "exe_preflight.json", "unicode_layout_report.json",
    "font_preflight.json", "font_preview.html",
}
OPTIONAL_FILES = {"engine_callsite_slices.json"}
MAX_MEMBER_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 12 * 1024 * 1024
IMPORTANT_CALLS = ("TextOutA", "TextOutW", "CreateFontIndirectA",
                   "CreateFontIndirectW", "MultiByteToWideChar",
                   "WideCharToMultiByte")
EXPECTED_HISTORICAL_VAS = {
    "TextOutA": {"0x41a79a", "0x41a7b9"},
    "CreateFontIndirectA": {"0x41aaab"},
}


def read_zip(path):
    """Never extract untrusted ZIP content to disk."""
    try:
        with ZipFile(path) as archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            if len(names) != len(set(names)) or set(names) not in (REQUIRED_FILES, REQUIRED_FILES | OPTIONAL_FILES):
                raise ValueError("Unexpected ZIP members; expected five legacy or six current diagnostic files")
            if any(item.file_size > MAX_MEMBER_BYTES for item in infos):
                raise ValueError("Diagnostic ZIP contains oversized member")
            if sum(item.file_size for item in infos) > MAX_TOTAL_BYTES:
                raise ValueError("Diagnostic ZIP exceeds uncompressed size budget")
            return {
                name: json.loads(archive.read(name).decode("utf-8"))
                for name in names if name.endswith(".json")
            }
    except BadZipFile as exc:
        raise ValueError("Not a valid diagnostic ZIP") from exc


def analyze_reports(docs):
    manifest = docs["manifest.json"]
    exe = docs["exe_preflight.json"]
    unicode = docs["unicode_layout_report.json"]
    font = docs["font_preflight.json"]
    if manifest.get("status") != "diagnostic_bundle_not_a_patch":
        raise ValueError("Unexpected or unverified diagnostic manifest")
    if exe.get("status") != "static_diagnostic_only_not_a_patch":
        raise ValueError("Not a static EXE report")
    if unicode.get("status") != "static_language_preflight_not_a_game_patch":
        raise ValueError("Not a Unicode preflight report")
    if not re.fullmatch(r"[0-9a-f]{64}", str(manifest.get("exe_sha256", ""))):
        raise ValueError("Missing valid SHA-256")
    if exe.get("sha256") != manifest["exe_sha256"]:
        raise ValueError("EXE hash mismatch between reports")
    if exe.get("exe_filename", "").lower() != "angelslg.exe":
        raise ValueError("This report did not examine AngelSLG.exe")
    if manifest.get("translation_count") != unicode.get("counts", {}).get("translated"):
        raise ValueError("Translation total differs between reports")
    if manifest.get("review_count") != unicode.get("counts", {}).get("mode_review"):
        raise ValueError("Review total differs between reports")
    if manifest.get("font_status") != font.get("status"):
        raise ValueError("Font status differs between reports")

    imports = exe.get("gdi_and_encoding_imports", [])
    api_names = sorted({item.get("api", "") for item in imports})
    xrefs = exe.get("potential_x86_iat_calls", [])
    observed_xrefs = {
        api: sorted({va.lower() for item in xrefs
                     if item.get("api") == api
                     for va in item.get("candidate_call_vas", [])})
        for api in IMPORTANT_CALLS
    }
    historic_matches = {
        api: sorted(set(observed_xrefs[api]) & targets)
        for api, targets in EXPECTED_HISTORICAL_VAS.items()
    }
    charset_bytes = (
        exe.get("historical_va_hints", {})
        .get("charset_134_historical", {})
        .get("bytes_hex_at_location", "")
    )
    # mov byte ptr [ebp-0x29], 0x86 (x86) is a probable LOGFONT charset
    # assignment; the 16 sampled bytes alone do not establish control flow.
    charset_134_bytes_match = charset_bytes.lower().startswith("c645d786")
    font_present = font.get("status") == "local_windows_gdi_font_diagnostic_only"
    sample_ratios = []
    if font_present:
        for item in font.get("sample_extents", []):
            src = max(item.get("source_line_px", []), default=0)
            vi = max(item.get("vi_line_px", []), default=0)
            sample_ratios.append({
                "id": item.get("id"), "call": item.get("call"),
                "source_max_px": src, "vi_max_px": vi,
                "ratio_rounded": round(vi / src, 2) if src else None,
            })
        sample_ratios.sort(key=lambda item: (
            -(item["ratio_rounded"] or 0), item.get("id", "")
        ))
    gd = exe.get("import_table_diagnostics", {})
    code = docs.get("engine_callsite_slices.json")
    if code is not None:
        if code.get("status") != "read_only_code_neighborhoods_not_disassembly_or_patch":
            raise ValueError("Unexpected engine callsite evidence status")
        if code.get("exe_sha256") != exe["sha256"]:
            raise ValueError("Engine code-slice SHA-256 differs from EXE metadata")
    code_summary = {
        "present": code is not None,
        "candidate_count_by_api": code.get("candidate_count_by_api", {}) if code else {},
        "reference_exe_matched": code.get("matches_documented_exe_sha256") if code else None,
        "scope": "Raw bounded code neighborhoods, not disassembly or proof of string-buffer origin",
    }
    return {
        "schema_version": 1,
        "status": "evidence_summary_not_a_game_patch",
        "game_exe": {
            "sha256": exe["sha256"], "architecture": exe.get("architecture"),
            "file_size": exe.get("file_size"), "imagebase": exe.get("imagebase"),
            "entry_rva": exe.get("entry_rva"),
            "installation_bin_count": exe.get("installation", {}).get("data_bin_count"),
        },
        "engine_code_slice_evidence": code_summary,
        "pe_imports": {
            "descriptors_read": gd.get("descriptors_read"),
            "null_terminated": gd.get("null_terminated"),
            "warnings": gd.get("warnings", []),
            "interesting_imports_found": api_names,
            "historical_x86_iat_candidate_matches": historic_matches,
            "charset_134_bytes_at_historical_location": charset_134_bytes_match,
            "font_name_gbk_byte_hits": exe.get("font_name_byte_offsets", {}).get("Songti_GBK", []),
            "scope": "IAT byte-pattern matches and 16-byte snippets, not runtime disassembly",
        },
        "font_probe": {
            "status": font.get("status"),
            "face_requested": font.get("font_requested"),
            "face_selected": font.get("font_selected"),
            "size_pt": font.get("size_pt"), "dpi": font.get("dpi"),
            "characters_tested": font.get("required_unique_nonspace_characters"),
            "missing_glyph_candidate_count":
                len(font.get("missing_glyph_candidates", [])) if font_present else None,
            "limitations": "GDI glyph coverage of the selected desktop font only",
        },
        "translation_preflight": {
            "total": unicode.get("counts", {}).get("translated"),
            "review": unicode.get("counts", {}).get("mode_review"),
            "unencodable_cp936_rows":
                unicode.get("counts", {}).get("rows_with_unencodable_cp936"),
            "unencodable_cp936_distinct_chars":
                len(unicode.get("unencodable_cp936_codepoints", [])),
            "width_warnings_heuristic":
                unicode.get("warning_counts", {}).get("width_heuristic"),
            "expanded_warnings_heuristic":
                unicode.get("warning_counts", {}).get("longer_than_source_heuristic"),
        },
        "measured_desktop_font_samples_sorted_by_ratio": sample_ratios,
        "limits": [
            "No executable contents were submitted; only preflight metadata.",
            "Runtime draw pipeline, true viewport widths, codepage conversion and savegame hooks remain unverified.",
            "Do not infer a Unicode-safe engine from the presence of MultiByteToWideChar imports.",
            "Never ship modified BINs by forcing UTF-8 into a CP936 field.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Summarize an EOA3 Windows diagnostic ZIP, without reading or altering the game"
    )
    parser.add_argument("zip", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    try:
        summary = analyze_reports(read_zip(args.zip))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    payload = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print("Wrote read-only diagnostic summary:", args.out)
    else:
        print(payload)


if __name__ == "__main__":
    main()
