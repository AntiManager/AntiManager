# -*- coding: utf-8 -*-
"""Assemble the unified public A3 regulation from the two vault draft editions.

Input (vault root, read-only):
  * "Регламент работа с формой А3 (финальная версия).md"  (edition 3, base)
Output:
  * "<vault>/Методология ПС/Типовые документы/Форма-А3.md" (public note)

Transforms on the base edition:
  * frontmatter + publication header block (version, date, license, owner);
  * empty П1-П16 parameter cells -> "задаёт предприятие" (no figures);
  * \[П<n>\] code references -> "по параметру П<n> (см. п. 3.3)";
  * escaped punctuation (\\_ \\[ \\]) unescaped for GFM;
  * an annotation block after the title;
  * a concrete header row for the blank А3 form table (Приложение Б);
  * appendix H3 headings promoted to H2 (site table of contents).

The script reads the original from the vault root and writes a brand-new note,
so it can be re-run after the source changes.
"""
import io
import os
import re

VAULT = os.path.join(os.environ['USERPROFILE'], 'Documents', 'Personal Vault')
# The two draft editions were moved out of the vault root on 2026-11-04
# (Archive/Исходники А3/). The edition-3 regulation stays the generation base.
SRC_DIR = os.path.join(VAULT, 'Archive', '\u0418\u0441\u0445\u043e\u0434\u043d\u0438\u043a\u0438 \u04103')
BASE = os.path.join(SRC_DIR, '\u0420\u0435\u0433\u043b\u0430\u043c\u0435\u043d\u0442 \u0440\u0430\u0431\u043e\u0442\u0430 \u0441 '
                              '\u0444\u043e\u0440\u043c\u043e\u0439 \u04103 (\u0444\u0438\u043d\u0430\u043b\u044c\u043d\u0430\u044f '
                              '\u0432\u0435\u0440\u0441\u0438\u044f).md')
DOC_DIR = os.path.join(VAULT, '\u041c\u0435\u0442\u043e\u0434\u043e\u043b\u043e\u0433\u0438\u044f \u041f\u0421',
                       '\u0422\u0438\u043f\u043e\u0432\u044b\u0435 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b')
OUT = os.path.join(DOC_DIR, '\u0424\u043e\u0440\u043c\u0430-\u04103.md')

TODAY = '2026-11-04'

FRONTMATTER = """---
tags: [\u043c\u0435\u0442\u043e\u0434\u043e\u043b\u043e\u0433\u0438\u044f, \u0442\u0438\u043f\u043e\u0432\u043e\u0439-\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442, a3, \u0440\u0435\u0448\u0435\u043d\u0438\u0435-\u043f\u0440\u043e\u0431\u043b\u0435\u043c]
status: published
created: {today}
updated: {today}
version: "1.0"
owner: AntiManager
license: CC BY-SA 4.0
library: documents
public: true
aliases: [\u0424\u043e\u0440\u043c\u0430 \u04103, A3, \u04103, \u0424\u043e\u0440\u043c\u0430 \u04103 \u0440\u0435\u0448\u0435\u043d\u0438\u0435 \u043f\u0440\u043e\u0431\u043b\u0435\u043c, \u041c\u0435\u0442\u043e\u0434 \u04103]
---
"""

TITLE = ('# \u0424\u043e\u0440\u043c\u0430 \u04103: \u0440\u0435\u0448\u0435\u043d\u0438\u0435 \u043f\u0440\u043e\u0431\u043b\u0435\u043c \u0438 '
         '\u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u0438\u0439 \u0432 \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0439 '
         '\u0441\u0438\u0441\u0442\u0435\u043c\u0435\n\n'
         '**\u0412\u0435\u0440\u0441\u0438\u044f:** 1.0 \u00b7 **\u0421\u0442\u0430\u0442\u0443\u0441:** '
         '\u043f\u0443\u0431\u043b\u0438\u0447\u043d\u044b\u0439 \u0448\u0430\u0431\u043b\u043e\u043d \u00b7 '
         '**\u0414\u0430\u0442\u0430:** 04.11.2026 \u00b7 **\u041b\u0438\u0446\u0435\u043d\u0437\u0438\u044f:** '
         'CC BY-SA 4.0 \u00b7 **\u0412\u043b\u0430\u0434\u0435\u043b\u0435\u0446:** AntiManager\n\n'
         '---\n\n')

