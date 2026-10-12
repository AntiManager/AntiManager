#!/usr/bin/env python3
"""Attach the APQC PCF crosswalk attribute to every PROCESS (T1.3).

Reads a mapping (code -> list of APQC L3 codes, first = primary) and writes
`**APQC:** <codes>` into each PROCESS attribute block, right after `**Код:**`.
Idempotent: an existing `**APQC:**` line in the block is replaced, not duplicated.
Preserves UTF-8 (no BOM) and the file's own line endings.

Usage:
  python apqc_crosswalk.py <library-folder> <apqc_mapping.json> [--dry-run]
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from datetime import datetime

PROC_HEAD_RE = re.compile(r"^#{3}\s+Процесс\s+([A-Z][A-Z0-9_-]*)\s*:\s*(.+?)\s*$")
HEAD_RE = re.compile(r"^#{1,5}\s+")
CODE_LINE_RE = re.compile(r"^\*\*Код:\*\*\s*[A-Z]")
APQC_LINE_RE = re.compile(r"^\*\*APQC:\*\*")
ATTR_LINE_RE = re.compile(r"^\*{1,2}[^*:]+:\*{1,2}")


def process_sections(lines):
    """Yield (code, start_idx, end_idx) for each `### Процесс` section."""
    n = len(lines)
    heads = []
    for i, ln in enumerate(lines):
        m = PROC_HEAD_RE.match(ln.rstrip("\r\n"))
        if m:
            heads.append((m.group(1), i))
        elif HEAD_RE.match(ln.rstrip("\r\n")):
            heads.append((None, i))
    heads.append((None, n))
    for k in range(len(heads) - 1):
        code, i = heads[k]
        if code is None:
            continue
        yield code, i, heads[k + 1][1]


def update_block(lines, start, end, codes):
    """Insert/replace `**APQC:**` inside the attr block of lines[start:end]."""
    code_idx = None
    apqc_idx = None
    for i in range(start + 1, end):
        s = lines[i].rstrip("\r\n")
        if APQC_LINE_RE.match(s):
            apqc_idx = i
            break
        if code_idx is None and CODE_LINE_RE.match(s):
            code_idx = i
            continue
        if code_idx is not None and s.strip() and not ATTR_LINE_RE.match(s):
            break  # attr block ended
    value = ", ".join(codes)
    # determine EOL from a neighbouring line
    eol = "\r\n" if any("\r\n" in lines[j] for j in range(start, min(end, start + 6))) else "\n"
    new_line = f"**APQC:** {value}{eol}"

    if apqc_idx is not None:
        old = lines[apqc_idx].rstrip("\r\n")
        if old == f"**APQC:** {value}":
            return lines, "unchanged"
        lines[apqc_idx] = new_line
        return lines, "replaced"
    if code_idx is None:
        raise ValueError("no `**Код:**` line found in PROCESS block")
    lines.insert(code_idx + 1, new_line)
    return lines, "inserted"


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    folder, mapping_path = argv[0], argv[1]
    dry = "--dry-run" in argv
    mapping = json.load(open(mapping_path, encoding="utf-8"))["processes"]

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = os.path.join(os.environ.get("TEMP", "."), "kilo", "backups",
                              "apqc-" + stamp)
    os.makedirs(backup_dir, exist_ok=True)

    seen, stats = set(), {"inserted": 0, "replaced": 0, "unchanged": 0}
    files = [f for f in sorted(os.listdir(folder)) if f.endswith(".md")]
    for fn in files:
        path = os.path.join(folder, fn)
        raw = open(path, encoding="utf-8", newline="").read()
        lines = raw.splitlines(keepends=True)
        changed = False
        # bottom-up so an insertion does not shift the indices of earlier sections
        for code, start, end in reversed(list(process_sections(lines))):
            if code not in mapping:
                print(f"  ! {code} ({fn}) has no mapping entry")
                continue
            seen.add(code)
            lines, action = update_block(lines, start, end, mapping[code])
            stats[action] += 1
            changed = changed or action != "unchanged"
        if changed and not dry:
            shutil.copy2(path, os.path.join(backup_dir, fn))
            open(path, "w", encoding="utf-8", newline="").write("".join(lines))

    missing = set(mapping) - seen
    print(f"PROCESS seen: {len(seen)}/{len(mapping)}  "
          f"inserted={stats['inserted']} replaced={stats['replaced']} "
          f"unchanged={stats['unchanged']}")
    if missing:
        print("MAPPING codes not found in library:")
        for c in sorted(missing):
            print("  -", c)
    print("backup (if written):", backup_dir)
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
