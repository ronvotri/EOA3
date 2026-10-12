"""Read-only validation of real EOA3 V9 glyph report; no game executable required.

The dispatch mapping is reconstructed from verified byte tables in the V9 ZIP,
not guessed from control-code names. Never writes to source/, translations/,
EXE or assets, and never publishes original code fragments.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from zipfile import ZipFile

EXE_SHA = "2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf"
WINDOWS = {
    0x41C470: (512,"c2799f4284c722ec7113e48ccab1a969e04efe9035385b7a8830d0272734f17d"),
    0x41C5B0: (512,"aa58258771afc0bcbc3884c64a102c5899dfdadecc8998de7dda1d94f8766d99"),
    0x41C650: (512,"26a00e71c0eb5f38c00a1c1fe546c5b570dd6f96ceef06b38c496042a2676cc0"),
    0x41CB90: (512,"b18f608397ce7a16539adfb5cc55358f74067b5bce07ad695b58ce9e05ee2b3c"),
    0x41CCC0: (512,"b58eb15bdb1cb384df04d692ac30c2876ef5e93a2f428e2779b2a41c5779178d"),
    0x414380: (384,"e818871cafe5ee54a102394e5322a7c6f2a8985d53cfd5f4d64cedd7a3b7a35e"),
    0x42AA00: (512,"f47d093a197bdadee799b126d22137cc6958e06a40522109709b9a7bdb9c9dd7"),
    0x42AE00: (512,"9e6923cdb88b7c3615fa1dbfe7a47444f3ff0d365ebb9a9371ea09297c1442a3"),
    0x41AC80: (512,"566fdd1d584e441dc5fe51ede417bb792bf8dcc56c630684f9ec071236eae8ce"),
    0x41B270: (512,"5804d3032780ebb60cb58f62dc21f3e8baf358af38410a0102d8ff66e40fe0b4"),
    0x41B5E0: (512,"3b37a9170fe58745244cb25598a0c72047c4ec806968e3979ab1bb188fe9eb24"),
    0x41B960: (512,"e1328f3d7f05590a36921476b1ec34c44fd9a5c59b8454656b55870559fbccc8"),
    0x41BE40: (512,"d45f45b596cf989906b2d6796e0694c18e57b329ab8b6c7812eda28afe7be7d9"),
}
MEMBERS={"manifest.json","glyph_trace_v9.json"}
CHECK_BYTES={
    0x41C5C3:"8b45fc8b88c40f000083e901",  # bound: count-1
    0x41C5E5:"8b4d0881e1ffff0000",      # lookup key 16-bit
    0x41C5F4:"33f6668b7450203bce",      # sorted array comparison
    0x41C6C8:"33f6668b7441203bd6",      # insertion position
    0x41C741:"e8aa0e0b00",              # copy cached bitmap via memcpy
    0x41C496:"e855e2ffff",              # font raster helper
    0x41CC45:"81b8c40f0000cf070000",    # cache 0x7cf boundary
    0x414389:"8b450883e01fc1e00a",      # 5-bit first channel <<10
    0x414392:"8b4d0c83e11fc1e105",      # 5-bit second channel <<5
    0x41439D:"8b551083e21f",            # 5-bit third channel
    0x42AA09:"33c98a8a6dae4200",        # char -> case index byte
    0x42AA11:"ff248d3dae4200",          # indirect jump by case index
}
DIRECT_CALLS={
    0x41C496:0x41A6F0,0x41C49E:0x41C3B0,
    0x41C741:0x4CD5F0,0x4143BA:0x414260,
    0x42AA3C:0x42A8A0,0x42AB7A:0x42A8A0,
}
CASE_EXPECTED={
    "%":0x42AA18,"c":0x42AB6B,"C":0x42AB6B,
    "k":0x42AC6E,"K":0x42AC6E,
    "w":0x42ABE7,"W":0x42ABE7,
    "N":0x42AA81,"n":0x42AA81,
    "s":0x42AA49,"t":0x42AADD,"z":0x42AB1E,
}
CONTROL_CHARS=tuple("%CKNPSTWXYZcknpstwxyz")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def windows_from_report(report, strict=True):
    require(report.get("status")=="read_only_v9_glyph_trace_not_disassembly_or_patch",
            "Unexpected V9 report type")
    require(report.get("exe_sha256")==EXE_SHA and
            report.get("matches_documented_exe_sha256") is True and
            report.get("warnings")==[],"V9 EXE mismatch or warnings")
    samples=report.get("samples",[])
    require(len(samples)==len(WINDOWS),"V9 requires exactly 13 windows")
    found={}
    for s in samples:
        va=int(s["va"],16)
        require(va in WINDOWS and va not in found,"Unknown or duplicate V9 code address")
        expected_size,expected_digest=WINDOWS[va]
        raw=bytes.fromhex(s["bytes_hex"])
        require(len(raw)==expected_size==s.get("byte_count") and
                s.get("section")==".text" and not s.get("truncated_to_section_boundary"),
                "Invalid section/boundary or incomplete V9 sample")
        digest=hashlib.sha256(raw).hexdigest()
        require(digest==s["bytes_sha256"],"Corrupted SHA in sample")
        if strict:
            require(digest==expected_digest,"Sample differs from user V9 evidence")
        found[va]=raw
    require(set(found)==set(WINDOWS),"Missing expected V9 samples")
    return found


def get(windows,va,size):
    for base,data in windows.items():
        if base<=va and va+size<=base+len(data):
            return data[va-base:va-base+size]
    raise ValueError("Uncovered VA "+hex(va))


def verify_overlaps(*reports):
    windows={}
    overlap_count=0
    for report in reports:
        for va,raw in report.items():
            for pos,b in enumerate(raw):
                addr=va+pos
                if addr in windows:
                    require(windows[addr]==b,"Conflicting V9/V8 overlapping bytes "+hex(addr))
                    overlap_count+=1
                windows[addr]=b
    require(overlap_count>0,"No overlap found")
    return overlap_count


def decode_commands(windows):
    # V9 disassembly: cmp (next_byte - 0x25), 0x55; load LUT at
    # 0x42AE6D and jmp through 12 absolute addresses at 0x42AE3D.
    require(get(windows,0x42AA09,8)==bytes.fromhex(CHECK_BYTES[0x42AA09]),
            "Control dispatcher signature changed")
    require(get(windows,0x42AA11,7)==bytes.fromhex(CHECK_BYTES[0x42AA11]),
            "Control jump table signature changed")
    ptrs=get(windows,0x42AE3D,12*4)
    case_targets=struct.unpack("<12I",ptrs)
    byte_table=get(windows,0x42AE6D,86)
    require(all(0<=v<12 for v in byte_table),"Out-of-range command case index")
    result={}
    for c in CONTROL_CHARS:
        index=ord(c)-0x25
        result[c]=case_targets[byte_table[index]]
    for c,destination in CASE_EXPECTED.items():
        require(result[c]==destination,"Unexpected case target for %"+c)
    return result


def verify_landmarks(windows):
    for va,sig in CHECK_BYTES.items():
        require(get(windows,va,len(sig)//2)==bytes.fromhex(sig),
                "Unexpected instruction bytes at "+hex(va))
    for va,target in DIRECT_CALLS.items():
        raw=get(windows,va,5)
        require(raw[0]==0xe8 and va+5+struct.unpack("<i",raw[1:])[0]==target,
                "Unexpected CALL target at "+hex(va))


def read_v9(path):
    with ZipFile(path) as z:
        names=z.namelist()
        require(set(names)==MEMBERS and len(names)==2,"Unexpected V9 archive members")
        require(all(z.getinfo(n).file_size<3_000_000 for n in names),
                "Unexpectedly large V9 member")
        manifest=json.loads(z.read("manifest.json"))
        require(manifest.get("status")=="read_only_glyph_v9_not_a_patch" and
                manifest.get("exe_sha256")==EXE_SHA and
                manifest.get("window_count")==13 and
                set(manifest.get("contents",[]))==MEMBERS,
                "V9 manifest mismatch")
        return json.loads(z.read("glyph_trace_v9.json"))


def audit(path, v8=None):
    report=read_v9(path)
    found=windows_from_report(report)
    count=verify_overlaps(found)
    verify_landmarks(found)
    commands=decode_commands(found)
    if v8:
        with ZipFile(v8) as z:
            v8_report=json.loads(z.read("renderer_trace_v8.json"))
        require(v8_report.get("exe_sha256")==EXE_SHA and
                v8_report.get("matches_documented_exe_sha256") is True,
                "Wrong V8 reference")
        ref={int(s["va"],16):bytes.fromhex(s["bytes_hex"])
             for s in v8_report["samples"]}
        count+=verify_overlaps(found,ref)
    return {
        "status":"verified_real_v9_static_evidence_not_a_patch",
        "exe_sha256":EXE_SHA,
        "verified_code_windows":len(found),
        "sample_bytes":sum(len(x) for x in found.values()),
        "overlap_byte_checks":count,
        "percent_command_target_va":{c:hex(t) for c,t in sorted(commands.items())},
        "glyph_lookup":"sorted 16-bit keys and binary search at 0x41c5b0",
        "glyph_insertion":"memmove cache rows at 0x41c650",
        "cache_guard":"cmp count with 0x7cf at 0x41cc45",
        "color_intermediate":"(channel0 & 31)<<10 | (channel1 & 31)<<5 | (channel2 & 31)",
        "limitations":[
            "RGB555 is intermediate; 0x414260 final transformation unverified",
            "No decoded Unicode path or playable Vietnamese font patch",
            "TextOutA and 1/2-byte source encoding must be adapted together",
        ],
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("v9",type=Path)
    parser.add_argument("--v8",type=Path)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    result=audit(args.v9,args.v8)
    output=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(output,encoding="utf-8")
    print(output)

if __name__=="__main__":
    main()