ANNOTATION = """## \u0410\u043d\u043d\u043e\u0442\u0430\u0446\u0438\u044f

\u041c\u0435\u0442\u043e\u0434\u0438\u043a\u0430 \u043e\u043f\u0438\u0441\u044b\u0432\u0430\u0435\u0442, \u043a\u0430\u043a \u043f\u0440\u0438\u043c\u0435\u043d\u044f\u0442\u044c \u0444\u043e\u0440\u043c\u0443 \u04103 \u0434\u043b\u044f \u0441\u0438\u0441\u0442\u0435\u043c\u043d\u043e\u0433\u043e \u0440\u0435\u0448\u0435\u043d\u0438\u044f \u043f\u043e\u0432\u0442\u043e\u0440\u044f\u044e\u0449\u0438\u0445\u0441\u044f \u043f\u0440\u043e\u0431\u043b\u0435\u043c \u0438 \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u0438\u0439: \u043e\u0442 \u043d\u0430\u0431\u043b\u044e\u0434\u0435\u043d\u0438\u044f \u0432 \u0433\u0435\u043c\u0431\u0430 \u0434\u043e \u0437\u0430\u043a\u0440\u0435\u043f\u043b\u0435\u043d\u0438\u044f \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u0430 \u0441\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043e\u043c.

**\u0414\u043b\u044f \u043a\u043e\u0433\u043e:** \u0440\u0443\u043a\u043e\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u0438 \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0441\u0442\u0432, \u043d\u0430\u0447\u0430\u043b\u044c\u043d\u0438\u043a\u0438 \u0446\u0435\u0445\u043e\u0432 \u0438 \u0443\u0447\u0430\u0441\u0442\u043a\u043e\u0432, \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0441\u0442\u044b \u043f\u043e \u0440\u0430\u0437\u0432\u0438\u0442\u0438\u044e \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0439 \u0441\u0438\u0441\u0442\u0435\u043c\u044b, \u043d\u0430\u0441\u0442\u0430\u0432\u043d\u0438\u043a\u0438 \u0438 \u0430\u0432\u0442\u043e\u0440\u044b \u04103.

**\u041a\u0430\u043a \u044d\u0442\u043e \u0443\u0441\u0442\u0440\u043e\u0435\u043d\u043e:** \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442 \u0442\u0438\u043f\u043e\u0432\u043e\u0439. \u0417\u043d\u0430\u0447\u0435\u043d\u0438\u044f, \u043a\u043e\u0442\u043e\u0440\u044b\u0435 \u043f\u0440\u0435\u0434\u043f\u0440\u0438\u044f\u0442\u0438\u0435 \u0437\u0430\u0434\u0430\u0451\u0442 \u0441\u0430\u043c\u043e, \u0441\u043e\u0431\u0440\u0430\u043d\u044b \u0432 \u0442\u0430\u0431\u043b\u0438\u0446\u0435 \u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u043e\u0432 (\u043f. 3.3) \u043f\u043e\u0434 \u043a\u043e\u0434\u0430\u043c\u0438 \u041f1\u2013\u041f16. \u0410\u0434\u0430\u043f\u0442\u0430\u0446\u0438\u044f \u0441\u0432\u043e\u0434\u0438\u0442\u0441\u044f \u043a \u0437\u0430\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u044e \u044d\u0442\u043e\u0439 \u0442\u0430\u0431\u043b\u0438\u0446\u044b \u043e\u0434\u0438\u043d \u0440\u0430\u0437 \u043f\u0440\u0438\u043a\u0430\u0437\u043e\u043c \u2014 \u0431\u0435\u0437 \u043f\u0440\u0430\u0432\u043a\u0438 \u0442\u0435\u043a\u0441\u0442\u0430 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430.

---

"""


