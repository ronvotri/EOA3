"""Read-only Windows PE / EOA3 installation preflight (Python 3.9+, stdlib).

This script never patches or launches the game. Static evidence alone cannot
prove Vietnamese glyph rendering or that a historical VA still points to code.
"""
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

MAX_EXE_SIZE = 512 * 1024 * 1024
LEGACY_VAS = {
    "TextOutA_callsite_1_historical": 0x41A79A,
    "TextOutA_callsite_2_historical": 0x41A7B9,
    "CreateFontIndirectA_callsite_historical": 0x41AAAB,
    "charset_134_historical": 0x41AA85,
}
INTERESTING_APIS = {
    "TextOutA", "TextOutW", "ExtTextOutA", "ExtTextOutW",
    "DrawTextA", "DrawTextW", "CreateFontIndirectA", "CreateFontIndirectW",
    "GetTextExtentPoint32A", "GetTextExtentPoint32W", "MultiByteToWideChar",
    "WideCharToMultiByte", "GetACP", "GetCPInfo", "CharNextA",
}


def get_u16(data, offset):
    if offset < 0 or offset + 2 > len(data):
        raise ValueError("Truncated PE field at offset %d" % offset)
    return struct.unpack_from("<H", data, offset)[0]


def get_u32(data, offset):
    if offset < 0 or offset + 4 > len(data):
        raise ValueError("Truncated PE field at offset %d" % offset)
    return struct.unpack_from("<I", data, offset)[0]


def get_u64(data, offset):
    if offset < 0 or offset + 8 > len(data):
        raise ValueError("Truncated PE field at offset %d" % offset)
    return struct.unpack_from("<Q", data, offset)[0]


def c_string(data, offset, limit=512):
    if offset is None or offset < 0 or offset >= len(data):
        raise ValueError("Invalid string pointer in PE")
    end = data.find(b"\0", offset, min(len(data), offset + limit))
    if end < 0:
        raise ValueError("Unterminated string in PE")
    return data[offset:end].decode("ascii", errors="replace")


