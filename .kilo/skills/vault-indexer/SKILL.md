---
name: vault-indexer
description: Full vault inventory (structure, links, health)
---

# vault-indexer

Full inventory of the Obsidian vault: structure, links, health.

## Commands

### `/vault-index [full|quick|health]`

**full** — full vault audit:
1. Scan all `.md` files (excluding `.obsidian/`, `.kilo/`, `node_modules/`, `.trash/`, `Attachment/`)
2. For each file check:
   - Frontmatter: `tags`, `status`, `created`, `updated`
   - Presence of `#`-tags inside the text (if there is no frontmatter)
   - Encoding (UTF-8 BOM, mojibake)
3. Extract all `[[wiki links]]` and build a graph:
   - Which notes link to what
   - Which notes have incoming links
   - List of orphan notes (0 incoming + 0 outgoing)
   - List of broken links (target does not exist)
   - mojibake in links (text like `Р¦РёРєР»` instead of Russian)
4. Check for duplicates (SHA256 of content)
5. Report:

```
=== VAULT INDEX ===
Всего файлов: N
С frontmatter: N (X%)
С тегами: N (X%)
Orphan-заметки: N
Битые ссылки: N (из них mojibake: M)
Дубликаты: N пар
Проблемы кодировки: N
```

**quick** — statistics only (no graph):
```
Файлы: N | Frontmatter: N | Теги: N | Orphans: N
```

**health** — problems only:
```
❌ N файлов без frontmatter
❌ N битых ссылок
❌ N mojibake
❌ N дубликатов
```

## Report format

After each audit create/update:
```
Roadmap/VAULT_INDEX.md
```
With the structure:
- Audit date
- Statistics
- List of critical issues
- List of important issues
- Recommendations (by priority)

## Integration with other skills

- `book-writing` — after index, check article frontmatter
- `management-research` — after index, add links between concepts
- `fix-encoding` — before index, check encoding

## Automation in AGENTS.md

On every session start related to the vault, run `/vault-index quick` for context.
