#!/usr/bin/env python3
"""
Process-library engine: Markdown parser + ontology validator + CLI.

Implements the Spiral A (`ontology-processes.md` v3.0) model:
  levels LIBRARY -> GROUP -> PROCESS -> SUBPROCESS -> OPERATION,
  headings `#`..`#####` (see specs/T0.7-markdown-convention.md);
  axioms §4 and validation rules §7, plus the goal / means-end rule (T0.4)
  and the APQC crosswalk presence rule (T0.2).

Usage:
  python engine.py <path>            # path = library file or folder
  python engine.py <path> --json out.json
  python engine.py <path> --vocab <vocabulary-spec.md>
  python engine.py <path> --all      # include specs/ and _-prefixed files

Default folder behaviour: parse every *.md under <path>, skipping any path
segment named `specs` and files whose name starts with `_`.

Exit code 0 = VALID (no ERROR), 1 = INVALID, 2 = usage/IO error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# --------------------------------------------------------------------------
# Regexes (Markdown convention, T0.7)
# --------------------------------------------------------------------------
HEAD_RE = re.compile(r"^(#{1,5})\s+(.*?)\s*$")
GROUP_RE = re.compile(r"^Группа\s+([A-Z][A-Z0-9_-]*)\s*:\s*(.+?)\s*$")
PROC_RE = re.compile(r"^Процесс\s+([A-Z][A-Z0-9_-]*)\s*:\s*(.+?)\s*$")
SUB_RE = re.compile(r"^Подпроцесс\s+([A-Z][A-Z0-9_-]*)\s*:\s*(.+?)\s*$")
OP_RE = re.compile(r"^Операция\s+([A-Z][A-Z0-9_-]*)\s*:\s*(.+?)\s*$")
OPCONTAINER_RE = re.compile(r"^Операции подпроцесса\s+([A-Z][A-Z0-9_-]*)\s*:\s*$")
CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]*(-[0-9]{2})+$")
ATTR_RE = re.compile(r"^\*\*([^*:]+):\*\*\s*(.*?)\s*$")
ATTR_IT_RE = re.compile(r"^\*([^*:]+):\*\s*(.*?)\s*$")
BULLET_RE = re.compile(r"^-\s+\*\*([^*:]+):\*\*\s*(.*?)\s*$")
BULLET_PLAIN_RE = re.compile(r"^[\s\t]*-\s*([^:]+):\s*(.*?)\s*$")
NUM_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+\*\*(.+?)\*\*\s*$")
LINK_TOKEN_RE = re.compile(r"^([A-Z][A-Z0-9_]*(-[0-9]{2})+)[.,]\s*(.+?)\s*$")

LEVELS = ["LIBRARY", "GROUP", "PROCESS", "SUBPROCESS", "OPERATION"]
LEVEL_BY_DEPTH = {1: "LIBRARY", 2: "GROUP", 3: "PROCESS", 4: "SUBPROCESS", 5: "OPERATION"}
VALID_OP_TYPES = {"Simple", "Splitter", "Joiner", "Multiplicator", "Aggregator"}
# Operation economics / decomposition domains (T0.5 Decision 1, T0.6 Decision 2).
VALID_CRITICALITY = {"high", "medium", "low"}
VALID_DECOMPOSITION = {"ATOMIC", "DECOMPOSABLE", "PARTIALLY_DECOMPOSABLE"}
PERIODICITY_RE = re.compile(r"^(?:year|quarter|month|week|day|shift|event)\s*×\s*\d+$")
LABOUR_RE = re.compile(r"^\d+(?:[.,]\d+)?\s*ч$")
COST_RE = re.compile(r"^\d+(?:[.,]\d+)?\s*руб$")


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def aget(attrs: dict, *keys):
    for k in keys:
        if k in attrs and str(attrs[k]).strip():
            return str(attrs[k]).strip()
    return None


class Node:
    def __init__(self, code, name, level, parent=None):
        self.code = code
        self.name = name
        self.level = level
        self.parent = parent
        self.children = []
        self.attrs = {}
        self.io_in = []       # list of {'raw','kind','base'}
        self.io_out = []
        self.source = ""      # relative file path

    def goal(self):
        if self.level == "LIBRARY":
            return aget(self.attrs, "Цель библиотеки", "Цель")
        if self.level == "GROUP":
            return aget(self.attrs, "Цель группы", "Цель")
        return aget(self.attrs, "Цель")

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "level": self.level,
            "parent": self.parent.code if self.parent else None,
            "attrs": self.attrs,
            "io_in": self.io_in,
            "io_out": self.io_out,
            "children": [c.code for c in self.children],
            "source": self.source,
        }


class Library:
    def __init__(self):
        self.root = Node("LIBRARY", "Библиотека процессов", "LIBRARY")
        self.by_code = {}
        self.links = []       # {'src','src_type','dst','dst_type','cond'}
        self.errors = []
        self.warnings = []

    def add(self, node: Node):
        if node.level != "LIBRARY":
            if node.code in self.by_code:
                self.errors.append(f"DUPLICATE CODE {node.code} (in {node.source} and "
                                   f"{self.by_code[node.code].source}) §7.9")
            self.by_code[node.code] = node


# --------------------------------------------------------------------------
# Vocabulary (T0.3)
# --------------------------------------------------------------------------
def load_vocabulary(path):
    """Extract the first ```json block declaring entity-state types."""
    if not path or not os.path.exists(path):
        return None
    text = open(path, encoding="utf-8").read()
    for m in re.finditer(r"```json\s*(.*?)```", text, re.S):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("vocabulary") == "entity-state":
            ids = {t["id"] for t in data["types"]}
            parents = {t["id"]: t.get("parent") for t in data["types"]}
            return {"version": data.get("version"), "ids": ids, "parents": parents}
    return None


# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------
def parse_io(value):
    items = []
    if value is None:
        return items
    v = value.strip()
    if v in ("", "—", "-", "–", "нет", "no"):
        return items
    for p in re.split(r"[;,]", v):
        p = p.strip()
        if not p or p in ("—", "-", "–"):
            continue
        m = re.match(r"^`([^`]+)`$", p)
        if m:
            ref = m.group(1).strip()
            items.append({"raw": ref, "kind": "ref", "base": ref.split("@")[0].strip()})
        else:
            items.append({"raw": p, "kind": "free", "base": None})
    return items


def _collect_attr_block(lines, idx):
    """Collect consecutive attribute lines (bold or legacy italic).

    Leading blank lines are skipped, so a heading may be separated from its
    regulated block by a blank line — the layout every source-file block uses
    (T0.7 Decision 2 as amended). The block itself still ends at the first
    blank or non-matching line.
    """
    attrs = {}
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    while idx < len(lines):
        ln = lines[idx].rstrip("\n")
        s = ln.strip()
        if not s:
            break
        m = ATTR_RE.match(s) or ATTR_IT_RE.match(s)
        if not m:
            break
        attrs[m.group(1).strip()] = m.group(2).strip()
        idx += 1
    return attrs, idx


def parse_text(text, relpath, lib: Library):
    lines = text.split("\n")
    # heading index
    heads = []  # (line_idx, depth, text)
    for i, ln in enumerate(lines):
        m = HEAD_RE.match(ln)
        if m:
            heads.append((i, len(m.group(1)), m.group(2).strip()))
    stack = {0: lib.root, 1: lib.root}

    for h_i, (li, depth, text) in enumerate(heads):
        end = heads[h_i + 1][0] if h_i + 1 < len(heads) else len(lines)
        body = lines[li + 1:end]
        # pop deeper/equal stack levels
        for lv in range(depth, 6):
            stack[lv] = None

        node = None
        container_code = None
        if depth == 1:
            node = lib.root
            if text:
                lib.root.name = text
            a, _ = _collect_attr_block(body, 0)
            lib.root.attrs.update(a)
        elif depth == 2:
            m = GROUP_RE.match(text)
            if m:
                node = Node(m.group(1), m.group(2), "GROUP", stack.get(1) or lib.root)
        elif depth == 3:
            m = PROC_RE.match(text)
            if m:
                node = Node(m.group(1), m.group(2), "PROCESS", stack.get(2))
        elif depth == 4:
            m = SUB_RE.match(text)
            if m:
                node = Node(m.group(1), m.group(2), "SUBPROCESS", stack.get(3))
        elif depth == 5:
            m = OP_RE.match(text)
            mc = OPCONTAINER_RE.match(text)
            if m:
                node = Node(m.group(1), m.group(2), "OPERATION", stack.get(4) or stack.get(3))
                a, _ = _collect_bullet_attrs(body, 0)
                node.attrs.update(a)
                node.io_in = parse_io(aget(a, "Входы", "Вход"))
                node.io_out = parse_io(aget(a, "Выходы", "Выход"))
            elif mc:
                container_code = mc.group(1)
                _parse_container_ops(body, container_code, stack.get(4) or stack.get(3), lib, relpath)

        if node is not None and node.level != "LIBRARY":
            node.source = relpath
            if node.parent is not None:
                node.parent.children.append(node)
            else:
                lib.errors.append(f"DANGLING NODE {node.code} (no parent) §4.7")
            lib.add(node)
            _collect_block_for_node(body, node)
            stack[depth] = node
        elif node is not None:
            stack[depth] = node

        # links in this section
        for ln in body:
            _maybe_link(ln, lib)


def _collect_block_for_node(body, node):
    if node.level in ("GROUP", "PROCESS", "SUBPROCESS"):
        a, _ = _collect_attr_block(body, 0)
        node.attrs.update(a)
        if node.level in ("PROCESS", "SUBPROCESS"):
            node.io_in = parse_io(aget(a, "Входы (из)"))
            node.io_out = parse_io(aget(a, "Выходы (в)"))


def _collect_bullet_attrs(body, idx):
    attrs = {}
    while idx < len(body):
        s = body[idx].strip()
        if not s:
            idx += 1
            continue
        m = BULLET_RE.match(s) or BULLET_PLAIN_RE.match(s)
        if not m:
            break
        attrs[m.group(1).strip()] = m.group(2).strip()
        idx += 1
    return attrs, idx


def _parse_container_ops(body, code, parent, lib, relpath):
    """Legacy `##### Операции подпроцесса CODE:` + numbered list (T0.8 Rule 2)."""
    n = 0
    cur = None
    for ln in body:
        m = NUM_ITEM_RE.match(ln)
        if m:
            n += 1
            opcode = f"{code}-{n:02d}"
            cur = Node(opcode, m.group(2).strip(), "OPERATION", parent)
            cur.source = relpath
            cur.attrs["_legacy"] = "1"
            if parent is not None:
                parent.children.append(cur)
            lib.add(cur)
            continue
        if cur is not None:
            mm = BULLET_PLAIN_RE.match(ln) or BULLET_RE.match(ln)
            if mm:
                k = mm.group(1).strip()
                v = mm.group(2).strip()
                if k:
                    cur.attrs[k] = v
                if k in ("Входы", "Вход"):
                    cur.io_in = parse_io(v)
                elif k in ("Выходы", "Выход"):
                    cur.io_out = parse_io(v)


def _maybe_link(line, lib):
    if "|" not in line:
        return
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 3:
        return
    if cells[1] not in ("→", "->", "⇒"):
        return
    src = LINK_TOKEN_RE.match(cells[0])
    dst = LINK_TOKEN_RE.match(cells[2])
    if not src or not dst:
        return
    lib.links.append({
        "src": src.group(1), "src_type": src.group(3).strip(),
        "dst": dst.group(1), "dst_type": dst.group(3).strip(),
        "cond": cells[3] if len(cells) > 3 else "",
    })


# --------------------------------------------------------------------------
# Validator (§4, §7, T0.4)
# --------------------------------------------------------------------------
def _iter_nodes(lib):
    out = []
    def rec(n):
        if n is not lib.root:
            out.append(n)
        for c in n.children:
            rec(c)
    rec(lib.root)
    return out


def validate(lib: Library, vocab):
    errors, warnings = lib.errors[:], lib.warnings[:]
    nodes = _iter_nodes(lib)

    # --- goals (T0.4) ---
    if lib.root.children and not lib.root.goal():
        errors.append("MISSING GOAL on LIBRARY root (T0.4)")
    for n in nodes:
        if n.level in ("GROUP", "PROCESS", "SUBPROCESS", "OPERATION"):
            if not n.goal():
                errors.append(f"MISSING GOAL on {n.code} ({n.level}) (T0.4)")

    # --- APQC presence on PROCESS (T0.2) ---
    for n in nodes:
        if n.level == "PROCESS" and not aget(n.attrs, "APQC"):
            errors.append(f"MISSING APQC on PROCESS {n.code} (T0.2)")

    # --- hierarchy (§4.7, §4.9, §4.10) ---
    for n in nodes:
        if n.level == "OPERATION":
            if n.children:
                errors.append(f"OPERATION {n.code} has children §4.7")
            if n.parent is None or n.parent.level not in ("PROCESS", "SUBPROCESS"):
                errors.append(f"OPERATION {n.code} not under PROCESS/SUBPROCESS §4.9")
        if n.level == "PROCESS" and not _has_op(n):
            errors.append(f"PROCESS {n.code} has no operations §4.10")
        if n.level == "SUBPROCESS" and not _has_op(n):
            errors.append(f"SUBPROCESS {n.code} has no operations §4.10")

    ops = [n for n in nodes if n.level == "OPERATION"]

    # --- typing (§7.1) + free-text warnings (T0.8) ---
    ids = vocab["ids"] if vocab else None
    for op in ops:
        for side, items in (("in", op.io_in), ("out", op.io_out)):
            for it in items:
                if it["kind"] == "free":
                    warnings.append(f"FREE-TEXT I/O on {op.code} ({side}): "
                                    f"'{it['raw']}' — convert to vocabulary ref (T0.8)")
                elif it["kind"] == "ref" and ids is not None and it["base"] not in ids:
                    errors.append(f"UNKNOWN TYPE '{it['base']}' on {op.code} ({side}) §7.1")

    # --- cardinality / boundary (§4.1) ---
    for op in ops:
        nin, nout = len(op.io_in), len(op.io_out)
        boundary = (nin == 0) or (nout == 0)
        if not boundary and (nin < 1 or nout < 1):
            errors.append(f"FLOW CONSERVATION on {op.code}: in={nin} out={nout} §4.1")
        if nin == 0 and nout == 0:
            errors.append(f"ISOLATED OPERATION {op.code}: in=0 out=0 §4.1")
        # type matrix (§3) — warnings only
        t = aget(op.attrs, "Тип")
        if t and not boundary and t in VALID_OP_TYPES:
            ok = _type_matrix_ok(t, nin, nout)
            if not ok:
                warnings.append(f"TYPE-CARDINALITY mismatch on {op.code}: "
                                f"{t} in={nin} out={nout} §3")

    # --- economics / decomposition domains (T0.5, T0.6) ---
    # Optional attributes: validated for format only when present.
    for op in ops:
        crit = aget(op.attrs, "Критичность")
        if crit and crit not in VALID_CRITICALITY:
            errors.append(f"BAD CRITICALITY '{crit}' on {op.code} (T0.5)")
        peri = aget(op.attrs, "Периодичность")
        if peri and not PERIODICITY_RE.match(peri):
            errors.append(f"BAD PERIODICITY '{peri}' on {op.code} (T0.5)")
        lab = aget(op.attrs, "Трудоёмкость")
        if lab and not LABOUR_RE.match(lab):
            errors.append(f"BAD LABOUR '{lab}' on {op.code} (T0.5)")
        cost = aget(op.attrs, "Стоимость")
        if cost and not COST_RE.match(cost):
            errors.append(f"BAD COST '{cost}' on {op.code} (T0.5)")
        dec = aget(op.attrs, "decomposition")
        if dec and dec not in VALID_DECOMPOSITION:
            errors.append(f"BAD DECOMPOSITION '{dec}' on {op.code} (T0.6)")

    # --- flow links (§4.2, §4.5) ---
    op_by_code = {o.code: o for o in ops}
    used_out, used_in = set(), set()
    for lk in lib.links:
        used_out.add((lk["src"], norm(lk["src_type"])))
        used_in.add((lk["dst"], norm(lk["dst_type"])))
        if lk["src"] not in op_by_code:
            errors.append(f"LINK source {lk['src']} is not an OPERATION §4.8")
        if lk["dst"] not in op_by_code:
            errors.append(f"LINK target {lk['dst']} is not an OPERATION §4.8")

    for op in ops:
        nin, nout = len(op.io_in), len(op.io_out)
        is_sensor = (nin == 0 and nout >= 1)
        is_actor = (nout == 0 and nin >= 1)
        if not is_actor:
            for it in op.io_out:
                if (op.code, norm(it["raw"])) not in used_out:
                    errors.append(f"DANGLING output {op.code}.{it['raw']} not consumed §4.2")
        if not is_sensor:
            for it in op.io_in:
                if (op.code, norm(it["raw"])) not in used_in:
                    errors.append(f"DANGLING input {op.code}.{it['raw']} not provided §4.2")

    _check_cycles(ops, lib.links, errors)

    # --- duplicates (§7.9) ---
    seen = {}
    for op in ops:
        key = (frozenset(norm(i["raw"]) for i in op.io_in),
               frozenset(norm(i["raw"]) for i in op.io_out))
        if key in seen:
            warnings.append(f"POSSIBLE DUPLICATE: {op.code} ~ {seen[key]} §7.9")
        seen[key] = op.code

    return errors, warnings


def _has_op(node):
    return any(c.level == "OPERATION" for c in _descendants(node))


def _descendants(n):
    out = []
    for c in n.children:
        out.append(c)
        out.extend(_descendants(c))
    return out


def _type_matrix_ok(t, nin, nout):
    return {
        "Simple": nin == 1 and nout == 1,
        "Splitter": nin == 1 and nout >= 2,
        "Joiner": nin >= 2 and nout == 1,
        "Multiplicator": nin >= 1 and nout >= 1,
        "Aggregator": nin >= 2 and nout == 1,
    }[t]


def _check_cycles(ops, links, errors):
    adj = {}
    for lk in links:
        adj.setdefault(lk["src"], set()).add(lk["dst"])
    # simple Tarjan-ish SCC via Kosaraju
    nodes = [o.code for o in ops]
    idx = {}
    st = []
    on = set()
    comps = []

    def strong(v):
        idx[v] = len(idx)
        low = idx[v]
        st.append(v); on.add(v)
        for w in adj.get(v, ()):  # noqa
            if w not in idx:
                low = min(low, strong(w))
            elif w in on:
                low = min(low, idx[w])
        if low == idx[v]:
            comp = []
            while True:
                w = st.pop(); on.discard(w); comp.append(w)
                if w == v:
                    break
            comps.append(comp)
        return low

    sys.setrecursionlimit(10000)
    for v in nodes:
        if v not in idx:
            strong(v)
    for comp in comps:
        if len(comp) > 1:
            members = set(comp)
            has_exit = any(w not in members for v in comp for w in adj.get(v, ()))
            if not has_exit:
                errors.append(f"CYCLE WITHOUT EXIT: {sorted(comp)} §4.5")


# --------------------------------------------------------------------------
# Signature (for split regression, T1.1)
# --------------------------------------------------------------------------
def graph_signature(lib: Library):
    nodes, edges = [], []
    for n in _iter_nodes(lib):
        nodes.append((n.code, n.level, n.parent.code if n.parent else None))
    for lk in lib.links:
        edges.append((lk["src"], norm(lk["src_type"]), lk["dst"], norm(lk["dst_type"])))
    return {"nodes": sorted(nodes), "edges": sorted(edges)}


# --------------------------------------------------------------------------
# IO + CLI
# --------------------------------------------------------------------------
def collect_files(path, include_all=False):
    if os.path.isfile(path):
        return [path]
    out = []
    for root, dirs, files in os.walk(path):
        if not include_all:
            dirs[:] = [d for d in dirs if d != "specs"]
        for fn in files:
            if not fn.endswith(".md"):
                continue
            if not include_all and fn.startswith("_"):
                continue
            out.append(os.path.join(root, fn))
    return sorted(out)


def parse_paths(path, include_all=False):
    lib = Library()
    for fp in collect_files(path, include_all):
        rel = os.path.relpath(fp, path if os.path.isdir(path) else os.path.dirname(path))
        try:
            text = open(fp, encoding="utf-8").read()
        except Exception as e:
            lib.errors.append(f"READ ERROR {rel}: {e}")
            continue
        parse_text(text, rel, lib)
    return lib


def _counts(lib):
    c = {k: 0 for k in LEVELS}
    c["LIBRARY"] = 1
    for n in _iter_nodes(lib):
        c[n.level] = c.get(n.level, 0) + 1
    return c


def _find_vocab(base, explicit):
    if explicit:
        return explicit
    name = os.path.join("specs", "T0.3-entity-state-vocabulary.md")
    for cand in (os.path.join(base, name),
                 os.path.join(os.path.dirname(base), name)):
        if os.path.exists(cand):
            return cand
    return os.path.join(base, name)


def main(argv=None):
    try:  # Windows consoles default to cp1251; Cyrillic output must not crash.
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Process-library parser + validator")
    ap.add_argument("path")
    ap.add_argument("--json")
    ap.add_argument("--vocab")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args(argv)

    if not os.path.exists(args.path):
        print(f"ERROR: path not found: {args.path}")
        return 2

    base = args.path if os.path.isdir(args.path) else os.path.dirname(args.path)
    # Folder mode is scoped to the library/ subfolder (T0.7 Decision 6);
    # an absent library/ yields an empty (valid) graph.
    target = args.path if os.path.isfile(args.path) else os.path.join(base, "library")
    vocab = load_vocabulary(_find_vocab(base, args.vocab))

    lib = parse_paths(target, args.all)
    errors, warnings = validate(lib, vocab)

    c = _counts(lib)
    print(f"Parsed: {c['GROUP']} groups, {c['PROCESS']} processes, "
          f"{c['SUBPROCESS']} subprocesses, {c['OPERATION']} operations, "
          f"{len(lib.links)} links")
    print(f"Vocabulary: {'v' + str(vocab['version']) if vocab else 'NOT FOUND'} "
          f"({len(vocab['ids']) if vocab else 0} types)")
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings[:50]:
            print(f"  - {w}")
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors[:50]:
            print(f"  - {e}")
    print("\n" + ("VALID" if not errors else "INVALID"))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({
                "signature": graph_signature(lib),
                "root": lib.root.to_dict(),
                "nodes": [n.to_dict() for n in _iter_nodes(lib)],
                "links": lib.links,
                "errors": errors,
                "warnings": warnings,
            }, f, ensure_ascii=False, indent=2)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
