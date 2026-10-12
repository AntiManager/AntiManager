"""Summarise a process-engine JSON report, scoped to code prefixes.

Usage:
  python -X utf8 engine_filter.py <report.json> <PREFIX> [<PREFIX> ...]

Prints per-rule error/warning counts and the list of node codes with findings,
restricted to messages whose referenced node code starts with a given prefix.
"""
import json
import re
import sys

CODE_RE = re.compile(r"\b([A-Z][A-Z0-9_]*(?:-[0-9]{2})+)\b")


def rules_of(msg: str) -> str:
    if msg.startswith("MISSING GOAL"):
        return "MISSING GOAL"
    if msg.startswith("FREE-TEXT"):
        return "FREE-TEXT"
    if msg.startswith("UNKNOWN TYPE"):
        return "UNKNOWN TYPE"
    if msg.startswith("DANGLING output"):
        return "DANGLING output"
    if msg.startswith("DANGLING input"):
        return "DANGLING input"
    if msg.startswith("FLOW CONSERVATION"):
        return "FLOW CONSERVATION"
    if msg.startswith("ISOLATED"):
        return "ISOLATED"
    if msg.startswith("POSSIBLE DUPLICATE"):
        return "POSSIBLE DUPLICATE"
    if msg.startswith("TYPE-CARDINALITY"):
        return "TYPE-CARDINALITY"
    if msg.startswith("OPERATION") or msg.startswith("SUBPROCESS") or msg.startswith("PROCESS"):
        return msg.split("(")[0].strip()
    return msg.split(":")[0].strip()


SUBJECT_RES = (
    re.compile(r"^MISSING GOAL on ([A-Z][A-Z0-9_-]*(?:-[0-9]{2})*)\b"),
    re.compile(r"^MISSING APQC on PROCESS ([A-Z][A-Z0-9_-]*(?:-[0-9]{2})*)\b"),
    re.compile(r"FREE-TEXT I/O on ([A-Z][A-Z0-9_-]*(?:-[0-9]{2})+)\b"),
    re.compile(r"UNKNOWN TYPE '[^']*' on ([A-Z][A-Z0-9_-]*(?:-[0-9]{2})+)\b"),
    re.compile(r"^DANGLING (?:output|input) ([A-Z][A-Z0-9_-]*(?:-[0-9]{2})+)\."),
    re.compile(r"^FLOW CONSERVATION on ([A-Z][A-Z0-9_-]*(?:-[0-9]{2})+)\b"),
    re.compile(r"^ISOLATED OPERATION ([A-Z][A-Z0-9_-]*(?:-[0-9]{2})+)\b"),
    re.compile(r"^POSSIBLE DUPLICATE: ([A-Z][A-Z0-9_-]*(?:-[0-9]{2})+)\b"),
    re.compile(r"TYPE-CARDINALITY mismatch on ([A-Z][A-Z0-9_-]*(?:-[0-9]{2})+)\b"),
    re.compile(r"^DUPLICATE CODE ([A-Z][A-Z0-9_-]*(?:-[0-9]{2})*)\b"),
)


def subject_code(m: str):
    for rx in SUBJECT_RES:
        mm = rx.search(m)
        if mm:
            return mm.group(1)
    return None


def scoped(messages, prefixes):
    out = []
    for m in messages:
        code = subject_code(m)
        if not prefixes:
            out.append(m)
        elif code and any(code.startswith(p) for p in prefixes):
            out.append(m)
    return out


def main() -> int:
    args = sys.argv[1:]
    listing = "--list" in args
    args = [a for a in args if a != "--list"]
    report = args[0]
    prefixes = args[1:]
    data = json.load(open(report, encoding="utf-8"))
    errs = scoped(data.get("errors", []), prefixes)
    warns = scoped(data.get("warnings", []), prefixes)

    for label, msgs in (("ERRORS", errs), ("WARNINGS", warns)):
        counts = {}
        codes = set()
        for m in msgs:
            counts[rules_of(m)] = counts.get(rules_of(m), 0) + 1
            code = subject_code(m)
            if code and any(code.startswith(p) for p in prefixes):
                codes.add(code)
        print(f"{label}: {len(msgs)}  nodes={len(codes)}")
        for k, v in sorted(counts.items()):
            print(f"  {k}: {v}")
        if listing:
            for m in msgs:
                print("    | " + m.encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
