#!/usr/bin/env python3
"""Author typed OPERATION nodes from a mapping (T2.2 replication, T2.6).

Converts a subprocess's legacy operation container

    ##### Операции подпроцесса MFG-01-01:
    1. **<name>**
    \t- Исполнитель: ...
    \t- Входы: ...
    \t- Выходы: ...
    \t- КПЭ: ...

into one `##### Операция <code>: <name>` node per operation with the regulated
bullet block (T0.5/T2.2):

    - **Тип:** Simple
    - **Цель:** ...
    - **Горизонт:** shift
    - **Исполнитель:** ...
    - **Входы:** `Тип@Состояние`
    - **Выходы:** `Тип`
    - **КПЭ:** ...
    - **decomposition:** ATOMIC

Usage:
  python -X utf8 author_operations.py <file.md> <ops.json>

`ops.json` maps a subprocess code to its ordered operations:

    {"MFG-01-01": [
        {"code": "MFG-01-01-01", "name": "...", "type": "Simple",
         "goal": "...", "horizon": "shift", "executor": "...",
         "inputs": ["СменносуточноеЗадание"], "outputs": ["..."],
         "kpi": "...", "decomposition": "ATOMIC"}, ...]}

I/O entries are vocabulary refs (backticks added by the tool); an empty list
renders `—` (boundary side). Line endings are detected and preserved. Economics
bullets are added separately by `author_economics.py`.

Two source forms are handled (T2.6 replication):

- legacy container `##### Операции подпроцесса <code>:` + numbered list;
- existing `##### Операция <code>: <name>` node with a partial bullet block
  (retype): the whole node is rewritten to the regulated block.
"""
from __future__ import annotations

import json
import re
import sys

SUBPROC_HEAD = re.compile(r"^####\s+Подпроцесс\s+(\S+?):")
CONTAINER = re.compile(r"^#####\s+Операции подпроцесса\s+(\S+?):\s*$")
NODE = re.compile(r"^#####\s+Операция\s+(\S+?):")
HEAD = re.compile(r"^#{1,6}\s")


def io_cell(items):
    if not items:
        return "\u2014"
    return ", ".join("`%s`" % i for i in items)


def block(op):
    lines = [f"##### Операция {op['code']}: {op['name']}"]
    lines.append(f"- **Тип:** {op['type']}")
    lines.append(f"- **Цель:** {op['goal']}")
    lines.append(f"- **Горизонт:** {op['horizon']}")
    lines.append(f"- **Исполнитель:** {op['executor']}")
    lines.append(f"- **Входы:** {io_cell(op.get('inputs'))}")
    lines.append(f"- **Выходы:** {io_cell(op.get('outputs'))}")
    lines.append(f"- **КПЭ:** {op['kpi']}")
    lines.append(f"- **decomposition:** {op.get('decomposition', 'ATOMIC')}")
    return lines


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    path, ops_path = argv
    data = json.load(open(ops_path, encoding="utf-8"))
    # A JSON value is a subprocess's ordered operations; the container form is
    # keyed by subprocess code, the node form is located by operation code.
    containers = {k: v for k, v in data.items() if not k.startswith("_")}
    nodes = {o["code"]: o for v in containers.values() for o in v}
    all_codes = set(nodes)

    raw = open(path, "rb").read()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    lines = raw.decode("utf-8").split(eol)
    present = {NODE.match(x).group(1) for x in lines if NODE.match(x)}

    out = []
    i = 0
    n = len(lines)
    replaced = set()
    while i < n:
        line = lines[i]
        mc = CONTAINER.match(line)
        mn = NODE.match(line)
        if mc and mc.group(1) in containers:
            repl = containers[mc.group(1)]
        elif mn and mn.group(1) in nodes:
            repl = [nodes[mn.group(1)]]
        else:
            out.append(line)
            i += 1
            continue
        # skip the heading + body up to the next heading
        j = i + 1
        while j < n and not HEAD.match(lines[j]):
            j += 1
        for k, o in enumerate(repl):
            if k:
                out.append("")
            out.extend(block(o))
        out.append("")
        replaced.update(o["code"] for o in repl)
        i = j

    # Re-runnable: a group already converted (its ops present as nodes) is done.
    missing = {c for c in all_codes if c not in replaced and c not in present}
    if missing:
        raise SystemExit(f"operation source not found for: {sorted(missing)}")

    open(path, "wb").write(eol.join(out).encode("utf-8"))
    print(f"{path}: wrote {len(replaced)} operations "
          f"in {len(containers)} source groups, "
          f"eol={'CRLF' if eol == chr(13)+chr(10) else 'LF'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
