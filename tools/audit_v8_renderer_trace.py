"""Verify real EOA3 V8 code windows and palette. Read-only; no game EXE or assets."""
import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path

EXE_SHA = "2d7d9705837e32c72685d69e50e426fde168ea8d435de90ba937cefbf5138baf"
WINDOWS = {
  0x41C790:(512,"904891976d44068c14645ba1bfd31b2c0094af8a549bad07c45af7d965a2e682"),
  0x41C990:(512,"cafb93d976fdf7faa17a1405abc649170ab81e72bb75c1e04fde29c433da613b"),
  0x41ABF0:(512,"3661bf9aa0519524610c0c3ea0276236f98c76e8538db903ef4f09ebaca234da"),
  0x41A600:(512,"ce7ee262d9fe29eb8acb6156745cc048d53420ed4a749fa2a73f35cf73d868c2"),
  0x42A8A0:(448,"b6bae4fdbbbe8fc720d6e19863808cca946652f7de2fa9b5c5153ebe76830f39"),
  0x42AED0:(320,"13c50d7d30ab022859ff4e770ae482100a6c44137f4497f2926fd4e7a3678bb2"),
  0x42AAF0:(512,"439cfa44cb1c7576973c4e25ce8f83b2fbd943148097eedcb08e36808afec546"),
}
PALETTE_SHA = "3dd254eff3b201d0f9ea3878353fdc54b6b4a29f62e04a5f1ec6177b13ec8301"
TRIPLES = ((0,0,0),(31,31,31),(31,0,0),(0,31,0),(0,0,31),(31,31,0),
           (31,0,31),(0,31,31),(15,15,15),(0,0,0),(15,0,0),
           (0,15,0),(0,0,15),(15,15,0),(15,0,15),(0,15,15))
MEMBERS = {"manifest.json","exe_preflight.json","unicode_layout_report.json",
           "font_preflight.json","font_preview.html","engine_callsite_slices.json",
           "engine_followup_evidence.json","renderer_trace_v8.json"}
LANDMARKS = {
  0x41C7E0:"33c98a0881f980000000",      # if byte >= 0x80
  0x41C7F2:"8b45fc8a0a8888c80f0000",    # two-byte character first byte
  0x41C7FD:"8b55f483c201",              # increment byte index
  0x41C80C:"8b4dfc8a108891c90f0000",    # second byte
  0x41C834:"c680c90f000000",            # single-byte path clears second byte
  0x41C84C:"668b88c80f000051",          # font index lookup input
  0x41ABFC:"8b45fc8b4d088988e00f0000",  # DWORD at +FE0
  0x41AC2C:"8b45fc668b4d08668988e60f0000", # WORD +FE6
  0x41AC5C:"8b45fc668b4d08668988e40f0000", # WORD +FE4
  0x42A8A9:"6a0a8b4510508b4d0c51", # radix 10
  0x42AED9:"8b4510508b4d0c518b550852", # forwards 3 params
  0x42AB91:"8b55e881e20f000080",
  0x42ACA4:"6bc903",
}
CALLS = {
  0x41C7A7:0x4CE790,0x41C857:0x41C5B0,0x41C8BB:0x41CCC0,
  0x41C928:0x41AC80,0x41C961:0x41B270,0x41C99B:0x41B5E0,
  0x41C9D2:0x41B960,0x41CA08:0x41BE40,0x41CA34:0x41C650,
  0x41CA6E:0x41C470,0x42A8B3:0x4CF41E,0x42AEE5:0x414380,
  0x42AB2D:0x42A8A0,0x42AB61:0x41AA10,
  0x42AC52:0x41AC50,0x42ACDA:0x41AC20,
}

def check(ok, message):
    if not ok:
        raise ValueError(message)

def digest(b):
    return hashlib.sha256(b).hexdigest()

def read_bundle(path, expected):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        check(len(names)==len(set(names)) and set(names)==expected,"Bad ZIP members")
        return {n:z.read(n) for n in names}