def parse_pe(data):
    if not isinstance(data, bytes) or len(data) < 0x100 or data[:2] != b"MZ":
        raise ValueError("Not an MZ/PE executable")
    peoff = get_u32(data, 0x3C)
    if peoff + 24 > len(data) or data[peoff:peoff+4] != b"PE\0\0":
        raise ValueError("Invalid PE header")
    machine, section_count, _, _, _, opt_size, _ = struct.unpack_from("<HHIIIHH", data, peoff + 4)
    if section_count < 1 or section_count > 96:
        raise ValueError("Invalid PE section count")
    opt = peoff + 24
    if opt + opt_size > len(data):
        raise ValueError("Truncated PE optional header")
    magic = get_u16(data, opt)
    if magic not in (0x10B, 0x20B):
        raise ValueError("Unsupported PE optional header magic")
    is64 = magic == 0x20B
    min_opt_size = 112 if is64 else 96
    if opt_size < min_opt_size:
        raise ValueError("Truncated PE optional header fields")
    imagebase = get_u64(data, opt + 24) if is64 else get_u32(data, opt + 28)
    entry_rva = get_u32(data, opt + 16)
    header_size = get_u32(data, opt + 60)
    data_dir = opt + (112 if is64 else 96)
    number_rva_and_sizes = get_u32(data, opt + (108 if is64 else 92))
    section_offset = opt + opt_size
    sections = []
    for i in range(section_count):
        pos = section_offset + 40*i
        if pos + 40 > len(data):
            raise ValueError("Truncated PE sections")
        rawname, virtual_size, virtual_addr, raw_size, raw_ptr, _, _, _, _, flags = struct.unpack_from("<8sIIIIIIHHI", data, pos)
        sections.append({
            "name": rawname.split(b"\0", 1)[0].decode("ascii", errors="replace"),
            "rva": virtual_addr, "virtual_size": virtual_size,
            "file_offset": raw_ptr, "file_size": raw_size,
            "executable": bool(flags & 0x20000000),
        })

    def offset_for_rva(rva):
        if rva < header_size and rva < len(data):
            return rva
        for section in sections:
            delta = rva - section["rva"]
            if 0 <= delta < max(section["virtual_size"], section["file_size"]):
                if delta >= section["file_size"]:
                    return None  # Virtual-only bytes: not present in file
                off = section["file_offset"] + delta
                return off if off < len(data) else None
        return None

    imports = []
    warnings = []
    has_imports = False
    terminated = None
    descriptor_count = 0
    if number_rva_and_sizes > 1 and data_dir + 16 <= opt + opt_size:
        import_rva = get_u32(data, data_dir + 8)
        import_size = get_u32(data, data_dir + 12)
        if import_rva:
            has_imports = True
            terminated = False
            # IMAGE_IMPORT_DESCRIPTOR is a null-terminated list (20 bytes/entry).
            # A PE's directory Size is NOT a reliable bound for the final zero
            # descriptor: some old executables exclude it. Use mapped RVA
            # bounds plus a strict record budget, never raw arbitrary offsets.
            # The previous size//20 loop falsely raised "descriptor limit"
            # for perfectly readable tables without an in-size terminator.
            for desc in range(1024):
                descriptor_rva = import_rva + 20 * desc
                at = offset_for_rva(descriptor_rva)
                if at is None or at + 20 > len(data):
                    warnings.append("import_descriptors_end_at_unmapped_or_truncated_rva")
                    break
                # Require all 20 descriptor bytes to be file-backed; mapping
                # only the first byte is insufficient near section boundaries.
                if any(offset_for_rva(descriptor_rva + j) != at + j
                       for j in (0, 4, 8, 12, 16, 19)):
                    warnings.append("import_descriptor_crosses_raw_section_boundary")
                    break
                oft, timestamp, forwarder, dll_rva, ft = struct.unpack_from("<IIIII", data, at)
                if not (oft or timestamp or forwarder or dll_rva or ft):
                    terminated = True
                    if import_size and 20 * (desc + 1) > import_size:
                        warnings.append("import_directory_size_does_not_include_null_terminator")
                    break
                if not dll_rva or not ft:
                    warnings.append("import_descriptor_missing_dll_or_iat")
                    break
                try:
                    dll = c_string(data, offset_for_rva(dll_rva))
                except ValueError:
                    warnings.append("import_descriptor_invalid_dll_name")
                    break
                descriptor_count += 1
                thunk_rva = oft or ft
                ptr_size = 8 if is64 else 4
                highbit = 1 << (ptr_size * 8 - 1)
                for index in range(4096):
                    thunk_off = offset_for_rva(thunk_rva + index * ptr_size)
                    if thunk_off is None or thunk_off + ptr_size > len(data):
                        warnings.append("import_thunk_unmapped_or_truncated")
                        break
                    value = get_u64(data, thunk_off) if is64 else get_u32(data, thunk_off)
                    if value == 0:
                        break
                    if len(imports) >= 16384:
                        warnings.append("import_symbol_safety_budget_reached")
                        break
                    if value & highbit:
                        name = "#ordinal:%d" % (value & 0xFFFF)
                    else:
                        hint_offset = offset_for_rva(value)
                        if hint_offset is None:
                            warnings.append("import_symbol_unmapped_hint_name")
                            break
                        try:
                            name = c_string(data, hint_offset + 2)
                        except ValueError:
                            warnings.append("import_symbol_invalid_hint_name")
                            break
                    imports.append({
                        "dll": dll, "api": name, "iat_rva": ft + index * ptr_size,
                        "iat_va": imagebase + ft + index * ptr_size,
                    })
                else:
                    warnings.append("import_thunk_safety_budget_reached")
                if len(imports) >= 16384:
                    break
            else:
                warnings.append("import_descriptor_safety_budget_reached")
            if not terminated and not warnings:
                warnings.append("import_table_not_null_terminated")

    return {
        "machine": machine, "architecture": "PE32+" if is64 else "PE32",
        "imagebase": imagebase, "entry_rva": entry_rva, "sections": sections,
        "imports": imports, "has_import_table": has_imports,
        "import_descriptors_read": descriptor_count,
        "import_descriptors_null_terminated": terminated,
        "import_parse_warnings": warnings,
        "_offset_for_rva": offset_for_rva,
    }


def byte_matches(data, needle, limit=12):
    positions = []
    at = 0
    while len(positions) < limit:
        at = data.find(needle, at)
        if at < 0:
            break
        positions.append(at)
        at += 1
    return positions


