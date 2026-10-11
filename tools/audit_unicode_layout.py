"""Read-only Vietnamese glyph/line preflight for EOA3 translation JSON.

Flags are review priorities, NOT measured in-game pixel overflow. Never modifies
source files, translates lookup keys or creates a playable game patch.
Standard library only; Python 3.9+.
"""
import argparse
from collections import Counter, defaultdict
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROL = re.compile(r"%[A-Za-z](?:[+-]?\d+)?")
VISIBLE_CONTROL = re.compile(r"%(?!N)[A-Za-z](?:[+-]?\d+)?")
DEFAULT_WIDTH_CELLS = 52
DEFAULT_EXPANSION = 1.5
CATEGORIES = ("SP_AddAction", "Say", "MessageBox", "SetMission",
              "SetStageName", "AddSkillData", "AddItemData")
PROBE_GRAPHEME_SAMPLE = "Tiếng Việt: ă â ê ô ơ ư đ | Á À Ả Ã Ạ | ắ ằ ẳ ẵ ặ | ế ề ể ễ ệ | ố ồ ổỗộ | ớ ờ ở ỡ ợ | ứ ừ ử ữ ự | ỷ ỹ ỵ"


def text_width(value):
    """Approximate terminal cells; font metrics, kerning and engine glyphs unknown."""
    width = 0
    for char in value:
        if unicodedata.combining(char) or char in "\u200c\u200d":
            continue
        width += 2 if unicodedata.east_asian_width(char) in ("F", "W") else 1
    return width


def logical_lines(value):
    """Treat %N as EOA3 line break and ignore other control codes in measured text."""
    return [VISIBLE_CONTROL.sub("", line) for line in value.split("%N")]


def review_row(row, filename, width_cells=DEFAULT_WIDTH_CELLS,
               expansion=DEFAULT_EXPANSION):
    source = row["source"]
    vi = row["vi"]
    original_lines = logical_lines(source)
    translated_lines = logical_lines(vi)
    src_widths = [text_width(x) for x in original_lines]
    vi_widths = [text_width(x) for x in translated_lines]
    max_src = max(src_widths, default=0)
    max_vi = max(vi_widths, default=0)
    expanded = (
        max_vi > width_cells
        and max_vi > max(1, max_src) * expansion
    )
    over_width = max_vi > width_cells
    flags = []
    if over_width:
        flags.append("width_heuristic")
    if expanded:
        flags.append("longer_than_source_heuristic")
    if unicodedata.normalize("NFC", vi) != vi:
        flags.append("non_nfc")
    if "\n" in vi or "\r" in vi:
        flags.append("literal_newline")
    if CONTROL.findall(source) != CONTROL.findall(vi):
        flags.append("control_mismatch")
    legacy_bad = sorted({ch for ch in vi if not can_encode_cp936(ch)})
    return {
        "id": row["id"], "file": filename, "token": row["token"],
        "call": row["call"], "argument": row["argument"],
        "source": source, "vi": vi,
        "source_line_widths": src_widths, "vi_line_widths": vi_widths,
        "max_source_cells": max_src, "max_vi_cells": max_vi,
        "line_count": len(vi_widths), "legacy_cp936_incompatible": bool(legacy_bad),
        "flags": flags,
    }


def can_encode_cp936(ch):
    try:
        ch.encode("cp936", errors="strict")
        return True
    except UnicodeEncodeError:
        return False


