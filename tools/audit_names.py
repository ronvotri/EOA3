"""Static name-reference audit for EOA3 (stdlib only, does NOT alter game data).

Exact literal matches in parsed source are useful clues, NOT proof that the engine
doesn't look a name up in binary code or assets. The draft is never used by pack().
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT_PATH = ROOT / "translations" / "DISPLAY_NAMES_DRAFT.json"
DB_PATH = ROOT / "translations" / "DataBase.json"
CANDIDATE_FIELDS = {("AddGroundData", 1), ("AddSkillData", 1), ("AddItemData", 1), ("AddClassData", 2)}
EXPECTED = {"AddGroundData": 14, "AddSkillData": 63, "AddItemData": 58, "AddClassData": 360}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_draft(draft=None, database=None):
    draft = read(DRAFT_PATH) if draft is None else draft
    database = read(DB_PATH) if database is None else database
    if draft.get("status") != "draft_not_approved_for_runtime":
        raise ValueError("Draft must explicitly remain unapproved for runtime")
    if not isinstance(draft.get("entries"), list):
        raise ValueError("Missing draft entries")
    by_token = {row["token"]: row for row in database}
    if len(by_token) != len(database):
        raise ValueError("Duplicate database token")
    expected = {
        row["token"]: row for row in database
        if row["mode"] == "review" and (row["call"], row["argument"]) in CANDIDATE_FIELDS
    }
    got = {}
    for row in draft["entries"]:
        tok = row["token"]
        if tok in got or tok not in expected:
            raise ValueError("Duplicate or unauthorized draft token: %s" % tok)
        actual = expected[tok]
        for key in ("id", "token", "call", "argument", "source"):
            if row.get(key) != actual[key]:
                raise ValueError("Source mismatch in display draft %s field %s" % (tok, key))
        if not row.get("vi_draft", "").strip():
            raise ValueError("Blank draft label: %s" % tok)
        if row.get("risk") != "name_may_be_used_as_lookup_key":
            raise ValueError("Draft must preserve explicit lookup-risk marker: %s" % tok)
        got[tok] = row
    if got.keys() != expected.keys():
        raise ValueError("Draft coverage missing %s tokens" % len(expected.keys() - got.keys()))
    grouped = Counter(x["call"] for x in got.values())
    if dict(grouped) != EXPECTED:
        raise ValueError("Wrong audited field counts: %r" % dict(grouped))
    return grouped


def reference_report(database=None):
    database = read(DB_PATH) if database is None else database
    reviewed = [r for r in database if r["mode"] == "review"]
    names = defaultdict(list)
    for row in reviewed:
        names[row["source"]].append(row)
    refs = defaultdict(list)
    for path in sorted((ROOT / "source").glob("*.json")):
        doc = read(path)
        for index, token in enumerate(doc["tokens"]):
            if token[0] != 5:
                continue
            if token[1] not in names:
                continue
            matched = names[token[1]]
            if path.name == "DataBase.json" and any(r["token"] == index for r in matched):
                continue
            refs[token[1]].append({"file": path.name, "token": index})
    by_call = {}
    for call in sorted({r["call"] or "UNKNOWN" for r in reviewed}):
        subset = [r for r in reviewed if (r["call"] or "UNKNOWN") == call]
        distinct = {r["source"] for r in subset}
        by_call[call] = {
            "review_rows": len(subset),
            "unique_literals": len(distinct),
            "rows_with_other_exact_literals": sum(bool(refs[r["source"]]) for r in subset),
            "unique_literals_with_other_exact_literals": sum(bool(refs[x]) for x in distinct),
        }
    return {
        "caution": "Only exact matches among decoded token strings. Zero matches does NOT prove a name is safe to rename; engine-level lookup and images have not been inspected.",
        "files_scanned": len(list((ROOT / "source").glob("*.json"))),
        "review_rows_scanned": len(reviewed),
        "by_call": by_call,
        "literal_examples": [
            {"source": name, "references": refs[name][:12]}
            for name in sorted(refs) if refs[name]
        ][:50],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("check", "report"), nargs="?", default="check")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    verified = verify_draft()
    info = reference_report()
    if info["review_rows_scanned"] != 573:
        raise SystemExit("Expected 573 DataBase review rows, found %s" % info["review_rows_scanned"])
    print("PASS: 495 draft labels (14 terrain, 63 skills, 58 items, 360 class records); all keys still review.")
    print("Static reference scan: %s files; %s unapproved database name rows." %
          (info["files_scanned"], info["review_rows_scanned"]))
    for call, status in info["by_call"].items():
        print("%s: %s review rows, %s names have another exact literal occurrence" %
              (call, status["review_rows"], status["rows_with_other_exact_literals"]))
    if args.command == "report":
        out = args.out or (ROOT / "build" / "name_reference_report.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Wrote static reference report: %s" % out)


if __name__ == "__main__":
    main()
