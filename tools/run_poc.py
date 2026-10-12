"""Load user's locally generated VV font temporarily and run copied EOA3.

This is an experimental Windows GDI probe. No persistent font installation.
"""
import argparse
import ctypes
import os
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path


def check_font(font_path):
    if sys.platform!="win32":
        raise RuntimeError("Only runs on Windows")
    gdi=ctypes.WinDLL("gdi32",use_last_error=True)
    gdi.AddFontResourceExW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.LPVOID]
    gdi.AddFontResourceExW.restype=ctypes.c_int
    gdi.RemoveFontResourceExW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.LPVOID]
    gdi.RemoveFontResourceExW.restype=wintypes.BOOL
    added=gdi.AddFontResourceExW(str(font_path),0,None)
    if not added:
        raise RuntimeError("GDI did not load experimental VV font")
    return gdi


def verify_selected_face(gdi):
    gdi.CreateCompatibleDC.argtypes=[wintypes.HDC]
    gdi.CreateCompatibleDC.restype=wintypes.HDC
    gdi.CreateFontW.argtypes=[ctypes.c_int]*13+[wintypes.LPCWSTR]
    gdi.CreateFontW.restype=wintypes.HFONT
    gdi.SelectObject.argtypes=[wintypes.HDC,wintypes.HGDIOBJ]
    gdi.SelectObject.restype=wintypes.HGDIOBJ
    gdi.GetTextFaceW.argtypes=[wintypes.HDC,ctypes.c_int,wintypes.LPWSTR]
    gdi.GetTextFaceW.restype=ctypes.c_int
    gdi.GetGlyphIndicesW.argtypes=[wintypes.HDC,wintypes.LPCWSTR,ctypes.c_int,ctypes.POINTER(ctypes.c_ushort),wintypes.DWORD]
    gdi.GetGlyphIndicesW.restype=wintypes.DWORD
    gdi.DeleteObject.argtypes=[wintypes.HGDIOBJ]
    gdi.DeleteDC.argtypes=[wintypes.HDC]
    dc=gdi.CreateCompatibleDC(None)
    if not dc:raise RuntimeError("CreateCompatibleDC failed")
    font=gdi.CreateFontW(-24,0,0,0,400,0,0,0,134,0,0,0,0,"VV")
    if not font:
        gdi.DeleteDC(dc)
        raise RuntimeError("CreateFontW failed for VV")
    previous=gdi.SelectObject(dc,font)
    try:
        buf=ctypes.create_unicode_buffer(64)
        if gdi.GetTextFaceW(dc,64,buf)<=0 or buf.value.casefold()!="vv":
            raise RuntimeError("GDI substituted another face: "+buf.value+"; NOT launching unverified PoC")
        # GBK alias FD9B maps Chinese U+9FA5 to Vietnamese 'À' glyph in cloned cmap.
        checked="龥"
        indices=(ctypes.c_ushort*len(checked))()
        ret=gdi.GetGlyphIndicesW(dc,checked,len(checked),indices,1)
        if ret==0xffffffff or any(x==0xffff for x in indices):
            raise RuntimeError("VV face selected but required GBK proxy glyph not found")
    finally:
        gdi.SelectObject(dc,previous)
        gdi.DeleteObject(font)
        gdi.DeleteDC(dc)
    print("Windows GDI confirmed VV face and Vietnamese proxy glyph. Runtime test remains experimental.")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game-copy",type=Path,required=True)
    a=p.parse_args()
    folder=a.game_copy.resolve()
    ttf=folder/"_EOA3_VIET_POC_LOCAL_FONT"/"VV.ttf"
    exe=folder/"AngelSLG.exe"
    missing=[]
    if not ttf.is_file(): missing.append('_EOA3_VIET_POC_LOCAL_FONT/VV.ttf')
    if not exe.is_file(): missing.append('AngelSLG.exe')
    if not (folder/'_EOA3_VIET_POC_BACKUP'/'manifest.json').is_file():
        missing.append('_EOA3_VIET_POC_BACKUP/manifest.json')
    if missing:
        p.error('KHONG MO GAME: duong dan da nhan la %s. Thieu: %s. '
                'Hay mo BAT-DAU-O-DAY.cmd v0.3 va chon file AngelSLG.exe trong ban sao.'
                % (folder,', '.join(missing)))
    gdi=check_font(ttf)
    try:
        verify_selected_face(gdi)
        print("Starting copied EOA3; please inspect stage 1 conversation + first skill tooltip.")
        completed=subprocess.run([str(exe)],cwd=str(folder),check=False)
        print("Game exited, code:",completed.returncode)
    finally:
        gdi.RemoveFontResourceExW(str(ttf),0,None)

if __name__=="__main__":main()
