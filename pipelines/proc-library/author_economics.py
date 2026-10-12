#!/usr/bin/env python3
"""Insert T2.4 economics attributes into operations of a library file.

Usage:
  python -X utf8 author_economics.py <file.md> <mapping.json> [--rate N]

The mapping is ``{ "<op-code>": {"hours": <number>, "criticality": "<high|medium|low>"} }``.
For every mapped operation, four bullets are inserted after the ``- **КПЭ:**``
line (T0.5 Decision 1 order):

    - **Критичность:** <criticality>
    - **Периодичность:** <unit> ×1        # unit = the op's `Горизонт`
    - **Трудоёмкость:** <hours> ч
    - **Стоимость:** <hours × rate> руб   # reference rate, default 1000 руб/ч

Line endings are detected and preserved (the vault library is CRLF). The tool is
idempotent: an operation that already carries ``- **Критичность:**`` is skipped.
"""
from __future__ import annotations

import json
import re
import sys

HORIZON_RE = re.compile(r"^- \*\*Горизонт:\*\*\s*(\S+)\s*$")
KPI_RE = re.compile(r"^- \*\*КПЭ:\*\*")
CRIT_RE = re.compile(r"^- \*\*Критичность:\*\*")
OP_RE = re.compile(r"^##### Операция (\S+?):")

VALID_UNITS = {"year", "quarter", "month", "week", "day", "shift", "event"}


def fmt_num(x: float) -> str:
    """0.5 -> '0,5'; 2.0 -> '2'."""
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return ("%g" % x).replace(".", ",")


def main(argv):
    rate = 1000
    a = list(argv)
    if "--rate" in a:
        i = a.index("--rate")
        rate = float(a[i + 1])
        del a[i:i + 2]
    if len(a) != 2:
        print(__doc__)
        return 2
    path, mapping_path = a

    mapping = json.load(open(mapping_path, encoding="utf-8"))

    raw = open(path, "rb").read()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    lines = text.split(eol)

    out = []
    cur = None
    horizon = None
    inserted = 0
    skipped = 0
    seen = set()

    i = 0
    while i < len(lines):
        line = lines[i]
        m = OP_RE.match(line)
        if m:
            cur = m.group(1)
            horizon = None
        elif cur and HORIZON_RE.match(line):
            h = HORIZON_RE.match(line).group(1)
            horizon = h if h in VALID_UNITS else None

        out.append(line)
        if cur and KPI_RE.match(line) and cur in mapping and cur not in seen:
            seen.add(cur)
            # look ahead: already has an economics block?
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if CRIT_RE.match(nxt):
                skipped += 1
            else:
                spec = mapping[cur]
                hours = float(spec["hours"])
                crit = spec["criticality"]
                if horizon is None:
                    raise SystemExit(f"{cur}: no valid Горизонт found")
                cost = hours * rate
                out.append(f"- **Критичность:** {crit}")
                out.append(f"- **Периодичность:** {horizon} \u00d71")
                out.append(f"- **Трудоёмкость:** {fmt_num(hours)} \u0447")
                out.append(f"- **Стоимость:** {fmt_num(cost)} \u0440\u0443\u0431")
                inserted += 1
        i += 1

    missing = set(mapping) - seen
    if missing:
        raise SystemExit(f"mapped but not found: {sorted(missing)}")

    open(path, "wb").write(eol.join(out).encode("utf-8"))
    print(f"{path}: inserted {inserted}, skipped {skipped}, "
          f"eol={'CRLF' if eol == chr(13) + chr(10) else 'LF'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
