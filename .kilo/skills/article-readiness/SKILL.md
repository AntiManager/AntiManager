---
name: article-readiness
description: Assess whether a book article is ready to publish — objective 12-point screen (script) plus a two-layer rubric. Use when deciding on review→published transitions, auditing the vault, or refining weak articles.
---

# Skill: article-readiness

Two-layer readiness assessment for the book articles in `Книга/01_Статьи`
(`ARTICLES_DIR` in `.env`). Layer 1 is deterministic; Layer 2 is editorial.

## When to use

- Before any `review → published` frontmatter transition.
- When auditing the whole vault, or after a bulk edit.
- When an article feels weak and you need concrete gaps, not a vague opinion.

## Layer 1 — deterministic screen

```bash
python .kilo/scripts/article_readiness.py            # full vault → .kilo/reports/article-readiness.md
python .kilo/scripts/article_readiness.py --out <path>
python .kilo/scripts/article_readiness.py --json .kilo/reports/article-readiness.json
```

Read the report with the Read tool (do not rely on console output — Cyrillic in
PowerShell stdout is cp1251 and shows as mojibake). Never pass Russian text
through the shell.

Objective checks (12):

| Check | Passes when |
|---|---|
| frontmatter | `tags`, `status`, `created`, `updated` all present |
| title | at least one heading exists |
| length | ≥ `--min-words` (default 800) |
| related-tools | a «Связанные инструменты» heading exists |
| related-chapters | a «Связанные главы» heading exists |
| conclusion | a conclusion/epilogue-style heading exists (Итог/Вывод/Заключение/Эпилог/…) |
| action | an actionable heading exists (чек-лист/протокол/шаг/шаблон/тест/…) |
| case | a case/example heading exists (кейс/пример/истори/практик/…) |
| crosslinks | ≥ 2 `[[wiki links]]` |
| no placeholders | no TODO/TBD/???/«дописать»/placeholder markers |
| no heading jumps | no level skip (e.g. `#` → `###`) |
| encoding | no BOM, no `U+FFFD` replacement chars |

Verdict: `READY` ≥ 11/12 · `NEEDS-EDIT` 8–10/12 · `DRAFT` ≤ 7/12.
Flags in the report also surface monolithic blocks (> `--max-block`, default
2000 words with no subheading).

Limitations: the screen counts headings only, so a genuine case described in
body text without its own heading is a false gap; and genre-specific documents
(questionnaires, appendices, manifestos) score low by design. Always finish with
Layer 2.

## Layer 2 — editorial checklist

For each article that is not `READY`, or when the user asks for a quality pass:

1. **Thesis** — is the promise stated in the first 1–2 paragraphs, and answered
   by the end? (intro thesis, not just a title).
2. **Case** — is there a concrete production example with numbers/roles, not
   only theory? (the `case` gap in the report).
3. **Action** — does the reader get a checklist/template/protocol they can run
   on Monday?
4. **Style** — does the article follow concept → mechanism → practice?
5. **Cross-links** — do `[[…]]` links point to real notes (chapter/tool aliases),
   and are the «Связанные инструменты/главы» lists populated and correct?
6. **Structure** — heading hierarchy consistent (title, parts, chapters), no
   monolithic 2000+ word blocks, no empty «Часть X» headers.
7. **Vault hygiene** — `book/draft` tag and `status` match reality; `updated`
   reflects the last real edit; aliases present for wiki links.

## Output

Per article: `num`, verdict (`READY` / `NEEDS-EDIT` / `DRAFT`), the Layer 1 failed
checks, and a short list of concrete fixes from Layer 2. Do not report a score
without the fixes.

## Integration

- `book-writing` — run this before the `review → published` transition and on
  `book/draft` removal.
- `book-editor` agent — use the Layer 2 checklist as the editing procedure.
- Reports are generated local artifacts under `.kilo/reports/` (not committed).
