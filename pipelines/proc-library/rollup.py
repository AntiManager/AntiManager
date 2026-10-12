#!/usr/bin/env python3
"""Economic roll-up (T2.5) over a parsed process library.

Implements T0.5 Decision 2 on a parsed graph. For a node `v` over its descendant
operations `i`:

    FTE(v)        = Σ (Трудоёмкость_i × F_i) / AnnualFund
    LayerCost(v)  = Σ (Стоимость_i  × F_i)
    Criticality(v)= max(Критичность_i)
    Periodicity(v)= highest-frequency cadence present in the subtree

where `F_i` is the number of executions per year derived from the operation's
`Периодичность` (`<unit> ×<count>`). Reference constants (T2.4):
`AnnualFund = 1700 ч` per FTE, `REF_RATE = 1000 руб/ч`. All values are reference
values for an SME template, never client numbers.

Usage:
  python -X utf8 rollup.py <path> [--scope PREFIX ...] [--json out.json]

`<path>` is a library folder or a single `.md` file (as in `engine.py`). Rows are
emitted for every node at SUBPROCESS / PROCESS / GROUP level that contains at
least one operation carrying economics; `--scope` keeps only codes that start
with one of the given prefixes (e.g. `PLAN- SL_PLAN-`).

Exit code 0 = matrix written, 2 = usage/IO error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import engine

# Executions per year per cadence unit (T0.5 Decision 2).
EXEC_PER_YEAR = {"shift": 3 * 365, "day": 365, "week": 52,
                 "month": 12, "quarter": 4, "year": 1}
ANNUAL_FUND = 1700          # reference annual labour fund per FTE, ч
REF_RATE = 1000             # reference labour rate, руб/ч
RANK = {"low": 0, "medium": 1, "high": 2}
# Cadence frequency order (highest first); `event` is lowest (on demand).
FREQ_ORDER = ["shift", "day", "week", "month", "quarter", "year", "event"]

PERIODICITY_RE = re.compile(
    r"^(%s)\s*×\s*(\d+)$" % "|".join(FREQ_ORDER))
NUMBER_RE = re.compile(r"^(\d+(?:[.,]\d+)?)")


def num(value: str) -> float:
    """Parse '0,5 ч' / '300 руб' -> 0.5 / 300.0."""
    m = NUMBER_RE.match((value or "").strip())
    if not m:
        raise ValueError(f"not a number: {value!r}")
    return float(m.group(1).replace(",", "."))


def executions(periodicity: str):
    """`<unit> ×<count>` -> executions per year (None if unparsable)."""
    m = PERIODICITY_RE.match((periodicity or "").strip())
    if not m:
        return None
    unit, count = m.group(1), int(m.group(2))
    if unit == "event":
        return float(count)          # explicit, on demand (T0.5 D2)
    return float(EXEC_PER_YEAR[unit] * count)


def _ops(node):
    return [c for c in engine._descendants(node) if c.level == "OPERATION"]


def compute(node) -> dict:
    """Roll up one node's subtree (operations below it)."""
    ops = _ops(node)
    hours = cost = 0.0
    econ = 0
    cr = None
    periods = set()
    for op in ops:
        lab = engine.aget(op.attrs, "Трудоёмкость")
        per = engine.aget(op.attrs, "Периодичность")
        cst = engine.aget(op.attrs, "Стоимость")
        f = executions(per) if per else None
        if lab is None or cst is None or f is None:
            continue
        econ += 1
        hours += num(lab) * f
        cost += num(cst) * f
        k = engine.aget(op.attrs, "Критичность")
        if k and (cr is None or RANK[k] > RANK[cr]):
            cr = k
        unit = per.split("×")[0].strip()
        if unit in FREQ_ORDER:
            periods.add(unit)
    periodicity = next((u for u in FREQ_ORDER if u in periods), None)
    return {
        "code": node.code,
        "level": node.level,
        "name": node.name,
        "ops": len(ops),
        "ops_econ": econ,
        "hours": round(hours, 4),
        "fte": round(hours / ANNUAL_FUND, 6),
        "cost": round(cost, 2),
        "criticality": cr,
        "periodicity": periodicity,
    }


def in_scope(code, scope):
    """A prefix `P` matches code `P` itself or any descendant `P-…`."""
    for p in scope or ():
        base = p.rstrip("-")
        if code == base or code.startswith(base + "-"):
            return True
    return False


def rollup_matrix(lib, scope=None, levels=("SUBPROCESS", "PROCESS", "GROUP")):
    """One row per node at the requested levels that has economics ops.

    `scope` is an optional list of code prefixes (empty/None = whole library).
    """
    rows = []
    for n in engine._iter_nodes(lib):
        if n.level not in levels:
            continue
        if scope and not in_scope(n.code, scope):
            continue
        row = compute(n)
        if row["ops_econ"] > 0:
            rows.append(row)
    return sorted(rows, key=lambda r: r["code"])


def totals(rows, level):
    """Aggregate the rows of one level: {ops, hours, fte, cost}."""
    sel = [r for r in rows if r["level"] == level]
    return {
        "rows": len(sel),
        "ops": sum(r["ops"] for r in sel),
        "hours": round(sum(r["hours"] for r in sel), 4),
        "fte": round(sum(r["fte"] for r in sel), 6),
        "cost": round(sum(r["cost"] for r in sel), 2),
    }


def _fmt(x, places=0):
    s = f"{x:,.{places}f}".replace(",", " ").replace(".", ",")
    return s


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Economic roll-up (T2.5)")
    ap.add_argument("path")
    ap.add_argument("--scope", nargs="*", default=[])
    ap.add_argument("--json")
    args = ap.parse_args(argv)

    if not os.path.exists(args.path):
        print(f"ERROR: path not found: {args.path}")
        return 2
    base = args.path if os.path.isdir(args.path) else os.path.dirname(args.path)
    target = args.path if os.path.isfile(args.path) else os.path.join(base, "library")
    lib = engine.parse_paths(target)

    rows = rollup_matrix(lib, scope=args.scope or None)
    print(f"{'code':<22}{'level':<11}{'ops':>4}{'FTE':>9}"
          f"{'ч/год':>10}{'руб/год':>14}  crit/period")
    for r in rows:
        print(f"{r['code']:<22}{r['level'].lower():<11}{r['ops']:>4}"
              f"{_fmt(r['fte'], 3):>9}{_fmt(r['hours'], 1):>10}"
              f"{_fmt(r['cost']):>14}  {r['criticality']}/{r['periodicity']}")

    for level in ("SUBPROCESS", "PROCESS", "GROUP"):
        t = totals(rows, level)
        print(f"{level}: rows={t['rows']} ops={t['ops']} "
              f"FTE={_fmt(t['fte'], 3)} ч/год={_fmt(t['hours'], 1)} "
              f"руб/год={_fmt(t['cost'])}")
    print(f"constants: AnnualFund={ANNUAL_FUND} ч, REF_RATE={REF_RATE} руб/ч")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({
                "constants": {"AnnualFund": ANNUAL_FUND, "REF_RATE": REF_RATE},
                "scope": args.scope or None,
                "rows": rows,
                "totals": {lvl: totals(rows, lvl)
                           for lvl in ("SUBPROCESS", "PROCESS", "GROUP")},
            }, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
