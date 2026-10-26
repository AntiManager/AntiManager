"""Lint the typical-documents suite in the Personal Vault.

Checks (vault-level, no network, read-only):
  * YAML frontmatter with the required keys per document type;
  * a ``---`` separator after the title/metadata block (md_to_partial drops
    through it, so a missing separator would emit an empty partial);
  * version / status / license are filled, not placeholders;
  * no publication placeholders in the header block ([дата], {дата},
    [организация-публикатор], [указать лицензию...]) and no draft tokens
    (TODO/TBD/FIXME/???/.../дописать/placeholder/<<</>>>) anywhere;
  * no heading-level jumps;
  * no duplicate H2 headings;
  * every [[wiki link]] resolves by file basename or frontmatter alias;
  * a public document never links the internal СНУ regulation.

Template fields inside forms ([роль], [N], [X]%, [порог], [показатель],
[дата] inside a form table) are legitimate and stay: publication
placeholders are only checked in the header block.

Usage:
  python .kilo/scripts/check_documents.py --vault "<vault path>" [--check]
Exit codes: 0 = clean, 1 = errors found, 2 = usage / vault not found.
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

DOC_DIR = 'Методология ПС/Типовые документы'
ARTICLE_REL = 'Книга/01_Статьи/56_Ритм_управления.md'
REPORT_REL = '.kilo/reports/documents-lint.md'

DOC_KEYS = ('tags', 'status', 'created', 'updated', 'version', 'owner',
            'license', 'library', 'public', 'aliases')
ARTICLE_KEYS = ('tags', 'status', 'created', 'updated', 'topic', 'library',
                'aliases')

HEADER_PLACEHOLDERS = ('[дата]', '{дата}', '[организация-публикатор]',
                       '[указать лицензию', '[указать лицензию…]')
DRAFT_TOKENS = re.compile(r'TODO|TBD|FIXME|\?\?\?|\[\.\.\.\]|дописать|'
                          r'placeholder|<<<|>>>', re.IGNORECASE)
WIKI = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
H = re.compile(r'^(#{1,6})\s+(.*)$')
INTERNAL_TARGETS = ('СНУ-регламент', 'СНУ_типология')


def parse_frontmatter(text):
    lines = text.replace('\r\n', '\n').split('\n')
    if not lines or lines[0].strip() != '---':
        return None, 1, 'no frontmatter'
    fm = {}
    i = 1
    while i < len(lines) and lines[i].strip() != '---':
        line = lines[i]
        m = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
        i += 1
    if i >= len(lines):
        return None, 1, 'frontmatter not closed'
    return fm, i + 1, None


def fm_list(raw):
    raw = raw.strip()
    if raw.startswith('[') and raw.endswith(']'):
        raw = raw[1:-1]
    return [x.strip().strip('"\'') for x in raw.split(',') if x.strip()]


class VaultIndex:
    def __init__(self, vault):
        self.names = {}
        self.aliases = {}
        for p in vault.rglob('*.md'):
            if any(part.startswith('.') for part in p.relative_to(vault).parts):
                continue
            self.names.setdefault(p.stem, []).append(p)
            try:
                text = p.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            fm, _, err = parse_frontmatter(text)
            if err or not fm.get('aliases'):
                continue
            for a in fm_list(fm['aliases']):
                self.aliases.setdefault(a, []).append(p)

    def resolve(self, target):
        target = target.strip()
        if target in self.names or target in self.aliases:
            return True
        target = target.rsplit('/', 1)[-1]
        return target in self.names or target in self.aliases


def header_block(lines, body_start):
    """Title/metadata block: from the H1 to the first standalone ---.

    md_to_partial drops everything through that separator, so the block must
    be short (a far-away horizontal rule would silently strip content).
    """
    out = []
    i = body_start
    while i < len(lines):
        if lines[i].strip() == '---':
            return out, i
        out.append(lines[i])
        i += 1
    return out, -1


def lint_file(path, index, is_article):
    errors = []
    text = path.read_text(encoding='utf-8')
    lines = text.replace('\r\n', '\n').split('\n')

    fm, body_start, fm_err = parse_frontmatter(text)
    if fm_err:
        return [(1, 'FRONTMATTER', fm_err)], {}
    required = ARTICLE_KEYS if is_article else DOC_KEYS
    for key in required:
        if key not in fm or fm[key] == '':
            errors.append((1, 'FM_KEY', 'missing key: ' + key))

    if not is_article:
        if fm.get('library') != 'documents':
            errors.append((1, 'FM_LIBRARY', 'library must be documents'))
        if fm.get('public') not in ('true', 'false'):
            errors.append((1, 'FM_PUBLIC', 'public must be true or false'))
        if fm.get('license', '').strip('[]"\'') == '':
            errors.append((1, 'FM_LICENSE', 'license is empty'))
    else:
        if fm.get('library') != 'articles':
            errors.append((1, 'FM_LIBRARY', 'library must be articles'))

    hdr, sep_idx = header_block(lines, body_start)
    if sep_idx < 0 or sep_idx == len(lines) or len(hdr) > 40:
        errors.append((1, 'SEPARATOR',
                       'no standalone --- within 40 lines after the title block'))
    for offset, line in enumerate(hdr if sep_idx >= 0 and len(hdr) <= 40 else []):
        for token in HEADER_PLACEHOLDERS:
            if token in line:
                errors.append((body_start + offset + 1, 'PUB_PLACEHOLDER',
                               token))

    body = '\n'.join(lines[body_start:])
    for num, line in enumerate(lines[body_start:], start=body_start + 1):
        m = DRAFT_TOKENS.search(line)
        if m:
            errors.append((num, 'DRAFT_TOKEN', m.group(0)))

    prev = 0
    h2 = {}
    for num, line in enumerate(lines[body_start:], start=body_start + 1):
        m = H.match(line.strip())
        if not m:
            continue
        level = len(m.group(1))
        if prev and level > prev + 1:
            errors.append((num, 'HEADING_JUMP',
                           'h%d after h%d' % (level, prev)))
        prev = level
        if level == 2:
            title = m.group(2).strip()
            h2[title] = h2.get(title, 0) + 1
    for title, count in h2.items():
        if count > 1:
            errors.append((1, 'DUP_H2', title))

    public = fm.get('public') == 'true'
    for num, line in enumerate(lines[body_start:], start=body_start + 1):
        for m in WIKI.finditer(line):
            target = m.group(1).strip()
            if not index.resolve(target):
                errors.append((num, 'BROKEN_WIKI', target))
            if public and target in INTERNAL_TARGETS:
                errors.append((num, 'INTERNAL_LEAK', target))
    return errors, fm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vault', default=None)
    ap.add_argument('--check', action='store_true',
                    help='read-only mode (default behaviour)')
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    vault_raw = args.vault or __import__('os').environ.get('VAULT_DIR')
    if not vault_raw:
        print('ERROR: vault path not provided (use --vault or VAULT_DIR)')
        return 2
    vault = Path(vault_raw)
    if not vault.is_dir():
        print('ERROR: vault not found')
        return 2

    targets = []
    doc_dir = vault / DOC_DIR
    if doc_dir.is_dir():
        targets = [(p, False) for p in sorted(doc_dir.glob('*.md'))]
    article = vault / ARTICLE_REL
    if article.exists():
        targets.append((article, True))
    if not targets:
        print('ERROR: no target notes found')
        return 2

    index = VaultIndex(vault)
    all_errors = []
    docs = []
    for path, is_article in targets:
        errors, fm = lint_file(path, index, is_article)
        rel = path.relative_to(vault).as_posix()
        docs.append({'rel': rel, 'errors': errors,
                     'status': fm.get('status', ''),
                     'version': fm.get('version', '').strip('"\'')})
        all_errors.extend((rel, num, code, msg) for num, code, msg in errors)

    report = ['# Documents lint', '',
              'Checked: %d note(s) · %s' % (len(targets),
                                           datetime.now().strftime('%Y-%m-%d %H:%M')),
              '', 'Errors: %d' % len(all_errors), '']
    for rel, num, code, msg in all_errors:
        report.append('- `%s:%d` **%s** — %s' % (rel, num, code, msg))
    if not all_errors:
        report.append('No errors.')
    report_path = Path(__file__).resolve().parents[1] / 'reports' / 'documents-lint.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(report) + '\n', encoding='utf-8')

    safe = [{'i': i + 1, 'status': d['status'], 'version': d['version'],
             'errors': len(d['errors'])} for i, d in enumerate(docs)]
    print(json.dumps({'files': safe, 'errors': len(all_errors)},
                     ensure_ascii=True))
    return 0 if not all_errors else 1


if __name__ == '__main__':
    sys.exit(main())
