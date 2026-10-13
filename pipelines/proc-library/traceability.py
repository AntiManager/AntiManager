#!/usr/bin/env python3
"""Artifact-chain traceability report (plan 1791810263662, sub-plan 05, E4).

Builds the three traceability links and reports gap counts:
  role  -> КТК process -> goal          (goal from the library node)
  task  -> process                       (priority matrix)
  event -> process + horizon             (event grid)

Gaps: any artifact row with no process code is an H7 gap. A referenced code
that does not resolve to a library node is an H2 gap. Both must be 0 (or waived).

Usage:
  python traceability.py <vault> [--md out.md] [--json out.json]
Exit: 0 = no gaps, 1 = gap(s), 2 = usage/IO error (vault missing or no
artifact files found).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import check_artifacts as ca  # noqa: E402


def _role_of_table(t):
    return t["role"] if t["role"] else "?"


def build(vault):
    lib = ca.parse_library(vault)
    artifacts = [ca.parse_file(p) for p in ca.collect_artifacts(vault)]

    ktk, matrix, grid = [], [], []
    gaps = {"no_code": [], "unresolved": []}

    def codes_of(row, t, col):
        codes = ca.proc_codes(ca.cell(row, ca._col(t, col)))
        return codes

    for a in artifacts:
        base = os.path.basename(a["path"])
        if a["kind"] == "ktk":
            role = a["heading_roles"][0] if a["heading_roles"] else "?"
            for t in [t for t in a["tables"] if t["kind"] == "ktk"]:
                for r_no, row in enumerate(t["rows"], 1):
                    codes = codes_of(row, t, "Код процесса")
                    if not codes:
                        gaps["no_code"].append(f"КТК {role} row {r_no}")
                    for code in codes:
                        node = lib.by_code.get(code)
                        if node is None:
                            gaps["unresolved"].append(f"КТК {role} {code}")
                            goal = None
                        else:
                            goal = node.goal()
                        ktk.append({"role": role, "code": code, "goal": goal,
                                    "row": r_no, "out": ca.cell(
                                        row, ca._col(t, "Критический выход"))})
        elif a["kind"] == "priority-matrix":
            for t in [t for t in a["tables"] if t["kind"] == "priority-matrix"]:
                role = _role_of_table(t)
                for r_no, row in enumerate(t["rows"], 1):
                    codes = codes_of(row, t, "Связанный процесс (код)")
                    task = ca.cell(row, ca._col(t, "Задача"))
                    if not codes:
                        gaps["no_code"].append(f"matrix {role} row {r_no}")
                    for code in codes:
                        if code not in lib.by_code:
                            gaps["unresolved"].append(f"matrix {role} {code}")
                    matrix.append({"role": role, "task": task, "codes": codes})
        elif a["kind"] == "event-grid":
            for t in [t for t in a["tables"] if t["kind"] == "event-grid"]:
                for r_no, row in enumerate(t["rows"], 1):
                    codes = codes_of(row, t, "Процессы")
                    if not codes:
                        gaps["no_code"].append(f"grid row {r_no}")
                    for code in codes:
                        if code not in lib.by_code:
                            gaps["unresolved"].append(f"grid row {r_no} {code}")
                    grid.append({"event": ca.cell(row, ca._col(t, "Событие")),
                                 "owner": ca.cell(row, ca._col(t, "Владелец")),
                                 "codes": codes,
                                 "horizon": ca.cell(row, ca._col(t, "Горизонт"))})

    return {"ktk": ktk, "matrix": matrix, "grid": grid, "gaps": gaps,
            "artifact_files": len(artifacts),
            "counts": {"ktk_links": len(ktk), "matrix_rows": len(matrix),
                       "grid_rows": len(grid),
                       "no_code": len(gaps["no_code"]),
                       "unresolved": len(gaps["unresolved"])}}


def render_md(rep):
    L = ["# Artifact-chain traceability report", "",
         "role → КТК process → goal · task → process · event → process + horizon", ""]
    L += ["## Summary", "",
          f"- role → КТК process links: {rep['counts']['ktk_links']}",
          f"- matrix rows: {rep['counts']['matrix_rows']}",
          f"- grid rows: {rep['counts']['grid_rows']}",
          f"- rows with no process code (H7 gaps): {rep['counts']['no_code']}",
          f"- unresolved codes (H2 gaps): {rep['counts']['unresolved']}",
          ""]
    L += ["## role → КТК process → goal", "",
          "| Роль | Код | Цель процесса (library) |", "|---|---|---|"]
    for r in rep["ktk"]:
        goal = (r["goal"] or "—").replace("|", "\\|").replace("\n", " ")
        L.append(f"| {r['role']} | {r['code']} | {goal} |")
    L += ["", "## matrix task → process", "",
          "| Роль | Задача | Процессы |", "|---|---|---|"]
    for r in rep["matrix"]:
        L.append(f"| {r['role']} | {r['task'].replace('|', '\\|')} | "
                 f"{', '.join(r['codes']) or '—'} |")
    L += ["", "## event → process + horizon", "",
          "| Событие | Владелец | Процессы | Горизонт |", "|---|---|---|---|"]
    for r in rep["grid"]:
        L.append(f"| {r['event'].replace('|', '\\|')} | "
                 f"{r['owner'].replace('|', '\\|')} | "
                 f"{', '.join(r['codes']) or '—'} | {r['horizon']} |")
    if rep["gaps"]["no_code"] or rep["gaps"]["unresolved"]:
        L += ["", "## Gaps", ""]
        for g in rep["gaps"]["no_code"]:
            L.append(f"- H7 (no code): {g}")
        for g in rep["gaps"]["unresolved"]:
            L.append(f"- H2 (unresolved): {g}")
    return "\n".join(L) + "\n"


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Artifact-chain traceability report")
    ap.add_argument("vault")
    ap.add_argument("--md")
    ap.add_argument("--json")
    args = ap.parse_args(argv)
    if not os.path.exists(args.vault):
        print(f"ERROR: vault not found: {args.vault}")
        return 2

    rep = build(args.vault)
    if not rep["artifact_files"]:
        print(f"ERROR: no artifact files under "
              f"{os.path.join(args.vault, 'library', 'artifacts')}")
        return 2
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(render_md(rep))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
    c = rep["counts"]
    gaps = c["no_code"] + c["unresolved"]
    print(f"role→КТК links {c['ktk_links']} · matrix rows {c['matrix_rows']} · "
          f"grid rows {c['grid_rows']}")
    print(f"gaps: no_code={c['no_code']} unresolved={c['unresolved']}")
    print("\n" + ("OK" if not gaps else "FAIL"))
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())
