"""EOA3 experimental Vietnamese glyph font + two-script patch builder.

Requires a *copy* of user's original game and a user-supplied Windows TTF/TTC.
Does not execute the game. Does not modify the source EXE or game assets.
Only an explicitly separate install command may touch the user's game COPY.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXE_SHA = "2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf"
FONT_NAME_OFFSET = 992532
FONT_NAME_ORIGINAL = "宋体".encode("gbk")
FONT_NAME_PATCH = b"VV\0\0"
TEST_IDS = {"stage1": "stage1:1607", "DataBase": "DataBase:26628"}
CONTROL = re.compile(r"%[A-Za-z](?:[+-]?\d+)?")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def codebook():
    doc = json.loads((ROOT / "tools" / "vietnamese_gbk_codebook.json").read_text(encoding="utf-8"))
    records = doc["mapping"]
    if len(records) != 74 or doc["mapping_count"] != 74:
        raise ValueError("Expected exactly 74 certified Vietnamese glyph aliases")
    enc = {}
    dec = {}
    cps = {}
    for row in records:
        char = row["vietnamese"]
        code = bytes.fromhex(row["candidate_gbk_hex"])
        if len(char) != 1 or len(code) != 2 or code.decode("gbk") != row["underlying_gbk_char"]:
            raise ValueError("Invalid GBK alias " + repr(row))
        if char in enc or code in dec:
            raise ValueError("Duplicate GBK mapping")
        # Every alias must genuinely be unsupported by stock GBK
        try:
            char.encode("gbk")
        except UnicodeEncodeError:
            pass
        else:
            raise ValueError("Alias unexpectedly has a native GBK encoding: " + char)
        enc[char] = code
        dec[code] = char
        cps[ord(code.decode("gbk"))] = ord(char)
    return enc, dec, cps


def encode_text(value, mapping):
    out = bytearray()
    for char in value:
        out += mapping[char] if char in mapping else char.encode("gbk", errors="strict")
    return bytes(out)


def pack(doc, replacements=None, mapping=None):
    """Reconstruct the known ANGELSCRIPT binary exactly; no hidden fields."""
    replacements = replacements or {}
    out = bytearray(b"ANGELSCRIPT") + struct.pack("<I", doc["version"])

    def string(s):
        b = encode_text(s, mapping) if mapping is not None else s.encode("cp936", errors="strict")
        if len(b) > 65535:
            raise ValueError("ANGELSCRIPT 16-bit string length overflow")
        return struct.pack("<H", len(b)) + b

    for table in doc["tables"]:
        out += struct.pack("<H", len(table))
        for value in table:
            out += string(value)
    for i, (kind, value) in enumerate(doc["tokens"]):
        out.append(kind)
        if kind in (1,2,3,4,8):
            out.append(value)
        elif kind == 5:
            out += string(replacements.get(i, value))
        elif kind in (6,7):
            out += bytes.fromhex(value)
        else:
            raise ValueError("Unknown token type %r" % kind)
    return bytes(out)


def prepare_script(stem, enc):
    doc = json.loads((ROOT / "source" / (stem + ".json")).read_text(encoding="utf-8"))
    rows = json.loads((ROOT / "translations" / (stem + ".json")).read_text(encoding="utf-8"))
    original = pack(doc)
    if sha(original) != doc["sha256"]:
        raise ValueError("Original script reconstruction failed for " + stem)
    matching = [r for r in rows if r["id"] == TEST_IDS[stem]]
    if len(matching) != 1:
        raise ValueError("PoC translation ID missing or duplicated")
    row = matching[0]
    index = row["token"]
    if (row["mode"] != "translate" or
        doc["tokens"][index] != [5, row["source"]] or
        row["call"] not in ({"Say"} if stem == "stage1" else {"AddSkillData"}) or
        row["argument"] != (1 if stem == "stage1" else 2)):
        raise ValueError("PoC text field signature changed")
    if CONTROL.findall(row["source"]) != CONTROL.findall(row["vi"]):
        raise ValueError("PoC translation control codes changed")
    # Build only 1 replacement per script (not all 1,881 translations yet).
    patched = pack(doc, {index: row["vi"]}, enc)
    if original == patched:
        raise ValueError("PoC patch did not change anything")
    return original, patched, row


def patch_exe(original):
    if sha(original) != EXE_SHA:
        raise ValueError("Wrong AngelSLG.exe version / SHA-256; game not patched")
    if original[FONT_NAME_OFFSET:FONT_NAME_OFFSET+5] != FONT_NAME_ORIGINAL + b"\0":
        raise ValueError("Expected SimSun font string not present at known offset")
    # Both verified callsites push the very same string pointer 0x4F2514,
    # then call 0x41AA10, which calls CreateFontIndirectA.
    for va in (0x402BA4, 0x41A507):
        pos = va - 0x400000
        if original[pos-12:pos].find(b"\x68\x14\x25\x4f\x00") == -1:
            raise ValueError("Verified font-name pointer caller changed at 0x%X" % va)
        if original[pos:pos+5] != b"\xe8" + struct.pack("<i", 0x41AA10-pos-0x400000-5):
            raise ValueError("Font factory call changed at 0x%X" % va)
    result=bytearray(original)
    result[FONT_NAME_OFFSET:FONT_NAME_OFFSET+4]=FONT_NAME_PATCH
    delta=[i for i,(a,b) in enumerate(zip(original,result)) if a != b]
    if not delta or any(i < FONT_NAME_OFFSET or i >= FONT_NAME_OFFSET+4 for i in delta):
        raise ValueError("EXE patch not strictly limited to 4 name bytes")
    return bytes(result)


def build_font(input_font, output_path, aliases):
    try:
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise RuntimeError("Missing fonttools. Install locally: py -3 -m pip install fonttools") from exc
    font = TTFont(str(input_font),fontNumber=0)
    if not "glyf" in font or "cmap" not in font or "name" not in font:
        raise ValueError("Base font must be an editable TrueType outline font (glyf table)")
    native_cmap = font.getBestCmap()
    missing = [chr(cp) for cp in sorted(set(aliases.values())) if cp not in native_cmap]
    if missing:
        raise ValueError("Source font is missing Vietnamese glyphs: " + "".join(missing))
    count=0
    for table in font["cmap"].tables:
        if table.isUnicode() and table.format in (4,12):
            for chinese_unicode, vietnamese_unicode in aliases.items():
                table.cmap[chinese_unicode]=native_cmap[vietnamese_unicode]
            count += 1
    if not count:
        raise ValueError("Base TTF has no Windows-compatible Unicode cmap table")
    # GBK/Windows GDI font mapper requests GB2312_CHARSET=134.
    if "OS/2" in font:
        os2=font["OS/2"]
        if hasattr(os2,"ulCodePageRange1"):
            os2.ulCodePageRange1 |= (1 << 18) | 1  # simplified Chinese 936 and Latin1
    names=font["name"]
    for platform,encoding,language in ((3,1,0x409),(1,0,0)):
        for nid,value in ((1,"VV"),(2,"Regular"),(3,"VV-Viet-POC-20261012"),
                          (4,"VV Regular"),(6,"VV-Regular"),
                          (16,"VV"),(17,"Regular")):
            names.setName(value,nid,platform,encoding,language)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    font.save(str(output_path))
    font.close()
    # Verify saved cmap to catch silent fontTools round-trip changes.
    new = TTFont(str(output_path))
    cmap=new.getBestCmap()
    for alias,source in aliases.items():
        if cmap.get(alias)!=native_cmap[source]:
            raise ValueError("Generated font failed glyph cmap roundtrip")
    new.close()
    return output_path


def make_poc(game_copy, base_font, out):
    if game_copy.resolve()==out.resolve() or out.resolve().is_relative_to(game_copy.resolve()):
        raise ValueError("Output must be outside the game-copy folder")
    exe=game_copy/"AngelSLG.exe"
    if not exe.is_file():
        raise ValueError("Choose a COPIED game folder with AngelSLG.exe")
    enc,_,glyphs=codebook()
    # Stage in a separate folder. Do not write a single byte into game-copy here.
    patched_exe=patch_exe(exe.read_bytes())
    outputs={"AngelSLG.exe":patched_exe}
    summary=[]
    for stem in ("stage1","DataBase"):
        baseline,new,row=prepare_script(stem,enc)
        actual_path=game_copy/"Data"/(stem+".bin")
        if not actual_path.is_file() or sha(actual_path.read_bytes())!=sha(baseline):
            raise ValueError("Game-copy script doesn't match original SHA: "+str(actual_path))
        outputs["Data/"+stem+".bin"]=new
        summary.append({"id":row["id"],"source":row["source"],"vi":row["vi"],
                        "original_sha256":sha(baseline),"patched_sha256":sha(new)})
    out.mkdir(parents=True,exist_ok=True)
    for name,b in outputs.items():
        target=out/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(b)
    build_font(base_font,out/"VV.ttf",glyphs)
    manifest={"status":"experimental_vietnamese_glyph_poc_NOT_verified_in_game",
              "exe_original_sha256":EXE_SHA,"font_face":"VV",
              "font_patch":{"original":"宋体","address":"0x4F2514", "offset":FONT_NAME_OFFSET},
              "changed_script_fields":summary,
              "aliases":len(glyphs),"output_files":{n:sha(v) for n,v in outputs.items()},
              "base_font_local_path_not_recorded":True,
              "warnings":["Install ONLY to a separately copied game, never your original game.",
                          "A Windows GDI font with GB2312 charset may not select this face: verify on Windows.",
                          "Only a dialogue and one skill tooltip have changed; no full translation patch.",
                          "No in-game display QA has been completed."]}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("POC BUILD SUCCESS:",out)
    print("Vietnamese glyph aliases:",len(glyphs))
    print("Two ANGELSCRIPT files and patched EXE staged; game folder untouched.")
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game-copy",type=Path,required=True,help="SEPARATE game COPY containing AngelSLG.exe and Data/*.bin")
    p.add_argument("--base-font",type=Path,required=True,help="Existing locally licensed editable TrueType font, e.g. C:/Windows/Fonts/arial.ttf")
    p.add_argument("--out",type=Path,default=ROOT/"build"/"EOA3-Viet-POC")
    args=p.parse_args()
    if not args.base_font.is_file():
        p.error("Font file not found: " + str(args.base_font))
    try:
        make_poc(args.game_copy,args.base_font,args.out)
    except (ValueError,OSError,RuntimeError) as e:
        p.error(str(e))

if __name__=="__main__":
    main()
