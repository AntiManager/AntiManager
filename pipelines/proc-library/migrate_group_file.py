#!/usr/bin/env python3
"""Migrate a legacy process-library file into the unified vault template (T1.6).

Splits a source file by `## Группа <CODE>: <name>` into one `<CODE>.md` per group
and normalises it to the §9.1 convention:
  - group attribute block: italic `*key:*` -> bold `**key:**`; `Код группы` ->
    `Код`, `Владелец группы` -> `Владелец`; inserts `**Цель группы:**` (T0.4);
  - PROCESS `**Код процесса:**` -> `**Код:**` and inserts `**APQC:**` after it;
  - Obsidian `\\<` escapes removed.
Non-group `##` sections (Содержание, Приложения) are skipped and reported.

Usage:
  python migrate_group_file.py <source.md> <out_dir> <group_goals.json>
         <apqc_mapping.json> [--dry-run]
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

H2_RE = re.compile(r"^##\s+(.*?)\s*$")
GROUP_RE = re.compile(r"^##\s+Группа\s+([A-Z][A-Z0-9_-]*)\s*:\s*(.+?)\s*$")
PROC_RE = re.compile(r"^###\s+Процесс\s+([A-Z][A-Z0-9_-]*)\s*:\s*(.+?)\s*$")
ITAL_RE = re.compile(r"^\*([^*:]+):\*\s*(.*)$")
CODE_PROC_RE = re.compile(r"^\*\*Код процесса:\*\*\s*(.*)$")
CODE_RE = re.compile(r"^\*\*Код:\*\*\s*(.*)$")
UPDATED = "2026-10-11"

GROUP_ATTR = {"Код группы": "Код", "Владелец группы": "Владелец"}
TAG = {"INF": "inf", "SL_PLAN": "sl-plan", "SL_LOG": "sl-log", "SL_QUAL": "sl-qual",
       "SL_MNT": "sl-mnt", "SL_HRP": "sl-hrp", "SL_EMG": "sl-emg", "SL_ANL": "sl-anl"}


def read_lines(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n"), nl


def trim(lines):
    out = list(lines)
    while out and out[-1].strip() == "":
        out.pop()
    if out and out[-1].strip() == "---":
        out.pop()
    while out and out[-1].strip() == "":
        out.pop()
    return out


def normalize(body, goal, apqc):
    out = []
    cur_proc = None
    apqc_done = set()
    for ln in body:
        s = ln.strip()
        mp = PROC_RE.match(s)
        if mp:
            cur_proc = mp.group(1)
            out.append(ln)
            continue
        if s.startswith("###") or s.startswith("####"):
            if not mp:
                cur_proc = None
            out.append(ln)
            continue
        # group italic attrs -> bold §9.1
        mi = ITAL_RE.match(s)
        if mi:
            key, val = mi.group(1).strip(), mi.group(2)
            key = GROUP_ATTR.get(key, key)
            out.append(f"**{key}:** {val}")
            if key == "Владелец":
                out.append(f"**Цель группы:** {goal}")
            continue
        mcp = CODE_PROC_RE.match(s)
        if mcp:
            out.append(f"**Код:** {mcp.group(1)}")
            if cur_proc and cur_proc not in apqc_done:
                out.append(f"**APQC:** {', '.join(apqc[cur_proc])}")
                apqc_done.add(cur_proc)
            continue
        out.append(ln.replace("\\<", "<"))
    return out


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    dry = "--dry-run" in argv
    args = [a for a in argv if not a.startswith("--")]
    src, out_dir, goals_path, mapping_path = args
    goals = json.load(open(goals_path, encoding="utf-8"))["goals"]
    mapping = json.load(open(mapping_path, encoding="utf-8"))["processes"]

    lines, nl = read_lines(src)
    heads = [(i, GROUP_RE.match(ln.strip())) for i, ln in enumerate(lines)
             if H2_RE.match(ln.strip())]
    groups = [(i, m.group(1), m.group(2)) for i, m in heads if m]

    written, skipped = [], []
    for gi, (start, code, name) in enumerate(groups):
        end = groups[gi + 1][0] if gi + 1 < len(groups) else len(lines)
        # stop at the next `##` heading of any kind
        for j in range(start + 1, end):
            if H2_RE.match(lines[j].strip()) and not GROUP_RE.match(lines[j].strip()):
                end = j
                break
        body = trim(lines[start + 1:end])
        norm = normalize(body, goals.get(code, ""), mapping)
        fm = ["---", f"tags: [library, process-library, group, {TAG.get(code, code.lower())}]",
              "status: draft", f"updated: {UPDATED}", "---", ""]
        path = os.path.join(out_dir, f"{code}.md")
        if not dry:
            with io.open(path, "w", encoding="utf-8", newline="") as f:
                f.write(nl.join(fm + [f"## Группа {code}: {name}"] + norm).rstrip("\n") + nl)
        written.append(code)

    for i, ln in enumerate(lines):
        if H2_RE.match(ln.strip()) and not GROUP_RE.match(ln.strip()):
            skipped.append(ln.strip())

    print(f"groups written: {len(written)} -> {', '.join(written)}")
    print(f"non-group sections skipped: {skipped}")
    # report processes without a mapping entry
    proc_codes = [PROC_RE.match(l.strip()).group(1) for l in lines if PROC_RE.match(l.strip())]
    noapqc = [c for c in proc_codes if c not in mapping]
    if noapqc:
        print("PROCESS without APQC mapping:", noapqc)
        return 1
    print(f"processes with APQC: {len(proc_codes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