def analyze(sources, width_cells=DEFAULT_WIDTH_CELLS,
            expansion=DEFAULT_EXPANSION):
    """sources = mapping of filename to translation row list. No file I/O."""
    stats = Counter()
    flag_counts = Counter()
    unsupported = Counter()
    unicode_all = Counter()
    priority = []
    by_call = Counter()
    probes = []
    for filename in sorted(sources):
        for row in sources[filename]:
            stats["all_rows"] += 1
            stats["mode_" + row["mode"]] += 1
            if row["mode"] != "translate":
                continue
            if not row["vi"]:
                stats["missing_vi"] += 1
                continue
            stats["translated"] += 1
            by_call[row["call"] or "unknown"] += 1
            detail = review_row(row, filename, width_cells, expansion)
            for flag in detail["flags"]:
                flag_counts[flag] += 1
            if detail["legacy_cp936_incompatible"]:
                stats["rows_with_unencodable_cp936"] += 1
            for ch in row["vi"]:
                if ch != "\n" and not CONTROL.fullmatch(ch):
                    unicode_all[ch] += 1
                if not can_encode_cp936(ch):
                    unsupported[ch] += 1
            if detail["flags"]:
                priority.append(detail)
            if row["call"] in CATEGORIES:
                probes.append(detail)

    priority.sort(
        key=lambda x: ("control_mismatch" not in x["flags"],
                       "literal_newline" not in x["flags"],
                       "non_nfc" not in x["flags"],
                       -max(0, x["max_vi_cells"] - x["max_source_cells"]),
                       -x["max_vi_cells"], x["id"])
    )
    selected = []
    for call in CATEGORIES:
        matches = sorted(
            (x for x in probes if x["call"] == call),
            key=lambda x: (-x["max_vi_cells"], x["id"])
        )
        if matches:
            selected.append(matches[0])
    # Add a short one to check whether the engine handles Vietnamese accents
    short = sorted(
        (x for x in probes if any(c in x["vi"] for c in "ơưđệộứừ") and x["max_vi_cells"] <= 50),
        key=lambda x: (x["max_vi_cells"], x["id"])
    )
    if short:
        selected.append(short[0])
    # The synthetic sample exists for font testing only, not in the game data.
    glyph_probe = {"id": "synthetic-glyph-test-only", "call": "font_probe",
                   "vi": PROBE_GRAPHEME_SAMPLE,
                   "note": "Font coverage diagnostic, not a script row."}
    seen = set()
    selected = [x for x in selected if not (x["id"] in seen or seen.add(x["id"]))]
    # Do not output unbounded duplicates or all file contents in the report.
    top_chars = [
        {"character": ch, "codepoint": "U+%04X" % ord(ch),
         "name": unicodedata.name(ch, "UNKNOWN"),
         "occurrences": occurrences}
        for ch, occurrences in sorted(unsupported.items(), key=lambda t: (-t[1], ord(t[0])))
    ]
    return {
        "schema_version": 1, "status": "static_language_preflight_not_a_game_patch",
        "limits": {"heuristic_line_cells": width_cells, "max_growth_ratio": expansion},
        "counts": dict(sorted(stats.items())), "calls": dict(sorted(by_call.items())),
        "warning_counts": dict(sorted(flag_counts.items())),
        "unencodable_cp936_codepoints": top_chars,
        "distinct_unicode_codepoints": len(unicode_all),
        "priority_rows": priority[:80],
        "font_probe_cases": selected + [glyph_probe],
        "limitations": [
            "Width uses Unicode East Asian terminal-cell approximation, not GDI pixels, in-game font or bounding box.",
            "A width warning is not proof of clipping. A row without a warning can still clip.",
            "CP936 incompatibility is expected; do not strip Vietnamese accents or force lossy GBK output.",
            "No executable/asset files were read or modified. Runtime, font, control sequences and wrapping still require Windows checks.",
        ],
    }


def load_sources(root=ROOT):
    src = root / "source"
    translations = root / "translations"
    result = {}
    for path in sorted(src.glob("*.json")):
        trans = translations / path.name
        if not trans.exists():
            raise ValueError("Missing translation file for source: %s" % path.name)
        result[path.name] = json.loads(trans.read_text(encoding="utf-8"))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", choices=("check", "report"), default="check")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--max-cells", type=int, default=DEFAULT_WIDTH_CELLS)
    parser.add_argument("--expansion", type=float, default=DEFAULT_EXPANSION)
    args = parser.parse_args()
    if args.max_cells < 16 or args.expansion < 1:
        parser.error("Invalid width/expansion thresholds")
    report = analyze(load_sources(), args.max_cells, args.expansion)
    n = report["counts"]
    print("Unicode preflight: %s translated, %s review, %s locked across 40 scripts" %
          (n.get("translated", 0), n.get("mode_review", 0), n.get("mode_locked", 0)))
    print("CP936-incompatible lines: %s; distinct unsupported codepoints: %s" %
          (n.get("rows_with_unencodable_cp936", 0),
           len(report["unencodable_cp936_codepoints"])))
    print("Static width flags: %s; expanded beyond original: %s" %
          (report["warning_counts"].get("width_heuristic", 0),
           report["warning_counts"].get("longer_than_source_heuristic", 0)))
    fatal = any(report["warning_counts"].get(key, 0) for key in
                ("control_mismatch", "literal_newline", "non_nfc"))
    fatal = fatal or n.get("missing_vi", 0) > 0 or n.get("translated", 0) != 1881
    if args.command == "report":
        output = args.out or ROOT / "build" / "unicode_layout_report.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        print("Wrote non-playable QA report: %s" % output)
    if fatal:
        raise SystemExit("FAIL: invalid translation structural/Unicode integrity; inspect QA report")
    print("PASS: Unicode/control syntax preserved; font/overflow remain unverified.")


if __name__ == "__main__":
    main()
