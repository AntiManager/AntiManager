# -*- coding: utf-8 -*-
"""Render the A3 regulation Markdown into the editable DOCX for /genome/documents/.

Mirrors what gen_documents_pages.run_pandoc() does for the other documents, but
with python-docx because pandoc is not installed on this machine. The output
path is the one build.js existence-gates: site/materials/<slug>.docx.

Usage:
  <bundled python> .run/a3_docx.py <source.md> <out.docx> <title> <version>
"""
import io
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Inches


def split_frontmatter(text):
    lines = text.replace('\r\n', '\n').split('\n')
    if lines[0].strip() != '---':
        return '', text
    i = 1
    while i < len(lines) and lines[i].strip() != '---':
        i += 1
    return '\n'.join(lines[1:i]), '\n'.join(lines[i + 1:])


def inline_runs(paragraph, text):
    """Add **bold** / *italic* segments to a paragraph."""
    for part in re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*)', text):
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith('*') and part.endswith('*') and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        else:
            paragraph.add_run(part)


def main():
    src, out, title, version = sys.argv[1:5]
    text = io.open(src, encoding='utf-8').read()
    _, body = split_frontmatter(text)

    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(10)

    doc.add_heading(title, level=0)
    meta = doc.add_paragraph('Версия %s · CC BY-SA 4.0 · AntiManager' % version)
    meta.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    lines = body.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()

        if not s or s == '---':
            i += 1
            continue

        m = re.match(r'^(#{1,6})\s+(.*)$', s)
        if m:
            level = len(m.group(1))
            heading = m.group(2)
            # The document H1 is the authored title; skip a duplicate.
            if level == 1 and heading.strip() == title.strip():
                i += 1
                continue
            doc.add_heading(heading, level=min(level, 4))
            i += 1
            continue

        if s.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i].strip())
                i += 1
            cells = [[c.strip() for c in r.strip('|').split('|')] for r in rows]
            cells = [r for r in cells if not all(re.fullmatch(r':?-{2,}:?', c) for c in r)]
            if not cells:
                continue
            width = max(len(r) for r in cells)
            table = doc.add_table(rows=0, cols=width)
            table.style = 'Table Grid'
            for idx, row in enumerate(cells):
                trimmed = [re.sub(r'\*\*(.+?)\*\*', r'\1', c) for c in row]
                trimmed += [''] * (width - len(trimmed))
                tbl_row = table.add_row()
                for col, value in enumerate(trimmed):
                    cell = tbl_row.cells[col]
                    cell.text = ''
                    para = cell.paragraphs[0]
                    inline_runs(para, value)
                    if idx == 0:
                        for run in para.runs:
                            run.bold = True
            doc.add_paragraph('')
            continue

        if s.startswith('>'):
            quote = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote.append(lines[i].strip().lstrip('>').strip())
                i += 1
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Inches(0.3)
            inline_runs(para, ' '.join(q for q in quote if q))
            for run in para.runs:
                run.italic = True
            continue

        m = re.match(r'^[-*]\s+(.*)$', s)
        if m:
            items = []
            while i < len(lines) and re.match(r'^[-*]\s+', lines[i].strip()):
                items.append(re.match(r'^[-*]\s+(.*)$', lines[i].strip()).group(1))
                i += 1
            for item in items:
                para = doc.add_paragraph(style='List Bullet')
                inline_runs(para, item)
            continue

        m = re.match(r'^(\d+)\.\s+(.*)$', s)
        if m:
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i].strip()):
                items.append(re.match(r'^\d+\.\s+(.*)$', lines[i].strip()).group(1))
                i += 1
            for item in items:
                para = doc.add_paragraph(style='List Number')
                inline_runs(para, item)
            continue

        para = doc.add_paragraph()
        inline_runs(para, s)
        i += 1

    doc.save(out)
    print('OK docx: %s' % out)


if __name__ == '__main__':
    main()
