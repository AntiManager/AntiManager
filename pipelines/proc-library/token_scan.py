#!/usr/bin/env python3
"""Client-token (de-identification) scan for the unified process library (T1.5).

Checks a vault `library/` folder for client-**identity** tokens per
`specs/T0.6-generalization-rule.md` (Decision 1, criterion *token-free*):
legal-entity names, monetary figures/targets, plant codes, and person names.
These FAIL the freeze gate.

Two further classes are reported as INFO (visible, but they do not fail):
  - SOURCE-REF  — structural cross-references to the client regulation layer
    (`REG-<n>`, `../reglaments/*`, `И <name>`, `ПС ПП`), deferred to Phase 4;
  - TOOL/BRAND  — generic industry tool references (`1С`, `АРМ`) and Latin
    tokens that are neither our codes nor a known acronym (possible equipment
    model / brand to review).

Usage:
  python token_scan.py <library_dir | file.md> [--json out.json]
Exit: 0 = clean, 1 = identity token(s) found, 2 = usage/IO error.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

HEAD_RE = re.compile(r"^(#{1,5})\s+(.*?)\s*$")
CODE_RE = re.compile(r"\b([A-Z][A-Z0-9_-]*-\d{2}(?:-\d{2})?(?:-\d{2})?)\b")
LEVEL = {1: "LIBRARY", 2: "GROUP", 3: "PROCESS", 4: "SUBPROCESS", 5: "OPERATION"}

# --- FAIL: client-identity tokens (T0.6 criterion 2) -----------------------
IDENTITY = {
    "legal-entity": re.compile(r"\b(?:ООО|ОАО|ЗАО|ПАО|АО|ГК|Холдинг|Group|GmbH|Ltd|Inc|LLC)\b"),
    "money-figure": re.compile(r"\d[\d\s\u00a0]*(?:тыс|млн|млрд)\.?\s*(?:руб|т\.?\s?р\.?)|\d[\d\s\u00a0]*₽"),
    "plant-code": re.compile(r"\bЗ-\d{2}\b|[Зз]авод\s*№\s*\d"),
    "person-name": re.compile(r"\b[А-ЯЁ]\.\s?[А-ЯЁ]\.\s?[А-ЯЁ][а-яё]+"),
}

# --- INFO: source-regulation cross-refs (not identity tokens; Phase 4) -----
SOURCE_REF = re.compile(r"REG-\d+|\.\./reglaments/|И Хранение|И 2\.6-01|Приложени[ея]\s+[А-Я]|ПС ПП")

# --- INFO: generic tools / possible brands ---------------------------------
TOOL = re.compile(r"\b1С\b|\bАРМ\b")

# Known generic acronyms / structural words (not brands). Everything else that
# is a Latin token of length >= 3 is reported for review.
ACRONYMS = {
    "ANLZ", "APQC", "ENG", "ENV", "HRP", "IMPR", "INF", "KPI", "MFG", "MNT",
    "ORG", "PLAN", "QUAL", "SLA", "SL", "STRAT", "EMG", "ERP", "OEE", "OPE",
    "TEEP", "SQDCPME", "VSM", "TPM", "SMED", "WMS", "FIFO", "GPS", "MSDS",
    "SSCC", "CAPA", "RCA", "PDCA", "RACI", "ISO", "TWI", "Kaizen", "WBS",
    "IRR", "NPV", "MTBF", "MTTR", "SCADA", "CAD", "ABC", "XYZ", "EOQ", "WIP",
    "ADR", "SOP", "QR", "KUP", "OLAP", "HR", "OTK", "TT", "SME", "A3",
    # structural / frontmatter / mermaid
    "draft", "status", "tags", "updated", "library", "group", "index", "plant",
    "process", "sme", "flowchart", "mermaid", "subgraph", "end", "Power",
    "Workshop", "Logistics", "Reverse", "Check", "lists", "analysis", "cause",
    "root", "olap", "analysed", "brainstorming", "gap",
    # lowercase frontmatter tags
    "anlz", "eng", "env", "hrp", "impr", "inf", "mnt", "org", "plan", "qual",
    "emg", "strat", "mfg", "sl",
}
# Schema enum vocabulary (T0.5/T0.6): operation `Тип`, `Горизонт`,
# `decomposition`, `Критичность`, `Матрица` values — not brands.
ENUM = {
    "Simple", "Splitter", "Joiner", "Multiplicator", "Aggregator",
    "shift", "day", "week", "month", "quarter", "year", "event",
    "decomposition", "ATOMIC", "DECOMPOSABLE", "PARTIALLY_DECOMPOSABLE",
    "FULL", "DIAGONAL", "CUSTOM", "high", "medium", "low",
}
LATIN = re.compile(r"\b[A-Za-z][A-Za-z0-9]{2,}\b")
LOWER_LATIN = re.compile(r"[a-z]")


def _iter_lines(path):
    text = io.open(path, encoding="utf-8").read()
    return text.split("\n")


def _scan_file(path):
    hits = {"identity": [], "info": []}
    depth, code = 0, "?"
    in_fm, in_fence, fm_seen = False, False, False
    for i, ln in enumerate(_iter_lines(path), 1):
        s = ln.strip()
        if s == "---" and not fm_seen and depth == 0:
            in_fm = not in_fm
            if not in_fm:
                fm_seen = True
            continue
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fm or in_fence:
            continue
        m = HEAD_RE.match(ln)
        if m:
            depth = len(m.group(1))
            cm = CODE_RE.search(m.group(2))
            code = cm.group(1) if cm else "?"
            continue
        where = f"{os.path.basename(path)}:{i} [{LEVEL.get(depth, '?')} {code}]"
        for label, pat in IDENTITY.items():
            mm = pat.search(ln)
            if mm:
                hits["identity"].append((where, label, mm.group(0), ln.strip()[:160]))
        if SOURCE_REF.search(ln):
            hits["info"].append((where, "SOURCE-REF", SOURCE_REF.search(ln).group(0),
                                 ln.strip()[:160]))
        if TOOL.search(ln):
            hits["info"].append((where, "TOOL", TOOL.search(ln).group(0),
                                 ln.strip()[:160]))
        for tok in LATIN.findall(ln):
            if tok in ACRONYMS or tok in ENUM or not LOWER_LATIN.search(tok):
                continue
            hits["info"].append((where, "possible-brand", tok, ln.strip()[:160]))
    return hits


def scan(target):
    files = []
    if os.path.isfile(target):
        files = [target]
    else:
        for root, _dirs, fs in os.walk(target):
            files += [os.path.join(root, f) for f in fs if f.endswith(".md")]
    files = sorted(files)
    out = {"identity": [], "info": [], "files": [os.path.basename(f) for f in files]}
    for f in files:
        h = _scan_file(f)
        out["identity"] += h["identity"]
        out["info"] += h["info"]
    return out


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    argv = list(sys.argv[1:] if argv is None else argv)
    jpath = None
    if "--json" in argv:
        j = argv.index("--json")
        jpath = argv[j + 1]
        del argv[j:j + 2]
    if len(argv) != 1:
        print("usage: token_scan.py <library_dir|file.md> [--json out.json]")
        return 2
    target = argv[0]
    if not os.path.exists(target):
        print(f"ERROR: path not found: {target}")
        return 2
    res = scan(target)
    print(f"scanned: {len(res['files'])} file(s)")
    print(f"IDENTITY tokens (fail): {len(res['identity'])}")
    for where, label, tok, line in res["identity"][:50]:
        print(f"  ! [{label}] {where}: {tok} :: {line}")
    print(f"INFO items (review): {len(res['info'])}")
    for where, label, tok, line in res["info"][:50]:
        print(f"  - [{label}] {where}: {tok}")
    if jpath:
        with io.open(jpath, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
    return 1 if res["identity"] else 0


if __name__ == "__main__":
    sys.exit(main())