def file_inventory(folder):
    if not folder.is_dir():
        return {"present": False}
    # Enumerate names only; never read/write archives or recursively hash assets.
    bins = sorted(p.name for p in (folder / "Data").glob("*.bin") if p.is_file())
    top = [p for p in folder.iterdir() if p.is_file()]
    count = Counter(p.suffix.lower() for p in top)
    for sub in folder.iterdir():
        if sub.is_dir() and sub.name.lower() != "data":
            # Keep inventory bounded, avoid scanning unrelated subtrees.
            continue
    return {
        "present": True, "data_bin_count": len(bins),
        "data_bin_names": bins, "top_level_extensions": dict(sorted(count.items())),
        "known_ui_names": {
            name: any(p.name.lower() == name for p in top)
            for name in ("all_sys.tsw", "all_sys.act", "all_char.tsw", "all_char.act")
        },
    }


def analyze_bytes(data, game_folder=None):
    pe = parse_pe(data)
    imports = pe["imports"]
    imagebase = pe["imagebase"]
    wanted = [r for r in imports if r["api"] in INTERESTING_APIS]
    # An FF 15 + 32-bit absolute IAT VA is a possible x86 call [IAT] only.
    # Results are heuristic, not disassembly, and do not prove text conversion.
    xrefs = []
    if pe["architecture"] == "PE32":
        for imp in wanted:
            iat = imp["iat_va"]
            if iat > 0xFFFFFFFF:
                continue
            pattern = b"\xFF\x15" + struct.pack("<I", iat)
            matches = []
            for sec in pe["sections"]:
                if not sec["executable"]:
                    continue
                start, size = sec["file_offset"], sec["file_size"]
                if start >= len(data):
                    continue
                blob = data[start:min(start+size, len(data))]
                for offset in byte_matches(blob, pattern):
                    matches.append(hex(imagebase + sec["rva"] + offset))
            if matches:
                xrefs.append({"api": imp["api"], "dll": imp["dll"], "candidate_call_vas": matches})

    legacy = {}
    for label, va in LEGACY_VAS.items():
        rva = va - imagebase
        off = pe["_offset_for_rva"](rva) if rva >= 0 else None
        legacy[label] = {
            "va_historical": hex(va), "rva_at_this_imagebase": hex(rva) if rva >= 0 else None,
            "file_offset": off,
            "bytes_hex_at_location": data[off:off+16].hex() if off is not None else None,
            "status": "unverified_historical_hint_only",
        }
    encoded = {
        "SimSun_ASCII": b"SimSun",
        "Songti_GBK": "宋体".encode("cp936"),
        "Songti_UTF16LE": "宋体".encode("utf-16le"),
    }
    return {
        "schema_version": 1,
        "status": "static_diagnostic_only_not_a_patch",
        "file_size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "machine": hex(pe["machine"]), "architecture": pe["architecture"],
        "imagebase": hex(imagebase), "entry_rva": hex(pe["entry_rva"]),
        "sections": pe["sections"],
        "gdi_and_encoding_imports": wanted,
        "import_table_diagnostics": {
            "present": pe["has_import_table"],
            "descriptors_read": pe["import_descriptors_read"],
            "null_terminated": pe["import_descriptors_null_terminated"],
            "warnings": pe["import_parse_warnings"],
            "interpretation": "Partial or absent imports do not prove a drawing API is unused.",
        },
        "potential_x86_iat_calls": xrefs,
        "font_name_byte_offsets": {name: byte_matches(data, needle) for name, needle in encoded.items()},
        "historical_va_hints": legacy,
        "installation": file_inventory(game_folder) if game_folder is not None else None,
        "limitations": [
            "No file was modified or game launched.",
            "Static imports cannot establish which drawing API handles every text path.",
            "Historical VAs are not validated without matching the original executable hash/disassembly.",
            "GBK versus UTF-8 versus Unicode handling, line wrapping and font glyph coverage require runtime testing.",
            "This report does not authorize any executable patch or translation-name key changes.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Inspect EOA3 AngelSLG.exe and inventory game files without modifying them.")
    parser.add_argument("exe", type=Path, help="Path to AngelSLG.exe on your Windows game installation")
    parser.add_argument("--game-dir", type=Path, default=None, help="Game root, defaults to executable folder")
    parser.add_argument("--out", type=Path, default=None, help="Save report JSON; by default print to stdout")
    args = parser.parse_args()
    if not args.exe.is_file():
        parser.error("Executable not found")
    length = args.exe.stat().st_size
    if length > MAX_EXE_SIZE:
        parser.error("Executable is too large for the read-only probe")
    result = analyze_bytes(args.exe.read_bytes(), game_folder=args.game_dir or args.exe.parent)
    result["exe_filename"] = args.exe.name  # Avoid full path/account name in shareable report
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print("Created diagnostic report (no game file modified): %s" % args.out)
    else:
        print(text)


if __name__ == "__main__":
    main()
