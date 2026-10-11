"""Collect read-only EOA3 Windows diagnostics in one ZIP.

Only output file is the requested ZIP. Never writes to, launches, patches, or
attaches to the game. Includes NO executable bytes, font files or paths.
Python 3.9+ and the source/translation JSONs in this repository.
"""
import argparse
import json
import platform
from pathlib import Path
import zipfile

from audit_unicode_layout import analyze, load_sources
from font_preview import make_html
from probe_game import MAX_EXE_SIZE, analyze_bytes
from probe_engine_calls import collect as collect_engine_calls
from probe_engine_followup import collect_followup
from windows_font_probe import analyze_font

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build" / "EOA3-Windows-Diagnostics.zip"


def select_exe():
    """Open local file chooser if available; never auto-scans personal drives."""
    if platform.system() != "Windows":
        raise OSError("File chooser is Windows-only; pass --exe on other hosts")
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        try:
            path = filedialog.askopenfilename(
                title="Chọn AngelSLG.exe của Empire of Angels III",
                filetypes=[("Windows executable", "*.exe"), ("All files", "*.*")],
            )
        finally:
            root.destroy()
    except Exception as exc:
        raise RuntimeError("Cannot open file chooser. Provide --exe instead.") from exc
    if not path:
        raise ValueError("No executable selected; nothing was created")
    return Path(path)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def create_bundle(exe, out=DEFAULT_OUTPUT, font_name="Segoe UI", size_pt=16,
                  source_root=ROOT, font_analyzer=analyze_font):
    exe = Path(exe)
    out = Path(out)
    if not exe.is_file():
        raise ValueError("Executable does not exist: provide the actual AngelSLG.exe")
    if exe.name.lower() != "angelslg.exe":
        raise ValueError("Expected AngelSLG.exe, refusing unrelated EXE")
    if exe.stat().st_size > MAX_EXE_SIZE:
        raise ValueError("Executable exceeds read-only probe size limit")
    if exe.resolve() == out.resolve():
        raise ValueError("Output must not overwrite input executable")
    if not 6 <= size_pt <= 96 or not font_name or len(font_name) > 70:
        raise ValueError("Invalid GDI font selection")
    # Reading the user-selected EXE; no write access to game folder is needed.
    game_bytes = exe.read_bytes()
    exe_info = analyze_bytes(game_bytes, game_folder=exe.parent)
    engine_calls = collect_engine_calls(game_bytes)
    followup = collect_followup(game_bytes)
    exe_info["exe_filename"] = exe.name

    sources = load_sources(source_root)
    static_info = analyze(sources)
    try:
        font_info = font_analyzer(sources, font_name, size_pt)
    except (OSError, RuntimeError, ValueError) as exc:
        # Static information is still useful even if font is not installed,
        # font probing fails, or the OS isn't Windows. Do not include local paths.
        font_info = {
            "status": "font_probe_unavailable",
            "reason": type(exc).__name__,
            "message": "Font measurement unavailable; try Windows or another installed font.",
        }

    manifest = {
        "schema_version": 1, "status": "diagnostic_bundle_not_a_patch",
        "exe_filename": exe.name, "exe_sha256": exe_info["sha256"],
        "translation_count": static_info["counts"].get("translated", 0),
        "review_count": static_info["counts"].get("mode_review", 0),
        "font_status": font_info["status"],
        "contents": [
            "manifest.json",
            "exe_preflight.json",
            "unicode_layout_report.json",
            "font_preflight.json",
            "font_preview.html",
            "engine_callsite_slices.json",
            "engine_followup_evidence.json",
        ],
        "privacy_note": "Contains limited raw machine-code evidence around GDI and two font helpers plus possible caller bytes (NOT a complete EXE), no font files or local paths. Review before sharing publicly.",
    }
    output = {
        "manifest.json": json_bytes(manifest),
        "exe_preflight.json": json_bytes(exe_info),
        "unicode_layout_report.json": json_bytes(static_info),
        "font_preflight.json": json_bytes(font_info),
        "font_preview.html": make_html(static_info, font_name).encode("utf-8"),
        "engine_callsite_slices.json": json_bytes(engine_calls),
        "engine_followup_evidence.json": json_bytes(followup),
    }
    # Refuse path alias/symlink tricks before writing anywhere.
    if out.resolve() == exe.resolve() or out.is_dir():
        raise ValueError("Invalid output path")
    if out.resolve().is_relative_to(exe.parent.resolve()):
        raise ValueError("Output ZIP must be outside the game installation directory")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in manifest["contents"]:
            z.writestr(name, output[name])
    return {"path": out, "manifest": manifest}


def main():
    parser = argparse.ArgumentParser(
        description="Collect Windows EOA3 game/font/Unicode diagnostics into one ZIP without modifying game."
    )
    parser.add_argument("--exe", type=Path, default=None,
                        help="Path to AngelSLG.exe; omit to choose using Windows file dialog")
    parser.add_argument("--font", default="Segoe UI", help="Installed font face to measure")
    parser.add_argument("--size", type=int, default=16, help="Font size in points (6-96)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT,
                        help="Output diagnostics ZIP path; game files are never changed")
    args = parser.parse_args()
    try:
        exe = args.exe or select_exe()
        result = create_bundle(exe, args.out, args.font, args.size)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print("Diagnostics ZIP:", result["path"])
    print("Game SHA-256:", result["manifest"]["exe_sha256"])
    print("Font status:", result["manifest"]["font_status"])
    print("No game executable, font or assets included. Nothing in the game was modified.")


if __name__ == "__main__":
    main()
