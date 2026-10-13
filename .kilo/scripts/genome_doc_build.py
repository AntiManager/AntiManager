"""Fill the /genome/role/ partial from the vault role documents.

Reads the unified РП documents from the process-library vault and renders them as
HTML into site/src/content/genome/role.html, replacing everything between the
<!--KU:START-->…<!--KU:END--> and <!--PROFILE:START-->…<!--PROFILE:END--> markers.
Idempotent: re-run after vault edits; the page shell (hero/nav/sections) is left
untouched. Vendored into the repo so `node build.js` stays vault-independent — run
this by hand when the vault source changes, then commit the regenerated partial.

Requires the local Obsidian vault (path below). Not part of the site build.

Usage: python .kilo/scripts/genome_doc_build.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
VAULT = Path(r"C:\Users\evgeniy.bogdanov\Documents\Personal Vault\Библиотека процессов\library\org")
KU = VAULT / "КУ_руководителей" / "РП_оценка_КУ.md"
KU_APP = VAULT / "КУ_руководителей" / "РП_оценка_КУ_прил.md"
PROFILE = VAULT / "profiles" / "РП_profile.md"
TARGET = HERE / "site" / "src" / "content" / "genome" / "role.html"

H = re.compile(r"^(#{1,6})\s+(.*)$")
UL = re.compile(r"^[-*]\s+(.*)$")
OL = re.compile(r"^\d+[.)]\s+(.*)$")
SEP = re.compile(r"^:?-{2,}:?$")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s):
    s = re.sub(r"\\([!-/:-@\[-`{-~])", r"\1", s)
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
               lambda m: '<a href="%s">%s</a>' % (m.group(2).replace('"', "&quot;"), m.group(1)), s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", s)
    return s.strip()


def indent_of(line):
    return len(line[: len(line) - len(line.lstrip(" \t"))].replace("\t", "    "))


def render_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    sep = 1 if len(cells) > 1 and all(SEP.fullmatch(c) for c in cells[1]) else 0
    head, data = cells[0], cells[2:] if sep else cells[1:]
    t = ['<div class="table-wrap doc-table">', "<table>", "<thead>",
         "<tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr>",
         "</thead>", "<tbody>"]
    for row in data:
        t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
    t += ["</tbody>", "</table>", "</div>"]
    return "\n".join(t)


def render_list(block):
    tokens = []
    for line in block:
        s = line.strip()
        if s == "":
            continue
        if OL.match(s):
            tokens.append([indent_of(line), True, OL.match(s).group(1)])
        elif UL.match(s):
            tokens.append([indent_of(line), False, UL.match(s).group(1)])
        elif tokens:
            tokens[-1][2] += " " + s
        else:
            tokens.append([indent_of(line), False, s])
    root = {"children": []}
    stack = [(-1, root)]
    for indent, ordered, text in tokens:
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        node = {"ordered": ordered, "text": text, "children": []}
        stack[-1][1]["children"].append(node)
        stack.append((indent, node))

    def emit(nodes):
        html, i = "", 0
        while i < len(nodes):
            ordered = nodes[i]["ordered"]
            group = []
            while i < len(nodes) and nodes[i]["ordered"] == ordered:
                group.append(nodes[i])
                i += 1
            tag = "ol" if ordered else "ul"
            items = "".join(f"<li>{inline(n['text'])}{emit(n['children'])}</li>" for n in group)
            html += f"<{tag}>{items}</{tag}>"
        return html

    return emit(root["children"])


def render_blocks(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        raw, s = lines[i], lines[i].strip()
        if s == "":
            i += 1
            continue
        if s == "---":
            out.append("<hr>")
            i += 1
            continue
        m = H.match(s)
        if m:
            lvl = min(len(m.group(1)) + 1, 6)
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(render_table(rows))
            continue
        if s.startswith(">"):
            q = []
            while i < n and lines[i].strip().startswith(">"):
                t = lines[i].strip()[1:]
                q.append(t[1:] if t.startswith(" ") else t)
                i += 1
            out.append("<blockquote>" + render_blocks(q) + "</blockquote>")
            continue
        if UL.match(s) or OL.match(s):
            block = []
            while i < n:
                cur = lines[i]
                cs = cur.strip()
                if cs == "":
                    if i + 1 < n and (UL.match(lines[i + 1].strip()) or OL.match(lines[i + 1].strip())
                                      or indent_of(lines[i + 1]) > 0):
                        block.append(cur)
                        i += 1
                        continue
                    break
                if UL.match(cs) or OL.match(cs) or indent_of(cur) > 0:
                    block.append(cur)
                    i += 1
                    continue
                break
            out.append(render_list(block))
            continue
        para = []
        while i < n:
            cs = lines[i].strip()
            if cs == "" or cs == "---" or H.match(cs) or cs.startswith("|") or cs.startswith(">") \
                    or UL.match(cs) or OL.match(cs):
                break
            para.append(cs)
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)


def convert(path, drop_first_h1=True):
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        lines = lines[i + 1:]
    if drop_first_h1:
        for k, ln in enumerate(lines):
            if ln.strip() == "":
                continue
            if ln.startswith("# "):
                lines = lines[:k] + lines[k + 1:]
            break
    return render_blocks(lines)


def fill(html, tag, content):
    start, end = f"<!--{tag}:START-->", f"<!--{tag}:END-->"
    assert start in html and end in html, f"markers missing: {tag}"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    return pattern.sub(lambda m: start + "\n" + content + "\n" + end, html, count=1)


def main():
    ku = convert(KU) + "\n" + convert(KU_APP)
    profile = convert(PROFILE)
    html = TARGET.read_text(encoding="utf-8")
    html = fill(html, "KU", ku)
    html = fill(html, "PROFILE", profile)
    TARGET.write_text(html, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.name}: ku={len(ku)}ch profile={len(profile)}ch total={len(html)}ch",
          file=sys.stderr)


if __name__ == "__main__":
    main()
