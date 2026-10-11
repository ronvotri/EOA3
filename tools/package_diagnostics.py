"""Package portable EOA3 diagnostic scripts + existing script JSONs.

No game assets, binaries, fonts, save files, private paths or executable data
are included. User must extract the ZIP before running the Windows launcher.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "build" / "EOA3-Windows-Diagnostic-Tool.zip"
SCRIPTS = [
    "EOA3-KiemTra-Windows.cmd",
    "tools/audit_unicode_layout.py",
    "tools/font_preview.py",
    "tools/probe_game.py",
    "tools/probe_engine_calls.py",
    "tools/probe_text_callers.py",
    "tools/probe_engine_followup.py",
    "tools/windows_font_probe.py",
    "tools/windows_diagnostic_bundle.py",
    "docs/WINDOWS_RUNTIME_PREFLIGHT.md",
    "docs/UNICODE_LAYOUT_QA.md",
]
USAGE = """EOA3 - BO KIEM TRA WINDOWS (CHI DOC)
=======================================
1) Giai nen TOAN BO zip nay vao mot thu muc rieng (khong giai nen vao game).
2) Nhan dup EOA3-KiemTra-Windows.cmd
3) Trong cua so chon file, tro den AngelSLG.exe cua ban.
4) Neu THANH CONG, cua so build tu mo: EOA3-Windows-Diagnostics.zip
5) Neu BAO LOI, cua so build tu mo: gui EOA3-Diagnostic-Log.txt.
6) Gui ZIP bao cao de phan tich font va ma hoa.

Can Python 3.9+ co san tren Windows. Khong sua, chay, cai dat game, EXE hay font.
Neu Windows khong tim thay Python, cai Python truoc; khong can clone GitHub.
Co the keo file AngelSLG.exe tha vao .cmd de chon nhanh.
Bao cao gom hash SHA256, thong tin PE, danh sach font/ky tu, mau van ban;\nco mot tep JSON nho ve byte may quanh cac diem goi GDI. Hay xem truoc khi chia se cong khai.
KHONG gom EXE nguyen tep, font hoac duong dan day du. Bao cao V6 gom 7 tep,\nbao gom engine_followup_evidence.json voi vai doan ma may nho co gioi han.
Bai test nay CHUA tao patch va CHUA chung minh font hien thi dung trong game.
"""


def package(root=ROOT, output=DEFAULT_OUT):
    root, output = Path(root), Path(output)
    paths = []
    for rel in SCRIPTS:
        p = root / rel
        if not p.is_file() or p.is_symlink():
            raise ValueError("Missing or unsafe packaged script: " + rel)
        paths.append(rel)
    sources = sorted((root/"source").glob("*.json"))
    if len(sources) != 40:
        raise ValueError("Expected 40 original EOA3 script JSONs, got %d" % len(sources))
    for source in sources:
        target = root/"translations"/source.name
        if not target.is_file() or source.is_symlink() or target.is_symlink():
            raise ValueError("Missing/unsafe matching translation: " + source.name)
        paths.append("source/"+source.name)
        paths.append("translations/"+source.name)
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate archive path")
    for name in paths:
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Unsafe archive path: "+name)
    if output.resolve().is_relative_to((root/"source").resolve()):
        raise ValueError("Do not output inside source files")
    if output.resolve().is_relative_to((root/"translations").resolve()):
        raise ValueError("Do not output inside translations")
    data = {name: (root/name).read_bytes() for name in paths}
    hashes = {name: hashlib.sha256(value).hexdigest() for name,value in data.items()}
    manifest = {
        "schema_version": 1,
        "status": "diagnostic_scripts_not_a_patch",
        "python_version": "3.9+",
        "source_scripts": len(sources),
        "includes_game_executable": False,
        "includes_fonts": False,
        "includes_game_assets": False,
        "file_sha256": hashes,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("README-KIEMTRA.txt", USAGE.encode("utf-8"))
        z.writestr("MANIFEST.json", (json.dumps(manifest, indent=2)+"\n").encode("utf-8"))
        for name in paths:
            z.writestr(name, data[name])
    return {"output": output, "source_scripts": len(sources),
            "file_count": len(paths)+2}


def main():
    parser = argparse.ArgumentParser(description="Package EOA3 read-only Windows diagnostic scripts, NOT the game")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = package(output=args.out)
    print("Created portable diagnostic tool ZIP: %s" % result["output"])
    print("40 source + translation JSON pairs; NO executable, game assets or fonts.")
    print("Extract it, then double-click EOA3-KiemTra-Windows.cmd")


if __name__ == "__main__":
    main()
