---
name: book-writing
description: Writing and editing the book — structure, tags, encoding, links between notes
---

## Rules

### Frontmatter
- Required fields: `tags`, `status` (draft/review/published), `created`, `updated`
- On transition `draft→review→published`:
  - Remove `#book/draft` (if present)
  - On published: add `aliases` (key names for [[wiki links]])
  - Update `updated` to the current date
- Tags: `#book #book/chapter #book/draft #tool #case #system-dynamics #production #lean #digital`

### Encoding
- All .md files must be in **UTF-8 without BOM**
- Guard Encoding — mandatory before and after any edit:

1. Before editing: `python .kilo/scripts/guard_encoding.py --backup <file>`
2. After editing: `python .kilo/scripts/guard_encoding.py <file>`
3. On `CORRUPT` — roll back from the backup; fix only via `python .kilo/scripts/guard_encoding.py --fix <file>` (ftfy)

- Batch check: `/fix-encoding`

### Linking
- When mentioning a tool → `[[Название инструмента]]`
- When mentioning a chapter → `[[NN_Название_главы]]` or `[[Название]]` (if aliases exist)
- Terminology: verify against `Книга/03 - Инструменты/` (all files)

### After publication
1. Update the book's `README.md` (status in the table)
2. Update `Roadmap/Дорожная карта доработок.md`
3. Add backlinks: grep related topics, add `[[NN_Название]]` to the "Связанные главы" section
4. Create/update backlinks in related articles (if they have encoding issues — fix those first)
