"""Convert a vault book article (Markdown) into a site full-text partial (HTML).

Drops: frontmatter, the title block, the manual Оглавление, the trailing
«Связанные инструменты/главы» sections, and `---` separators.
Maps: `## ` -> <h2> (opens a <section>), `### ` -> <h3>, `#### ` -> <h4>,
`##### ` -> <h5>. Supports paragraphs, ul/ol lists, tables, blockquotes,
`**bold**`, `*italic*` and `[[wiki|links]]`.

Usage:
  python md_to_partial.py <input.md> <output.html> ["source comment"]
"""
import re
import sys


def inline(s):
    # Markdown backslash escapes (CommonMark): a backslash before ASCII
    # punctuation yields the literal symbol, so `1\.` and `повысить\_приоритет`
    # must not leak the backslash into the HTML.
    s = re.sub(r'\\([!-/:-@\[-`{-~])', r'\1', s)
    s = (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    # wiki links
    s = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', s)
    s = re.sub(r'\[\[([^\]]+)\]\]', r'\1', s)
    # bold then italic
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', s)
    return s.strip()


H = re.compile(r'^(#{1,6})\s+(.*)$')
UL = re.compile(r'^\s*-\s+(.*)$')
OL = re.compile(r'^\s*(\d+)\.\s+(.*)$')


def is_continuation(line):
    """An indented, non-blank line that continues the previous list item
    (a hard-break/indented follow-up), not a new block."""
    if not line or line[0] not in (' ', '\t'):
        return False
    t = line.strip()
    if not t:
        return False
    return not (H.match(t) or t.startswith('|') or t.startswith('>') or UL.match(t) or OL.match(t))


def convert(md_text):
    lines = md_text.replace('\r\n', '\n').split('\n')
    # strip frontmatter
    assert lines[0].strip() == '---', 'expected frontmatter'
    i = 1
    while lines[i].strip() != '---':
        i += 1
    body = lines[i + 1:]
    # Drop the title block. When a manual Оглавление exists, drop through the
    # '---' that follows it; otherwise drop through the first '---' (articles
    # that open directly with their first section).
    oi = next((k for k, l in enumerate(body) if re.match(r'^#{1,3}\s*Оглавление\s*$', l.strip())), None)
    j = oi + 1 if oi is not None else 0
    while j < len(body) and body[j].strip() != '---':
        j += 1
    body = body[j + 1:]

    out = []
    sec = [False]

    def close_sec():
        if sec[0]:
            out.append('</section>')
            sec[0] = False

    n = len(body)
    k = 0
    while k < n:
        line = body[k]
        stripped = line.strip()
        if stripped == '':
            k += 1
            continue
        if stripped == '---':
            k += 1
            continue
        if re.match(r'^#{2,3}\s+Связанные', stripped):
            break
        m = H.match(stripped)
        if m:
            level = len(m.group(1))
            txt = inline(m.group(2))
            if level <= 2:
                close_sec()
                out.append('<section>')
                out.append('')
                out.append(f'<h2>{txt}</h2>')
                out.append('')
                sec[0] = True
            else:
                out.append(f'<h{level}>{txt}</h{level}>')
                out.append('')
            k += 1
            continue
        if stripped.startswith('|'):
            rows = []
            while k < n and body[k].strip().startswith('|'):
                rows.append(body[k].strip())
                k += 1
            cells = [r.strip('|').split('|') for r in rows]
            cells = [[c.strip() for c in row] for row in cells]
            sep = 1 if len(cells) > 1 and all(re.fullmatch(r':?-{2,}:?', c) for c in cells[1]) else 0
            head = cells[0]
            data = cells[2:] if sep else cells[1:]
            t = ['<div class="table-wrap">', '<table>', '<thead>',
                 '<tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr>',
                 '</thead>', '<tbody>']
            for row in data:
                t.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in row) + '</tr>')
            t += ['</tbody>', '</table>', '</div>', '']
            out.extend(t)
            continue
        if re.match(r'^>', stripped):
            paras = []
            while k < n and body[k].strip().startswith('>'):
                q = body[k].strip()[1:].strip()
                if q == '':
                    k += 1
                    continue
                paras.append(q)
                k += 1
            out.append('<blockquote>' + ''.join(f'<p>{inline(p)}</p>' for p in paras) + '</blockquote>')
            out.append('')
            continue
        if UL.match(stripped):
            items = []
            while k < n:
                ss = body[k].strip()
                if UL.match(ss):
                    items.append(UL.match(ss).group(1))
                    k += 1
                elif items and is_continuation(body[k]):
                    items[-1] += ' ' + ss
                    k += 1
                else:
                    break
            out.append('<ul>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul>')
            out.append('')
            continue
        if OL.match(stripped):
            items = []
            start = int(OL.match(stripped).group(1))
            while k < n:
                ss = body[k].strip()
                if OL.match(ss):
                    items.append(OL.match(ss).group(2))
                    k += 1
                elif items and is_continuation(body[k]):
                    items[-1] += ' ' + ss
                    k += 1
                else:
                    break
            attr = f' start="{start}"' if start != 1 else ''
            out.append(f'<ol{attr}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ol>')
            out.append('')
            continue
        # paragraph: gather until blank or block start
        paras = []
        while k < n:
            s = body[k].strip()
            if s == '' or s == '---' or H.match(s) or s.startswith('|') or s.startswith('>') \
                    or UL.match(s) or OL.match(s) or re.match(r'^#{2,3}\s+Связанные', s):
                break
            paras.append(s)
            k += 1
        out.append('<p>' + inline(' '.join(paras)) + '</p>')
        out.append('')
    close_sec()
    return '\n'.join(out).rstrip() + '\n'


def main():
    src, dst = sys.argv[1], sys.argv[2]
    comment = sys.argv[3] if len(sys.argv) > 3 else ''
    with open(src, 'r', encoding='utf-8') as f:
        md = f.read()
    html = convert(md)
    header = f'<!-- {comment} -->\n' if comment else ''
    with open(dst, 'w', encoding='utf-8', newline='\n') as f:
        f.write(header + html)
    print('wrote', dst, len(html), 'bytes')


if __name__ == '__main__':
    main()
