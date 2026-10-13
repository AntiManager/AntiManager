#!/usr/bin/env python3
"""Artifact-chain conformance checker (plans 1791810263662, Phase A/E).

Validates the three management artifacts under `<vault>/library/artifacts/`
against the canonical role register (specs/T4.0 + role_registry.json) and the
machine-readable format contract (specs/T4.9). The artifacts are not
ProcessNode trees, so this is a SEPARATE checker: it imports `engine.py` for
process/code resolution and `token_scan.py` for identity-token classes, and it
does NOT extend the ontology validator.

Hard checks (always):
  H1a  artifact role codes are a non-empty subset of the register
  H1b  recognized-kind artifact declares a 'roles:' frontmatter key (T4.9 §2)
  H2   every referenced process code resolves to a library node
  H3   every grid event has a non-empty Горизонт (in the allowed vocabulary)
  H4   each event's Горизонт matches its section cadence
  H5   every КТК row has keystone ∈ {да,—} and Критичность ∈ {high,medium,low}
  H6   client/holding stop-word scan over artifacts = 0
  H7   every artifact row references ≥1 valid process code (gaps = 0)
  +    exact table-header match (T4.9)

Cross-document (--cross):
  H1   role sets identical across the three artifact kinds = register (10)
  W1   a role's keystone code appears in that role's matrix or grid
  W2   a grid event's process codes have the owner role in the library
  W6   no duplicate (role, process) КТК rows

Semantic (--semantic):
  W3   Делегирование non-empty for the two «not important» quadrants
  W4   every numeric KPI marked «ориентир»
  W5   every keystone = да has a non-empty «Обоснование keystone»

Usage:
  python check_artifacts.py <vault> [--cross] [--semantic] [--json out.json]
Exit: 0 = no H-violations, 1 = H-violation(s), 2 = usage/IO error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import engine  # noqa: E402
import token_scan  # noqa: E402

REGISTRY_DEFAULT = os.path.join(HERE, "role_registry.json")

KINDS = ("ktk", "priority-matrix", "event-grid")

KTK_HEADER = ["№", "Код процесса", "Роль", "keystone", "Критический выход",
              "KPI/критерий", "Частота контроля", "Источник данных",
              "Критичность", "Обоснование keystone"]
MATRIX_HEADER = ["Квадрант", "Задача", "Тип", "Делегирование",
                 "Профилактика / автоматизация", "Связанный процесс (код)"]
GRID_HEADER = ["Триггер/Период", "Событие", "Длительность", "Владелец",
               "Участники", "Повестка", "Вход", "Выход", "Процессы", "Горизонт"]

HEADERS = {
    "ktk": KTK_HEADER,
    "priority-matrix": MATRIX_HEADER,
    "event-grid": GRID_HEADER,
}
HEADER_KEY = {"|".join(v): k for k, v in HEADERS.items()}
CODE_COL = {"ktk": "Код процесса", "priority-matrix": "Связанный процесс (код)",
            "event-grid": "Процессы"}

HORIZONS = {"shift", "day", "week", "month", "quarter", "year", "event"}
KEYSTONE_OK = {"да", "—", "-", "–"}

HEAD_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
ROLE_HEAD_RE = re.compile(r"^##\s+.*?\(([^()]+)\)\s*$")
FM_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*?)\s*$")
PROC_CODE_RE = re.compile(r"\b[A-Z][A-Z0-9_-]*-\d{2}(?:-\d{2})*\b")
SEP_RE = re.compile(r"^\|[\s:\-|]+\|?\s*$")
ROLES_LIST_RE = re.compile(r"^\[(.*)\]$")

SECT_HORIZON = [
    (re.compile(r"ежедневн|daily", re.I), {"shift", "day"}),
    (re.compile(r"еженедельн|weekly|недел", re.I), {"week"}),
    (re.compile(r"ежемесячн|monthly|месяц", re.I), {"month"}),
    (re.compile(r"ежеквартальн|quarterly|квартал", re.I), {"quarter"}),
    (re.compile(r"ежегодн|yearly|annual|годов|\bгод", re.I), {"year"}),
]

# Client + holding stop-words (umbrella §5, T4.0 removal list). H6 fails if any.
STOPWORDS = [
    (re.compile(r"\bУК\b"), "holding-УК"),
    (re.compile(r"\bТД\b|Торговый дом"), "holding-ТД"),
    (re.compile(r"давальческ"), "holding-давальческая схема"),
    (re.compile(r"\bПУ\b"), "client-ПУ"),
    (re.compile(r"ПС ПП"), "client-ПС ПП"),
    (re.compile(r"ФРПС"), "client-ФРПС"),
    (re.compile(r"\bСГИ\b"), "holding-СГИ"),
    (re.compile(r"\bСГМ\b"), "holding-СГМ"),
    (re.compile(r"\bУПЛ\b"), "holding-УПЛ"),
    (re.compile(r"\bУСИС\b"), "holding-УСИС"),
    (re.compile(r"\bЦСМ\b"), "holding-ЦСМ"),
    (re.compile(r"Росприроднадзор"), "client-Росприроднадзор"),
    (re.compile(r"2-ТП"), "client-2-ТП"),
    (re.compile(r"REG-\d+"), "source-REG"),
    (re.compile(r"Proc_lib"), "source-Proc_lib"),
    (re.compile(r"Приоритеты_руководителей"), "source-matrix-xref"),
    (re.compile(r"Power\s*BI"), "tool-PowerBI"),
    (re.compile(r"Регламент\s*8\.\d"), "source-reglament-8"),
    (re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b"), "hard-date"),
]


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------
def load_registry(path=REGISTRY_DEFAULT):
    with open(path, encoding="utf-8") as f:
        reg = json.load(f)
    reg["codes"] = [r["code"] for r in reg["roles"]]
    reg["code_set"] = set(reg["codes"])
    # ordered (needle_lower, code) index over the three mapping tables; earlier
    # entries win for single-code resolution (role_for_string).
    idx = []
    for r in reg["roles"]:
        for syn in r["owner_synonyms"]:
            idx.append((syn.lower(), r["code"]))
    for fm in reg.get("fold_map", []):
        for code in fm["to"]:
            idx.append((fm["source"].lower(), code))
    for em in reg.get("event_owner_map", []):
        for code in em["to"]:
            idx.append((em["source"].lower(), code))
    reg["_match_index"] = idx
    return reg


def roles_for_string(reg, s):
    """Map a free-text owner/actor string to ALL matching canonical role codes.

    Consults owner synonyms, the fold map and the event-owner map (umbrella §5);
    a string that matches no role maps to [] (a worker / unmapped participant).
    """
    low = (s or "").lower()
    if not low.strip():
        return []
    out = []
    for needle, code in reg["_match_index"]:
        if needle and needle in low and code not in out:
            out.append(code)
    return out


def role_for_string(reg, s):
    """Single-code view of roles_for_string (first/highest-priority match or None)."""
    r = roles_for_string(reg, s)
    return r[0] if r else None


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------
def _hkey(line):
    return "|".join(c.strip() for c in line.strip().strip("|").split("|"))


def parse_frontmatter(lines):
    data = {}
    if not lines or lines[0].strip() != "---":
        return data, 0
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        m = FM_RE.match(lines[i])
        if m:
            data[m.group(1)] = m.group(2)
        i += 1
    return data, i + 1


def _fm_roles(value):
    m = ROLES_LIST_RE.match((value or "").strip())
    if not m:
        return []
    return [c.strip() for c in m.group(1).split(",") if c.strip()]


def parse_file(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    fm, start = parse_frontmatter(lines)
    kind = fm.get("artifact")
    out = {
        "path": path,
        "kind": kind if kind in KINDS else None,
        "has_roles_fm": "roles" in fm,
        "fm_roles": _fm_roles(fm.get("roles")),
        "heading_roles": [],
        "tables": [],
        "text": "\n".join(lines),
        "lines": lines,
    }
    heading = None
    role = None
    i = start
    while i < len(lines):
        ln = lines[i]
        hm = HEAD_RE.match(ln)
        if hm:
            heading = hm.group(2).strip()
            rm = ROLE_HEAD_RE.match(ln)
            role = rm.group(1).strip() if rm else None
            if role:
                out["heading_roles"].append(role)
            i += 1
            continue
        key = _hkey(ln)
        if key in HEADER_KEY:
            tkind = HEADER_KEY[key]
            j = i + 1
            if j < len(lines) and SEP_RE.match(lines[j].strip()):
                j += 1
            rows = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                if any(cells):
                    rows.append(cells)
                j += 1
            out["tables"].append({"kind": tkind, "header": HEADERS[tkind],
                                  "rows": rows, "heading": heading, "role": role})
            i = j
            continue
        i += 1
    return out


def collect_artifacts(vault):
    base = os.path.join(vault, "library", "artifacts")
    files = []
    if os.path.isdir(base):
        for root, _dirs, fs in os.walk(base):
            files += [os.path.join(root, f) for f in fs if f.endswith(".md")]
    return sorted(files)


def _col(table, name):
    try:
        return table["header"].index(name)
    except ValueError:
        return None


def cell(row, idx):
    return row[idx].strip() if idx is not None and idx < len(row) else ""


def proc_codes(text):
    """Process codes in a cell, excluding source-ref tokens (REG-<n>; handled by H6)."""
    return [c for c in PROC_CODE_RE.findall(text) if not c.startswith("REG-")]


# --------------------------------------------------------------------------
# Library role resolution (W2)
# --------------------------------------------------------------------------
def _node_role_codes(reg, node):
    codes = set()

    def add(s):
        codes.update(roles_for_string(reg, s))

    def rec(n):
        if n.level == "OPERATION":
            add(n.attrs.get("Исполнитель", ""))
        else:
            add(n.attrs.get("Владелец", ""))
        for ch in n.children:
            rec(ch)

    rec(node)
    return codes


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------
def check_structure(reg, artifacts, lib):
    """Hard checks on the present artifact files. Returns (errors, warnings)."""
    errors, warnings = [], []

    for a in artifacts:
        if a["kind"] is None:
            continue
        base = os.path.basename(a["path"])

        # H1b: recognized-kind artifact declares roles in frontmatter (T4.9 §2)
        if not a["has_roles_fm"]:
            errors.append(f"H1b {base}: frontmatter missing required 'roles:' key (T4.9)")

        # H1a: role codes ⊆ register, non-empty
        rset = set(a["fm_roles"]) | set(a["heading_roles"])
        if not rset:
            errors.append(f"H1a {base}: no role codes (frontmatter roles / role headings)")
        bad = rset - reg["code_set"]
        if bad:
            errors.append(f"H1a {base}: unknown role code(s) {sorted(bad)}")

        # H6: stop-word scan
        for ln_no, ln in enumerate(a["lines"], 1):
            for pat, label in STOPWORDS:
                m = pat.search(ln)
                if m:
                    errors.append(f"H6 {base}:{ln_no}: stop-word [{label}] '{m.group(0)}'")
            for label, pat in token_scan.IDENTITY.items():
                m = pat.search(ln)
                if m:
                    # A money figure is allowed when explicitly marked «ориентир»
                    # (T4.0 removal list: hard targets "drop or mark ориентир").
                    if label == "money-figure" and "ориентир" in ln.lower():
                        continue
                    errors.append(f"H6 {base}:{ln_no}: identity [{label}] '{m.group(0)}'")

        if a["kind"] == "ktk":
            if len(a["heading_roles"]) != 1:
                errors.append(f"H1a {base}: КТК needs exactly one role heading "
                              f"(found {len(a['heading_roles'])})")
            ktk_tables = [t for t in a["tables"] if t["kind"] == "ktk"]
            if not ktk_tables:
                errors.append(f"H1a {base}: no КТК table matching the contract header")
            for t in ktk_tables:
                c_code = _col(t, "Код процесса")
                c_key = _col(t, "keystone")
                c_crit = _col(t, "Критичность")
                c_kpi = _col(t, "KPI/критерий")
                c_just = _col(t, "Обоснование keystone")
                for r_no, row in enumerate(t["rows"], 1):
                    raw = cell(row, c_code)
                    codes = proc_codes(raw)
                    if not codes:
                        errors.append(f"H7 {base}: КТК row {r_no}: no process code")
                    for code in codes:
                        if code not in lib.by_code:
                            errors.append(f"H2 {base}: КТК row {r_no}: code {code} "
                                          f"not in library")
                    ks = cell(row, c_key)
                    if ks.lower() not in KEYSTONE_OK:
                        errors.append(f"H5 {base}: КТК row {r_no}: keystone '{ks}'")
                    crit = cell(row, c_crit)
                    if crit not in engine.VALID_CRITICALITY:
                        errors.append(f"H5 {base}: КТК row {r_no}: Критичность '{crit}'")

        elif a["kind"] == "priority-matrix":
            m_tables = [t for t in a["tables"] if t["kind"] == "priority-matrix"]
            if not m_tables:
                errors.append(f"H1a {base}: no matrix table matching the contract header")
            for t in m_tables:
                c_code = _col(t, "Связанный процесс (код)")
                for r_no, row in enumerate(t["rows"], 1):
                    codes = proc_codes(cell(row, c_code))
                    if not codes:
                        errors.append(f"H7 {base}: matrix row {r_no}: no process code")
                    for code in codes:
                        if code not in lib.by_code:
                            errors.append(f"H2 {base}: matrix row {r_no}: code {code} "
                                          f"not in library")

        elif a["kind"] == "event-grid":
            g_tables = [t for t in a["tables"] if t["kind"] == "event-grid"]
            if not g_tables:
                errors.append(f"H1a {base}: no grid table matching the contract header")
            for t in g_tables:
                c_code = _col(t, "Процессы")
                c_hz = _col(t, "Горизонт")
                allowed = None
                for pat, hs in SECT_HORIZON:
                    if t["heading"] and pat.search(t["heading"]):
                        allowed = hs
                        break
                if t["rows"] and t["heading"] and allowed is None:
                    warnings.append(f"{base}: grid section '{t['heading']}' cadence "
                                    f"unrecognized; H4 not applied to it")
                for r_no, row in enumerate(t["rows"], 1):
                    hz = cell(row, c_hz)
                    if not hz:
                        errors.append(f"H3 {base}: grid row {r_no}: empty Горизонт")
                    elif hz not in HORIZONS:
                        errors.append(f"H3 {base}: grid row {r_no}: Горизонт '{hz}' "
                                      f"not in vocabulary")
                    elif allowed is not None and hz not in allowed:
                        errors.append(f"H4 {base}: grid row {r_no}: Горизонт '{hz}' "
                                      f"vs section ({sorted(allowed)})")
                    codes = proc_codes(cell(row, c_code))
                    if not codes:
                        errors.append(f"H7 {base}: grid row {r_no}: no process code")
                    for code in codes:
                        if code not in lib.by_code:
                            errors.append(f"H2 {base}: grid row {r_no}: code {code} "
                                          f"not in library")

    return errors, warnings


def check_cross(reg, artifacts, lib):
    errors, warnings = [], []
    present = {}
    for a in artifacts:
        if a["kind"]:
            present.setdefault(a["kind"], []).append(a)

    for kind in KINDS:
        if kind not in present:
            errors.append(f"H1 cross: artifact kind '{kind}' missing")

    for kind, files in present.items():
        rset = set()
        for a in files:
            rset |= set(a["fm_roles"]) | set(a["heading_roles"])
        if rset != reg["code_set"]:
            miss = sorted(reg["code_set"] - rset)
            extra = sorted(rset - reg["code_set"])
            errors.append(f"H1 cross: {kind} role set != register "
                          f"(missing={miss}, extra={extra})")

    # W6: duplicate (role, process) КТК rows
    seen = {}
    for a in present.get("ktk", []):
        base = os.path.basename(a["path"])
        role = a["heading_roles"][0] if a["heading_roles"] else "?"
        for t in [t for t in a["tables"] if t["kind"] == "ktk"]:
            c_code = _col(t, "Код процесса")
            for row in t["rows"]:
                for code in proc_codes(cell(row, c_code)):
                    k = (role, code)
                    if k in seen:
                        warnings.append(f"W6 duplicate (role,process) {role}/{code} "
                                        f"in {base} and {seen[k]}")
                    seen[k] = base

    # W1: keystone codes should appear in that role's matrix or grid
    matrix_codes_by_role = {}
    for a in present.get("priority-matrix", []):
        for t in [t for t in a["tables"] if t["kind"] == "priority-matrix"]:
            c_code = _col(t, "Связанный процесс (код)")
            for row in t["rows"]:
                for code in proc_codes(cell(row, c_code)):
                    matrix_codes_by_role.setdefault(t["role"], set()).add(code)
    grid_codes_by_role = {}
    for a in present.get("event-grid", []):
        for t in [t for t in a["tables"] if t["kind"] == "event-grid"]:
            c_code = _col(t, "Процессы")
            c_own = _col(t, "Владелец")
            for row in t["rows"]:
                roles = roles_for_string(reg, cell(row, c_own))
                if not roles:
                    continue
                for code in proc_codes(cell(row, c_code)):
                    for role in roles:
                        grid_codes_by_role.setdefault(role, set()).add(code)
    for a in present.get("ktk", []):
        role = a["heading_roles"][0] if a["heading_roles"] else "?"
        for t in [t for t in a["tables"] if t["kind"] == "ktk"]:
            c_code = _col(t, "Код процесса")
            c_key = _col(t, "keystone")
            for row in t["rows"]:
                if cell(row, c_key).lower() != "да":
                    continue
                for code in proc_codes(cell(row, c_code)):
                    pool = matrix_codes_by_role.get(role, set()) | \
                        grid_codes_by_role.get(role, set())
                    if code not in pool:
                        warnings.append(f"W1 keystone {role}/{code} not in that "
                                        f"role's matrix or grid")

    # W2: grid event codes should have the owner role in the library
    for a in present.get("event-grid", []):
        base = os.path.basename(a["path"])
        for t in [t for t in a["tables"] if t["kind"] == "event-grid"]:
            c_code = _col(t, "Процессы")
            c_own = _col(t, "Владелец")
            for r_no, row in enumerate(t["rows"], 1):
                roles = set(roles_for_string(reg, cell(row, c_own)))
                if not roles:
                    continue
                for code in proc_codes(cell(row, c_code)):
                    node = lib.by_code.get(code)
                    if node is None:
                        continue
                    if not (roles & _node_role_codes(reg, node)):
                        warnings.append(f"W2 {base}: grid row {r_no}: "
                                        f"{sorted(roles)} not a library "
                                        f"Владелец/Исполнитель of {code}")
    return errors, warnings


def check_semantic(reg, artifacts, lib):
    warnings = []
    for a in artifacts:
        base = os.path.basename(a["path"])
        if a["kind"] == "ktk":
            for t in [t for t in a["tables"] if t["kind"] == "ktk"]:
                c_key = _col(t, "keystone")
                c_kpi = _col(t, "KPI/критерий")
                c_just = _col(t, "Обоснование keystone")
                for r_no, row in enumerate(t["rows"], 1):
                    ks = cell(row, c_key)
                    if ks.lower() == "да" and not cell(row, c_just):
                        warnings.append(f"W5 {base}: КТК row {r_no}: keystone=да "
                                        f"without justification")
                    kpi = cell(row, c_kpi)
                    if re.search(r"\d", kpi) and "ориентир" not in kpi.lower():
                        warnings.append(f"W4 {base}: КТК row {r_no}: numeric KPI "
                                        f"not marked «ориентир»: {kpi[:50]}")
        elif a["kind"] == "priority-matrix":
            for t in [t for t in a["tables"] if t["kind"] == "priority-matrix"]:
                c_q = _col(t, "Квадрант")
                c_d = _col(t, "Делегирование")
                for r_no, row in enumerate(t["rows"], 1):
                    q = cell(row, c_q).lower()
                    if ("не важно" in q) and not cell(row, c_d):
                        warnings.append(f"W3 {base}: matrix row {r_no}: quadrant "
                                        f"'{cell(row, c_q)}' without Делегирование")
    return warnings


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def parse_library(vault):
    """Parse the unified library tree, EXCLUDING library/artifacts/ (the checker's
    own inputs are not library nodes). Unlike engine.parse_paths, the artifact
    directory is pruned here."""
    base = os.path.join(vault, "library")
    art_prefix = os.path.abspath(os.path.join(base, "artifacts")) + os.sep
    lib = engine.Library()
    for fp in engine.collect_files(base):
        if os.path.abspath(fp).startswith(art_prefix):
            continue
        rel = os.path.relpath(fp, base)
        try:
            text = open(fp, encoding="utf-8").read()
        except Exception as e:
            lib.errors.append(f"READ ERROR {rel}: {e}")
            continue
        engine.parse_text(text, rel, lib)
    return lib


def run(vault, cross=False, semantic=False):
    reg = load_registry()
    lib = parse_library(vault)
    artifacts = [parse_file(p) for p in collect_artifacts(vault)]
    errors, warnings = check_structure(reg, artifacts, lib)
    errors += [f"LIBRARY {e}" for e in lib.errors]
    if not artifacts:
        errors.append("no artifact files found under library/artifacts")
    if cross:
        e, w = check_cross(reg, artifacts, lib)
        errors += e
        warnings += w
    if semantic:
        warnings += check_semantic(reg, artifacts, lib)
    return {"errors": errors, "warnings": warnings,
            "files": [os.path.relpath(a["path"], vault) for a in artifacts]}


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Artifact-chain conformance checker")
    ap.add_argument("vault")
    ap.add_argument("--cross", action="store_true")
    ap.add_argument("--semantic", action="store_true")
    ap.add_argument("--json")
    args = ap.parse_args(argv)

    if not os.path.exists(args.vault):
        print(f"ERROR: vault not found: {args.vault}")
        return 2

    res = run(args.vault, cross=args.cross, semantic=args.semantic)
    print(f"scanned: {len(res['files'])} artifact file(s)")
    if res["warnings"]:
        print(f"\nWARNINGS ({len(res['warnings'])}):")
        for w in res["warnings"]:
            print(f"  - {w}")
    if res["errors"]:
        print(f"\nERRORS ({len(res['errors'])}):")
        for e in res["errors"]:
            print(f"  - {e}")
    print("\n" + ("OK" if not res["errors"] else "FAIL"))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
    return 0 if not res["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
