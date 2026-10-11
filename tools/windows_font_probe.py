"""Measure actual Windows GDI glyph coverage and string extent, read-only.

Does not load/run/modify AngelSLG.exe, fonts or registry. Windows host only.
Report is a FONT DIAGNOSTIC: not proof that the game uses the same renderer.
"""
import argparse
import ctypes
import json
import platform
import re
from pathlib import Path
from ctypes import wintypes

from audit_unicode_layout import (
    CONTROL, PROBE_GRAPHEME_SAMPLE, analyze, load_sources, logical_lines
)

ROOT = Path(__file__).resolve().parents[1]


def required_characters(sources):
    """Return unique Unicode chars from *all* translated text, not just samples."""
    all_text = []
    for filename in sorted(sources):
        all_text.extend(x["vi"] for x in sources[filename]
                        if x["mode"] == "translate" and x["vi"])
    all_text.append(PROBE_GRAPHEME_SAMPLE)
    return sorted({
        char for text in all_text for visible in logical_lines(text)
        for char in visible if not char.isspace()
    }, key=ord)


def select_samples(sources):
    report = analyze(sources)
    return report["font_probe_cases"]


def create_font_prober(font_name, size_pt):
    if platform.system() != "Windows":
        raise OSError("Windows GDI required; run this on the user's Windows machine.")
    if not font_name or len(font_name) > 70:
        raise ValueError("Font face name is invalid")
    if size_pt < 6 or size_pt > 96:
        raise ValueError("Font size must be between 6 and 96 points")
    gdi = ctypes.windll.gdi32
    gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi.CreateCompatibleDC.restype = wintypes.HDC
    gdi.DeleteDC.argtypes = [wintypes.HDC]
    gdi.DeleteDC.restype = wintypes.BOOL
    gdi.CreateFontW.argtypes = [
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
        wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
        wintypes.LPCWSTR,
    ]
    gdi.CreateFontW.restype = wintypes.HFONT
    gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi.SelectObject.restype = wintypes.HGDIOBJ
    gdi.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi.DeleteObject.restype = wintypes.BOOL
    gdi.GetGlyphIndicesW.argtypes = [wintypes.HDC, wintypes.LPCWSTR,
                                    ctypes.c_int, ctypes.POINTER(ctypes.c_ushort), wintypes.DWORD]
    gdi.GetGlyphIndicesW.restype = wintypes.DWORD
    gdi.GetTextExtentPoint32W.argtypes = [wintypes.HDC, wintypes.LPCWSTR,
                                         ctypes.c_int, ctypes.POINTER(wintypes.SIZE)]
    gdi.GetTextExtentPoint32W.restype = wintypes.BOOL
    gdi.GetTextFaceW.argtypes = [wintypes.HDC, ctypes.c_int, wintypes.LPWSTR]
    gdi.GetTextFaceW.restype = ctypes.c_int
    gdi.GetDeviceCaps.argtypes = [wintypes.HDC, ctypes.c_int]
    gdi.GetDeviceCaps.restype = ctypes.c_int
    hdc = gdi.CreateCompatibleDC(None)
    if not hdc:
        raise OSError("Unable to create read-only GDI measurement DC")
    # LOGPIXELSY = 90. Negative font height requests character height.
    dpi = gdi.GetDeviceCaps(hdc, 90) or 96
    height = -round(size_pt*dpi/72)
    font = gdi.CreateFontW(height, 0, 0, 0, 400, 0, 0, 0, 1,
                           0, 0, 0, 0, font_name)
    if not font:
        gdi.DeleteDC(hdc)
        raise OSError("CreateFontW failed")
    old = gdi.SelectObject(hdc, font)
    if not old:
        gdi.DeleteObject(font)
        gdi.DeleteDC(hdc)
        raise OSError("Cannot select font into GDI DC")

    def glyph_missing(ch):
        if ord(ch) > 0xFFFF:
            return None
        glyph = ctypes.c_ushort(0)
        n = gdi.GetGlyphIndicesW(hdc, ch, 1, ctypes.byref(glyph), 1)
        if n == 0xFFFFFFFF:
            raise OSError("GetGlyphIndicesW failed")
        return glyph.value == 0xFFFF

    def pixels(text):
        if not text:
            return 0
        rect = wintypes.SIZE()
        if not gdi.GetTextExtentPoint32W(hdc, text, len(text), ctypes.byref(rect)):
            raise OSError("GetTextExtentPoint32W failed")
        return rect.cx

    def selected_face():
        buf = ctypes.create_unicode_buffer(128)
        gdi.GetTextFaceW(hdc, 128, buf)
        return buf.value

    def close():
        gdi.SelectObject(hdc, old)
        gdi.DeleteObject(font)
        gdi.DeleteDC(hdc)

    return {"missing": glyph_missing, "pixels": pixels, "face": selected_face(),
            "dpi": dpi, "close": close}


def analyze_font(sources, font_name="Segoe UI", size_pt=16):
    gdi = create_font_prober(font_name, size_pt)
    try:
        chars = required_characters(sources)
        missing = [ch for ch in chars if gdi["missing"](ch) is True]
        indeterminate = [ch for ch in chars if gdi["missing"](ch) is None]
        cases = []
        for item in select_samples(sources):
            vi = item["vi"]
            translated = logical_lines(vi)
            original = logical_lines(item.get("source", ""))
            cases.append({
                "id": item["id"], "call": item["call"],
                "source_line_px": [gdi["pixels"](x) for x in original],
                "vi_line_px": [gdi["pixels"](x) for x in translated],
                "vi_text": vi,
            })
        return {
            "schema_version": 1,
            "status": "local_windows_gdi_font_diagnostic_only",
            "font_requested": font_name, "font_selected": gdi["face"],
            "size_pt": size_pt, "dpi": gdi["dpi"],
            "required_unique_nonspace_characters": len(chars),
            "missing_glyph_candidates": [{"char": ch, "codepoint": "U+%04X" % ord(ch)}
                                         for ch in missing],
            "glyph_status_indeterminate_nonbmp": [{"char": ch, "codepoint": "U+%X" % ord(ch)}
                                                   for ch in indeterminate],
            "sample_extents": cases,
            "limitations": [
                "Only selected font face and GDI text extent on this Windows host were examined.",
                "The game may use a different font, fallback mechanism, text renderer, charset or clipping bounds.",
                "Widths in pixels are not in-game bounds, and zero missing glyphs does not prove the game renders Vietnamese.",
                "No game binary was loaded, run or modified.",
            ],
        }
    finally:
        gdi["close"]()


def main():
    parser = argparse.ArgumentParser(description="Test Windows font glyphs and text widths without modifying the game.")
    parser.add_argument("--font", default="Segoe UI")
    parser.add_argument("--size", type=int, default=16)
    parser.add_argument("--out", type=Path, default=ROOT/"build"/"eoa3-font-preflight.json")
    args = parser.parse_args()
    report = analyze_font(load_sources(), args.font, args.size)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print("Font:", report["font_selected"], "requested:", args.font)
    print("Required symbols:", report["required_unique_nonspace_characters"],
          "missing glyph candidates:", len(report["missing_glyph_candidates"]))
    print("GDI diagnostic saved:", args.out)
    print("This is NOT proof of game runtime rendering.")


if __name__ == "__main__":
    main()