def read(path):
    with io.open(path, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def unescape(text):
    """Drop CommonMark backslash escapes left by the drafting tool."""
    return re.sub(r'\\([!-/:-@\[-`{-~])', r'\1', text)


def fix_params_table(text):
    """Fill the П1-П16 parameter cells: empty -> 'задаёт предприятие'."""
    lines = text.split('\n')
    out = []
    in_table = False
    filled = 0
    for line in lines:
        s = line.strip()
        if s.startswith('| \u041a\u043e\u0434 |') and '\u041f\u0430\u0440\u0430\u043c\u0435\u0442\u0440' in s:
            in_table = True
            out.append(line)
            continue
        if in_table:
            if s.startswith('|'):
                cells = [c.strip() for c in s.strip('|').split('|')]
                if len(cells) == 3 and re.fullmatch(r'\u041f\d+', cells[0]):
                    if cells[2] == '':
                        cells[2] = '\u0437\u0430\u0434\u0430\u0451\u0442 \u043f\u0440\u0435\u0434\u043f\u0440\u0438\u044f\u0442\u0438\u0435'
                        filled += 1
                    out.append('| ' + ' | '.join(cells) + ' |')
                    continue
                out.append(line)
                continue
            in_table = False
        out.append(line)
    return '\n'.join(out), filled


def fix_param_refs(text):
    """'[П<n>]'-style bare codes -> a readable reference to the parameters table.

    The bare code is replaced by just the code (the table in 3.3 is named once
    in the annotation), so prepositions in the source keep reading naturally:
    "\u0441\u0432\u044b\u0448\u0435 [\u041f2]" -> "\u0441\u0432\u044b\u0448\u0435 \u041f2"; "\u0442\u0435\u0447\u0435\u043d\u0438\u0435 [\u041f3] \u0441\u043c\u0435\u043d" -> "\u0442\u0435\u0447\u0435\u043d\u0438\u0435 \u041f3 \u0441\u043c\u0435\u043d".
    """
    return re.sub(r'\[(\u041f\d+)\]', r'\1', text)


def fix_header_row(text):
    """Give the blank А3 form (Приложение Б) a real header row."""
    lines = text.split('\n')
    out = []
    done = False
    for line in lines:
        if not done and line.strip().startswith('| \u0428\u0430\u043f\u043a\u0430:'):
            out.append('| \u0428\u0430\u043f\u043a\u0430 \u04103 | \u0417\u0430\u043f\u043e\u043b\u043d\u044f\u0435\u0442\u0441\u044f |')
            out.append('| --- | --- |')
            out.append('| \u2116 \u043f\u043e \u0440\u0435\u0435\u0441\u0442\u0440\u0443 | \u2014 |')
            out.append('| \u041f\u043e\u0434\u0440\u0430\u0437\u0434\u0435\u043b\u0435\u043d\u0438\u0435, \u0443\u0447\u0430\u0441\u0442\u043e\u043a, \u043b\u0438\u043d\u0438\u044f | \u2014 |')
            out.append('| \u0414\u0430\u0442\u0430 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0439 \u0432\u0435\u0440\u0441\u0438\u0438 | \u2014 |')
            out.append('| \u0410\u0432\u0442\u043e\u0440 (\u043b\u0438\u0434\u0435\u0440) | \u2014 |')
            out.append('| \u0423\u0447\u0430\u0441\u0442\u043d\u0438\u043a\u0438 | \u043c\u0438\u043d\u0438\u043c\u0443\u043c \u0430\u0432\u0442\u043e\u0440 \u0438 \u043e\u0434\u0438\u043d \u0443\u0447\u0430\u0441\u0442\u043d\u0438\u043a |')
            out.append('| \u041d\u0430\u0441\u0442\u0430\u0432\u043d\u0438\u043a | \u2014 |')
            out.append('| \u0423\u0440\u043e\u0432\u0435\u043d\u044c | 1 \u00b7 2 \u00b7 3 (\u043f. 6.2) |')
            done = True
            continue
        out.append(line)
    if not done:
        raise SystemExit('ERROR: header row not found')
    # The blank form's own two-column layout follows the header as a separate
    # table; drop the dashes row that would otherwise split it in the HTML.
    text = '\n'.join(out)
    marker = '| \u0423\u0440\u043e\u0432\u0435\u043d\u044c | 1 \u00b7 2 \u00b7 3 (\u043f. 6.2) |\n'
    tail = text.split(marker, 1)[1]
    tail = tail.replace('| --- | --- |\n', '', 1)
    return text.split(marker, 1)[0] + marker + tail


def main():
    raw = read(BASE)
    if not raw.startswith('# '):
        raise SystemExit('ERROR: base edition has no H1')

    # The base edition has NO '---' separator after its title block (exactly the
    # defect check_documents.py flags), so split on the first section heading.
    m = re.search(r'(?m)^## 1 ', raw)
    if not m:
        raise SystemExit('ERROR: base edition has no "## 1 " section')
    body = raw[m.start():]

    body = unescape(body)
    body, filled = fix_params_table(body)
    body = fix_param_refs(body)
    body = fix_header_row(body)

    text = FRONTMATTER.format(today=TODAY) + TITLE + ANNOTATION + body.strip() + '\n'

    if not os.path.isdir(DOC_DIR):
        raise SystemExit('ERROR: target directory is missing (vault not found)')
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print('OK: wrote %s' % OUT.encode('ascii', 'backslashreplace').decode())
    print('   defaulted parameters: %d' % filled)
    print('   size: %d chars, %d lines' % (len(text), text.count('\n') + 1))


if __name__ == '__main__':
    main()
