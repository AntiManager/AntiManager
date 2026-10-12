#!/usr/bin/env python3
"""Extract the APQC PCF (v7.4, ru) L1/L2/L3 catalog (T1.3).

Source workbook (read-only): the `Combined` sheet, columns
`Hierarchy ID` / `Name` / `PCF ID`. Level is derived from the hierarchy id:
  X.0 -> L1, X.Y -> L2, X.Y.Z -> L3, X.Y.Z.W -> L4 (L4 is not emitted).

Usage:
  python apqc_catalog.py <xlsx> [out.json]     # default out: apqc_catalog.json
"""
from __future__ import annotations

import json
import sys

XLSX = (r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Archive\K014749_"
        r"APQC Process Classification Framework (PCF) - Cross-Industry - "
        r"Excel Version 7.4_ru.xlsx")


def level_of(hid: str) -> int:
    segs = hid.split(".")
    if not all(s.isdigit() for s in segs):
        return 0
    if len(segs) == 2 and segs[1] == "0":
        return 1
    return len(segs)  # 2 segs -> L2, 3 segs -> L3, 4 segs -> L4


def extract(xlsx: str) -> dict:
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    rows = list(wb["Combined"].iter_rows(values_only=True))[1:]
    out = {"l1": [], "l2": [], "l3": []}
    for r in rows:
        hid = r[1]
        if not hid:
            continue
        hid = str(hid).strip()
        lvl = level_of(hid)
        if lvl in (1, 2, 3):
            out[f"l{lvl}"].append({"hier": hid, "name": r[2], "pcf": r[0]})
    return out


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    xlsx = argv[0] if argv else XLSX
    out = argv[1] if len(argv) > 1 else "apqc_catalog.json"
    data = extract(xlsx)
    json.dump(data, open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"L1={len(data['l1'])} L2={len(data['l2'])} L3={len(data['l3'])} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
