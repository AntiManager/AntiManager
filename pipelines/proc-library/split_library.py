#!/usr/bin/env python3
"""Split a monolithic process library (Proc_lib.md) into per-group files.

T1.1 of plan 1791721561689. Faithful split only: the parsed graph (nodes,
levels, parents, links) must be byte-for-byte equivalent before/after, so this
script distributes content by the `## Группа <CODE>: <name>` headings and does
not touch the operations themselves.

Output layout (T0.7 Decision 6):

    <out>/INDEX.md      LIBRARY node (H1) + group registry + mermaid overview
    <out>/<CODE>.md     one file per GROUP (## Группа ...)

The INDEX heading anchor list is rewritten to per-file wikilinks, and Obsidian
dataview artifacts (`= this.version`, `=dateformat(...)`) are stripped
(T0.7 Decision 5 / T0.8 step 4).

Usage:
    python split_library.py <source.md> <out_dir>
"""
from __future__ import annotations

import io
import os
import re
import sys

GROUP_RE = re.compile(r"^##\s+Группа\s+([A-Z][A-Z0-9_-]*)\s*:\s*(.+?)\s*$")
DATAVIEW_RE = re.compile(r"=\s*(this\.|dateformat\()")
UPDATED = "2026-10-11"


def read_lines(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return lines, nl


def trim_section(lines):
    """Drop trailing blank lines and a trailing `---` separator."""
    out = list(lines)
    while out and out[-1].strip() == "":
        out.pop()
    if out and out[-1].strip() == "---":
        out.pop()
    while out and out[-1].strip() == "":
        out.pop()
    return out


def strip_dataview(lines):
    return [ln for ln in lines if not DATAVIEW_RE.search(ln)]


def strip_frontmatter(lines):
    """Remove a leading `---` frontmatter block, if present."""
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[i + 1:]
    return lines


def group_frontmatter(code):
    slug = code.lower().replace("_", "-")
    return [
        "---",
        f"tags: [library, process-library, group, {slug}]",
        "status: draft",
        f"updated: {UPDATED}",
        "---",
        "",
    ]


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print(__doc__)
        return 2
    src, out_dir = argv

    lines, nl = read_lines(src)

    groups = []  # (line_idx, code, name)
    for i, ln in enumerate(lines):
        m = GROUP_RE.match(ln)
        if m:
            groups.append((i, m.group(1), m.group(2)))
    if not groups:
        print("ERROR: no '## Группа <CODE>: <name>' headings found")
        return 1

    os.makedirs(out_dir, exist_ok=True)

    # ---- INDEX.md ----
    head = trim_section(lines[:groups[0][0]])
    head = strip_dataview(head)
    head = strip_frontmatter(head)
    # replace the heading-anchor contents list with per-file wikilinks
    contents_idx = next((i for i, l in enumerate(head) if l.strip() == "## Содержание"), None)
    if contents_idx is not None:
        j = contents_idx + 1
        while j < len(head) and head[j].strip() != "":
            j += 1
        registry = [f"{n}. [[{code}|{name} ({code})]]"
                    for n, (_, code, name) in enumerate(groups, 1)]
        head = head[:contents_idx + 1] + registry + head[j:]

    index_lines = [
        "---",
        "tags: [library, process-library, index, sme]",
        "status: draft",
        f"updated: {UPDATED}",
        "---",
        *head,
    ]
    write(os.path.join(out_dir, "INDEX.md"), index_lines, nl)

    # ---- one file per group ----
    for gi, (start, code, name) in enumerate(groups):
        end = groups[gi + 1][0] if gi + 1 < len(groups) else len(lines)
        body = trim_section(lines[start:end])
        write(os.path.join(out_dir, f"{code}.md"), group_frontmatter(code) + body, nl)

    print(f"Wrote INDEX.md + {len(groups)} group files to {out_dir}")
    for _, code, name in groups:
        print(f"  {code}.md  {name}")
    return 0


def write(path, lines, nl):
    data = nl.join(lines).rstrip("\n") + nl
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(data)


if __name__ == "__main__":
    sys.exit(main())