def samples(report, verify_historical=True):
    check(report.get("matches_documented_exe_sha256") is True and
          report.get("exe_sha256")==EXE_SHA and report.get("warnings")==[],
          "Unknown EXE SHA or warnings")
    entries = report.get("samples",[])
    check(len(entries)==7,"Missing V8 code samples")
    raw={}
    for s in entries:
        va=int(s["va"],16)
        check(va in WINDOWS and va not in raw,"Unknown/duplicate window")
        expected_n,expected_sha=WINDOWS[va]
        data=bytes.fromhex(s["bytes_hex"])
        check(s.get("byte_count")==expected_n and len(data)==expected_n and
              s.get("section")==".text" and not s.get("truncated_to_section_boundary"),
              "Truncated / non-code window")
        check(digest(data)==s.get("bytes_sha256"),"Corrupt sample digest")
        if verify_historical:
            check(digest(data)==expected_sha,"Wrong known V8 window")
        raw[va]=data
    check(set(raw)==set(WINDOWS),"Wrong sample coverage")
    return raw

def at(windows, va, length):
    for base,b in windows.items():
        if base<=va and va+length<=base+len(b):
            return b[va-base:va-base+length]
    raise ValueError("VA outside samples: "+hex(va))

def verify_x86(windows):
    for va,hx in LANDMARKS.items():
        check(at(windows,va,len(hx)//2)==bytes.fromhex(hx),
              "Bad instruction at "+hex(va))
    for va,target in CALLS.items():
        call=at(windows,va,5)
        check(call[0]==0xE8 and va+5+struct.unpack("<i",call[1:])[0]==target,
              "Wrong relative call at "+hex(va))

def overlaps(new,old):
    count=0
    for a,x in new.items():
        for b,y in old.items():
            left=max(a,b);right=min(a+len(x),b+len(y))
            if right>left:
                check(x[left-a:right-a]==y[left-b:right-b],
                      "V7/V8 overlap mismatch at "+hex(left))
                count+=1
    check(count>=2,"Missing both historical overlaps")
    return count

def palette(p):
    check(p.get("va")=="0x522f44" and p.get("section")==".data" and
          p.get("byte_count")==48 and not p.get("truncated_to_section_boundary"),
          "Missing 48-byte reference table")
    data=bytes.fromhex(p["bytes_hex"])
    check(len(data)==48 and digest(data)==PALETTE_SHA==p.get("bytes_sha256"),
          "Wrong V8 palette SHA")
    t=tuple(tuple(data[i:i+3]) for i in range(0,48,3))
    check(t==TRIPLES,"Wrong 16x3 reference triples")
    return t

def audit(v8_zip, v7_zip=None):
    f=read_bundle(v8_zip,MEMBERS)
    manifest=json.loads(f["manifest.json"])
    check(manifest.get("status")=="diagnostic_bundle_not_a_patch" and
          manifest.get("exe_sha256")==EXE_SHA and
          set(manifest.get("contents",[]))==MEMBERS and
          manifest.get("translation_count")==1881 and
          manifest.get("review_count")==574,"Bad manifest")
    v8=json.loads(f["renderer_trace_v8.json"])
    raw=samples(v8)
    verify_x86(raw)
    triples=palette(v8["palette_reference_bytes"])
    embedded=json.loads(f["engine_followup_evidence.json"])
    check(embedded.get("exe_sha256")==EXE_SHA and embedded.get("warnings")==[],
          "V7 embedded report inconsistent")
    older={int(s["va"],16):bytes.fromhex(s["bytes_hex"])
           for s in embedded["target_code_windows"]}
    overlap_count=overlaps(raw,older)
    if v7_zip:
        v7f=read_bundle(v7_zip,MEMBERS-{"renderer_trace_v8.json"})
        check(v7f["engine_followup_evidence.json"]==f["engine_followup_evidence.json"],
              "External V7 report differs from embedded V7")
        old=json.loads(v7f["engine_followup_evidence.json"])
        overlaps(raw,{int(s["va"],16):bytes.fromhex(s["bytes_hex"])
                      for s in old["target_code_windows"]})
    return {
      "status":"verified_static_v8_not_playable_patch",
      "exe_sha256":EXE_SHA,"seven_windows":len(raw),
      "checked_rel32_calls":len(CALLS),"v7_overlap_pairs":overlap_count,
      "palette_triples":[list(x) for x in triples],
      "limitations":["Glyph and layout helper bodies not sampled",
        "Consumer continues beyond 0x41CB8F",
        "The %c dispatcher and 0x414380 color packer remain unverified",
        "No runtime Unicode/patch is validated"],
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("v8_zip",type=Path)
    ap.add_argument("--v7",type=Path)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    result=audit(args.v8_zip,args.v7)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                            encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
