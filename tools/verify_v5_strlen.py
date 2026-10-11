"""Verify V5's real x86 byte-length helper, with NO game execution/patch.

Requires only the existing six-file EOA3 diagnostic ZIP. Anchors to the exact
AngelSLG.exe SHA, imported TextOutA callsite, small function/data SHA-256 and
several independent x86 instruction signatures before assigning semantics.
"""
import argparse
import hashlib
import json
from pathlib import Path

from analyze_windows_report import analyze_reports, read_zip
from inspect_textout_args import attest_windows
from probe_engine_calls import REFERENCE_EXE_SHA256

HELPER_VA = "0x4ce790"
SPACE_VA = "0x4f2b38"
HELPER_WINDOW_SHA256 = "2d06c948ce8060b68cb73d0d06f2b2cf08d561f7ddb5a5ac1860e02e752c8c21"
HELPER_FUNCTION_SHA256 = "ee3a394138000e43710e1f46da55d9eed3240ac7510488da765689c5aea446c7"
SPACES_WINDOW_SHA256 = "8e8a8af6d93387203012ad120b92a57a1fa55b27a6efef6d940f2528b7dbbadf"
HELPER_FUNCTION_LENGTH = 0x7B
RET_OFFSETS = (0x5C, 0x66, 0x70, 0x7A)


def verify_helper(raw):
    """Recognize the *specific* CRT-like word-at-a-time strlen x86 function."""
    if len(raw) != 192:
        return False
    if hashlib.sha256(raw).hexdigest() != HELPER_WINDOW_SHA256:
        return False
    if hashlib.sha256(raw[:HELPER_FUNCTION_LENGTH]).hexdigest() != HELPER_FUNCTION_SHA256:
        return False
    signatures = {
        0x00: bytes.fromhex("8b4c2404f7c103000000"),  # mov ecx, [esp+4]; test ecx,3
        0x0C: bytes.fromhex("8a014184c0"),          # mov al,[ecx]; inc ecx; test al,al
        0x20: bytes.fromhex("8b01bafffefe7e"),      # dword load + zero-byte detection constant
        0x53: bytes.fromhex("8d41ff8b4c24042bc1c3"),  # pointer-minus-start return, last-byte case
        0x5D: bytes.fromhex("8d41fe8b4c24042bc1c3"),
        0x67: bytes.fromhex("8d41fd8b4c24042bc1c3"),
        0x71: bytes.fromhex("8d41fc8b4c24042bc1c3"),
        0x7B: bytes.fromhex("cccccccccc"),         # function boundary padding
    }
    if any(raw[offset:offset+len(token)] != token for offset, token in signatures.items()):
        return False
    return all(raw[off] == 0xC3 for off in RET_OFFSETS)


def inspect_v5_docs(docs):
    metadata = analyze_reports(docs)
    evidence = docs.get("engine_callsite_slices.json")
    if evidence is None:
        raise ValueError("V5 six-file diagnostic ZIP is required")
    if metadata["game_exe"]["sha256"] != REFERENCE_EXE_SHA256:
        raise ValueError("Not the verified AngelSLG.exe build")
    if not evidence.get("matches_documented_exe_sha256"):
        raise ValueError("The engine evidence was not collected against the verified build")
    args = attest_windows(evidence)
    records = evidence.get("dependent_code_targets", [])
    targets = {
        obj.get("va", "").lower(): obj
        for obj in records if isinstance(obj, dict)
    }
    observations = {}
    for address, expected_len, expected_sha, is_code in (
        (HELPER_VA, 192, HELPER_WINDOW_SHA256, True),
        (SPACE_VA, 16, SPACES_WINDOW_SHA256, False),
    ):
        item = targets.get(address)
        if item is None:
            raise ValueError("Missing V5 dependent evidence at " + address)
        try:
            raw = bytes.fromhex(item["bytes_hex"])
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("Bad evidence bytes at " + address) from exc
        valid = (
            len(raw) == expected_len
            and item.get("byte_count") == expected_len
            and item.get("bytes_sha256") == hashlib.sha256(raw).hexdigest()
            and item.get("bytes_sha256") == expected_sha
            and item.get("truncated_to_section_boundary") is False
            and item.get("section") == (".text" if is_code else ".rdata")
        )
        if not valid:
            raise ValueError("Code/data evidence mismatch at " + address)
        observations[address] = raw

    helper_is_strlen = verify_helper(observations[HELPER_VA])
    two_spaces = observations[SPACE_VA][:4] == b"  \x00\x00"
    if args["verified_sites"] != args["expected_sites"]:
        raise ValueError("TextOutA/CreateFontIndirectA site signatures not fully verified")
    if not helper_is_strlen or not two_spaces:
        raise ValueError("V5 machine-code signatures are not the expected helper/data")
    return {
        "schema_version": 1,
        "status": "verified_v5_static_byte_strlen_and_spaces_not_a_game_patch",
        "exe_sha256": REFERENCE_EXE_SHA256,
        "evidence": {
            "helper_va": HELPER_VA,
            "helper_function_length_bytes": HELPER_FUNCTION_LENGTH,
            "helper_function_sha256": HELPER_FUNCTION_SHA256,
            "helper_semantics": "strlen: return number of 8-bit bytes before first NUL (0x00)",
            "helper_uses_4_byte_fast_scan": True,
            "first_textout_constant_va": SPACE_VA,
            "first_textout_constant": "two ASCII spaces (0x20 0x20), then NUL",
            "textout_call_sites": [r["site_va"] for r in args["entries"] if r["api"] == "TextOutA"],
            "textout_dynamic_length_unit": "bytes; not UTF-16 code units",
            "font_charset": 134,
        },
        "encoding_examples": [
            {
                "text": v,
                "characters": len(v),
                "utf8_bytes": len(v.encode("utf-8")),
                "utf16le_code_units": len(v.encode("utf-16le")) // 2,
                "cp936_encodable": _is_cp936(v),
            }
            for v in ("Việt", "được", "你好")
        ],
        "limitations": [
            "The helper is recognized from exact x86 code, not executed in the running game.",
            "These TextOutA sites might draw to an offscreen DC/glyph cache, not directly to the dialogue UI.",
            "This does not identify how ANGELSCRIPT text reaches the caller or how control codes are processed.",
            "TextOutW replacement without converting LPCSTR data and length to UTF-16 is unsafe.",
            "No executable/game asset was modified or distributed.",
        ],
    }


def _is_cp936(value):
    try:
        value.encode("cp936")
        return True
    except UnicodeEncodeError:
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate V5 EOA3 helper and two-space constant from diagnostic ZIP")
    parser.add_argument("report_zip", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = inspect_v5_docs(read_zip(args.report_zip))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print("Verified static V5 helper summary:", args.out)
    else:
        print(output)


if __name__ == "__main__":
    main()
