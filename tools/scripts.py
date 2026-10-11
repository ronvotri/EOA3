"""Python 3.9+, standard library only. Run from any directory."""
import argparse, hashlib, json, re, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CONTROL = re.compile(r"%[A-Za-z](?:[+-]?\d+)?")
SAFE_CALLS = {"Say", "MessageBox", "SetMission", "SetStageName"}
# Manually audited text parameters: not names/IDs used as cross-resource lookup keys.
# SP_AddAction argument 3 = cutscene overlay; skills/items argument 2 = tooltip text.
AUDITED_TEXT_FIELDS = {("SP_AddAction", 3), ("AddSkillData", 2), ("AddItemData", 2)}
OVERLAY_PREFIX = re.compile(r"^%s\\d+%t\\d+%z\\d+")


def is_safe_text_field(row):
    if row["call"] in SAFE_CALLS:
        return True
    field = (row["call"], row["argument"])
    if field not in AUDITED_TEXT_FIELDS:
        return False
    if row["call"] == "SP_AddAction":
        return bool(OVERLAY_PREFIX.match(row["source"]))
    # Descriptions have no display control prefix. Their adjacent name
    # parameters remain non-translatable pending key-reference analysis.
    return not row["source"].startswith("%")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def pack(doc, replacements=None):
    replacements = replacements or {}
    out = bytearray(b"ANGELSCRIPT") + struct.pack("<I", doc["version"])
    def string(value):
        encoded = value.encode("cp936", errors="strict")
        return struct.pack("<H", len(encoded)) + encoded
    for table in doc["tables"]:
        out += struct.pack("<H", len(table))
        for value in table:
            out += string(value)
    for index, (kind, value) in enumerate(doc["tokens"]):
        out.append(kind)
        if kind in (1, 2, 3, 4, 8):
            out.append(value)
        elif kind == 5:
            out += string(replacements.get(index, value))
        elif kind in (6, 7):
            out += bytes.fromhex(value)
        else:
            raise ValueError(f"Unknown token {kind}")
    return bytes(out)

def validate_rows(doc, rows):
    seen = set()
    replacements = {}
    for row in rows:
        index = row["token"]
        if index in seen:
            raise ValueError(f"Duplicate token {index}")
        seen.add(index)
        if doc["tokens"][index] != [5, row["source"]]:
            raise ValueError(f"Source mismatch: {row['id']}")
        text = row["vi"]
        if not isinstance(text, str):
            raise ValueError(f"vi must be a string: {row['id']}")
        if not text:
            continue
        if row["mode"] != "translate" or not is_safe_text_field(row):
            raise ValueError(f"Requires separate semantic review: {row['id']}")
        if CONTROL.findall(text) != CONTROL.findall(row["source"]):
            raise ValueError(f"Control codes changed: {row['id']}")
        if "\x00" in text:
            raise ValueError(f"NUL forbidden: {row['id']}")
        replacements[index] = text
    expected = {i for i, t in enumerate(doc["tokens"]) if t[0] == 5}
    if seen != expected:
        raise ValueError("Missing or extra string rows")
    return replacements

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["check", "roundtrip", "build"])
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "Data")
    args = parser.parse_args()
    staged = []
    translated = 0
    for path in sorted((ROOT / "source").glob("*.json")):
        doc = read(path)
        original = pack(doc)
        if hashlib.sha256(original).hexdigest() != doc["sha256"]:
            raise ValueError(f"Original reconstruction failed: {path.name}")
        replacements = validate_rows(doc, read(ROOT / "translations" / path.name))
        translated += len(replacements)
        try:
            result = pack(doc, replacements) if args.command == "build" else original
        except UnicodeEncodeError as exc:
            raise SystemExit(f"{path.name}: Vietnamese requires the pending font/encoding patch. "
                             "UTF-8 translation is saved safely; no lossy build is allowed.") from exc
        staged.append((path.stem + ".bin", result))
    if args.command in ("build", "roundtrip"):
        args.out.mkdir(parents=True, exist_ok=True)
        for name, data in staged:
            (args.out / name).write_bytes(data)
    print(f"OK: {len(staged)} scripts, original SHA-256 verified; {translated} translations validated.")
    if args.command == "build":
        print("Legacy GBK build only. Runtime/font/line wrapping still need Windows testing.")

if __name__ == "__main__":
    main()
