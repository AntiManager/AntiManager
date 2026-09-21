# AntiManager — Harness Map

Vault map: `Roadmap/Дорожная карта доработок.md`.
Site plan: `.kilo/plans/site-development-plan.md`.
Repository plan: `.kilo/plans/antimanager-repo-restructure.md`.
Plan policy: new plans are local (`.kilo/plans/` is gitignored) and enter the repository only deliberately; tracked plans (`site-development-plan.md`, `antimanager-repo-restructure.md`, `1784652237510-site-brutalist-rebuild.md`) are history — do not touch. Do not modify `.gitignore`.

## Language policy

- Agent-facing docs (skills, agents, commands, new plans, new execution-log entries, `.memory`, this file) — English.
- Human-facing content (articles, UI strings, `manifesto-*`) — Russian.
- Agent reasoning — English; answers to the user — Russian.
- Russian literals that are real product UI strings or vault paths inside agent docs stay verbatim.
- Existing Russian plans, execution log, and `.memory` are kept as history.

## Skills (7)

- web-developer — design system, page template, performance
- content-publisher — move Obsidian articles into HTML
- book-writing — article writing and editing
- vault-indexer — full vault inventory (structure, links, health)
- site-designer — site design and UX for antimanager.pro
- diagram-architect — Mermaid diagrams
- management-research — concept research

## Commands (8)

- `/fix-encoding` — check and repair broken encoding in vault `.md` files
- `/link-ideas` — link ideas across notes
- `/new-article` — create a new article
- `/new-chapter` — create a chapter draft
- `/new-tool` — create a tool note
- `/vault-audit` — audit vault structure
- `/vault-index` — full vault inventory
- `/check-site` — build the site and run the Playwright suite

## Agents (2)

- book-editor — book/article writing and editing (encoding, frontmatter, backlinks)
- vault-auditor — vault structure audit

## MCP (always enabled, 3)

- obsidian — batch note processing, vault read/write
- web-search — reference search
- github — commits/pushes, deploy

---

## New machine setup

1. Install Node.js, Python, Obsidian + remotely-save
2. Clone the repo: `git clone https://github.com/AntiManager/AntiManager`
3. Copy `.kilo/kilo.json.example` → `.kilo/kilo.json` and fill in the paths
4. Sync the vault (remotely-save pulls content only)
5. Done — the vault is clean, the config lives in the repo

---

## Security protocol (absolute priority)

1. **Back up before editing.** Any write operation starts with a backup to `$env:TEMP\kilo\backups\<date>\`.
2. **PowerShell for ASCII and simple operations only.** Handle Cyrillic through Python (ftfy).
3. **Guard Encoding: mandatory before and after.** Before any `edit`/`write` to vault files, run `python .kilo/scripts/guard_encoding.py --backup <file>`. After the operation, run `python .kilo/scripts/guard_encoding.py <file>`. If CORRUPT — restore from the backup and alert the user.
4. **Verify.** Check the result after every change. If the algorithm did not produce the expected result — roll back.
5. **No bulk runs.** One file → verify → commit. No mass applies.
6. **Cyrillic through Write/Edit.** If a file contains Cyrillic, modify content with Python only (`ftfy.fix_text`). Never pass Cyrillic through PowerShell.
