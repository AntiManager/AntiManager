# AntiManager — Harness Map

Vault map: `Roadmap/Дорожная карта доработок.md`.
Site plan: `.kilo/plans/site-development-plan.md`.
Repository plan: `.kilo/plans/antimanager-repo-restructure.md`.
Plan policy: new plans are local (`.kilo/plans/` is gitignored) and enter the repository only deliberately; tracked plans (`site-development-plan.md`, `antimanager-repo-restructure.md`, `1784652237510-site-brutalist-rebuild.md`) are history — do not touch. Completed local plans move to `.kilo/plans/archive/`; only the active plan stays at the root. Do not modify `.gitignore`.

## Language policy

- Agent-facing docs (skills, agents, commands, new plans, new execution-log entries, this file) — English. `.memory/` is English for `active_context.md`/`progress.md`; `project_brief.md`/`tech_context.md`/`system_patterns.md` still carry Russian domain wording (grandfathered — translate on the next substantial edit).
- Human-facing content (articles, UI strings, `manifesto-*`) — Russian.
- Agent reasoning — English; answers to the user — Russian.
- Russian literals that are real product UI strings or vault paths inside agent docs stay verbatim.
- Existing Russian plans, execution log, and `.memory` are kept as history.

## Skills (8)

- web-developer — design system, page template, performance
- content-publisher — move Obsidian articles into HTML
- book-writing — article writing and editing
- article-readiness — publish-readiness screen + editorial checklist
- vault-indexer — full vault inventory (structure, links, health)
- site-designer — site design and UX for antimanager.pro
- diagram-architect — Mermaid diagrams
- management-research — concept research

## Commands (10)

- `/fix-encoding` — check and repair broken encoding in vault `.md` files
- `/link-ideas` — link ideas across notes
- `/new-article` — create a new article
- `/new-chapter` — create a chapter draft
- `/new-tool` — create a tool note
- `/vault-audit` — audit vault structure
- `/vault-index` — full vault inventory
- `/check-site` — build the site and run the full test suite (unit + Playwright)
- `/article-readiness` — score vault articles for publish-readiness
- `/full-article` — migrate one article's full text to its `/full/` page (TOC, materials, PDF) and deploy

## Agents (2)

- book-editor — book/article writing and editing (encoding, frontmatter, backlinks)
- vault-auditor — vault structure audit

## Scripts (6)

- `genome_doc_build.py` — regenerate `/genome/role/` documents from the vault
- `gen_article_partials.py` — regenerate `/articles/` long-read partials from the vault
- `gen_ps_audit_page.py` — regenerate the `/genome/audit/` page regions and the fillable `express-audit-ps.xlsx` from the vault; `--check` exits 1 on drift
- `gen_systems_page.py` — regenerate the `/genome/systems/` regions, the owner document (`Заказчики/КАБЭКС/Карта-систем-собственнику.md/.docx`) and the blank card template from `Методология ПС/Карточки-систем.md`; `--check` exits 1 on drift
- `check_ps_audit.py` — `Аудит ПС/` linter: base structure, express-row identity with the base, banned tokens and system-card references
- `check_system_cards.py` — `Методология ПС/Карточки-систем.md` linter: 14 cards, 12-field count, base-id criterion refs, process-code resolution, artifact ids, project-interface lines, orphan marking, no project-type appendices, S14 model reference

## MCP (2 project + 1 global)

- obsidian — batch note processing, vault read/write (project `.kilo/kilo.json`)
- github — commits/pushes, deploy (project `.kilo/kilo.json`)
- context7 — library/framework reference docs (global `kilo.jsonc`)

---

## New machine setup

1. Install Node.js, Python, Obsidian + remotely-save
2. Clone the repo: `git clone https://github.com/AntiManager/AntiManager`
3. Copy `.kilo/kilo.json.example` → `.kilo/kilo.json` and fill in the paths
4. Sync the vault (remotely-save pulls content only)
5. Done — the vault is clean, the config template lives in the repo

---

## Security protocol (absolute priority)

1. **Back up before editing.** Any write operation starts with a backup under `$env:TEMP\kilo\backups\` (the encoding guard uses a flat `<timestamp>_<file>` naming).
2. **PowerShell for ASCII and simple operations only.** Handle Cyrillic through Python (ftfy).
3. **Guard Encoding: mandatory before and after.** Before any `edit`/`write` to vault files, run `python pipelines/common/guard_encoding.py --backup <file>`. After the operation, run `python pipelines/common/guard_encoding.py <file>`. If CORRUPT — restore from the backup and alert the user.
4. **Verify.** Check the result after every change. If the algorithm did not produce the expected result — roll back.
5. **No bulk runs.** One file → verify → commit. No mass applies.
6. **Cyrillic through Write/Edit.** If a file contains Cyrillic, modify content with Python only (`ftfy.fix_text`). Never pass Cyrillic through PowerShell.
7. **Do not use the Obsidian MCP for writes/moves on Cyrillic paths.** On this host `create_note` / `move_note` / `edit_note` roll back deterministically: the transaction journal stores the path as UTF-8→cp1251 mojibake (`РђСѓРґРёС‚ РџРЎ/...`). Use `Write`/`Edit` for content and a file-based Python script (ASCII source, `chr()`-built paths) for delete/move, with a backup under `%TEMP%\kilo\backups`. MCP stays reliable for reads.
