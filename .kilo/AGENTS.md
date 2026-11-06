# AntiManager — Harness Map

Vault map: `Roadmap/Дорожная карта доработок.md`.
Typical documents: `Методология ПС/Типовые документы/` (public templates + internal СНУ regulation) → site `/method/documents/`.
Site plan: `.kilo/plans/site-development-plan.md`.
Repository plan: `.kilo/plans/antimanager-repo-restructure.md`.
Active local plan: none — `1793969494727` (site IA refactor) closed and archived 2026-11-06; new plans go to `.kilo/plans/`.
Plan policy: new plans are local (`.kilo/plans/` is gitignored) and enter the repository only deliberately; tracked plans (`site-development-plan.md`, `antimanager-repo-restructure.md`, `1784652237510-site-brutalist-rebuild.md`) are history — do not touch. Completed local plans move to `.kilo/plans/archive/`; only the active plan stays at the root. Do not modify `.gitignore`.
- Deploy provenance: deploy only from a committed tree; record live `VERSION` ↔ SHA in `.memory` (details: `.kilo/harness.md`).

## Site IA (since 2026-11-06)

- Canonical routes live in `site/src/routes.js`: `/playbook/` (chapters + `/full/`), `/start/`,
  `/articles/`, `/method/` (`/audit/`, `/systems/`, `/documents/`, `/role/`), `/about/`
  (`/manifesto/`, `/origins/`), `/contact/`, `/privacy/`, `/search/`, `/404/`.
- Legacy URLs (`/weapons/`, `/genome/`, `/arsenal/`, `/book/`, `/scenarios/`, `/manifesto/`,
  `/archive/`, `/about/headquarters/`, `/headquarters/`, `/cases/`) 301 to the new routes; the map
  is generated into `site/deploy/redirects.conf` by `npm run gen:redirects` (from `site/`). Run
  `npm run check:redirects` after touching routes. `/cases/` is retired (data preserved).
- Site checks: `build.js`, `unit/build-routes.test.js`, `unit/build-cases-retired.test.js`,
  `tests/nav-mobile.spec.js`. Playwright uses port 3100 (`PLAYWRIGHT_PORT`), never 3000.

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

## Agents (0)

No dedicated agents. Book/article writing and editing (encoding, frontmatter, backlinks) is the
`book-writing` skill — the former `book-editor` agent (retired 2026-10-28) added only two things
beyond it (grep-for-duplicates before writing, concept→mechanism→case style), both now merged
into `book-writing`. Vault structure audit is `/vault-audit` (health mode of the `vault-indexer`
skill) — no dedicated agent; the former `vault-auditor` agent added nothing beyond that command.

## Scripts (8)

- `genome_doc_build.py` — regenerate `/method/role/` documents from the vault
- `gen_article_partials.py` — regenerate `/articles/` long-read partials from the vault
- `gen_documents_pages.py` — regenerate `/method/documents/` body partials, the hub card region and `materials/<slug>.docx` from the vault; `--check` exits 1 on drift (missing vault → 2)
- `check_documents.py` — `Методология ПС/Типовые документы/` + article 56 linter: frontmatter, separator, publication placeholders (header block only), heading jumps, duplicate H2, wiki resolution by basename/alias, public→internal leak guard; writes `.kilo/reports/documents-lint.md`
- `gen_ps_audit_page.py` — regenerate the `/method/audit/` page regions and the fillable `express-audit-ps.xlsx` from the vault; `--check` exits 1 on drift
- `gen_systems_page.py` — regenerate the `/method/systems/` regions, the owner document (`Заказчики/КАБЭКС/Карта-систем-собственнику.md/.docx`) and the blank card template from `Методология ПС/Карточки-систем.md`; `--check` exits 1 on drift
- `check_ps_audit.py` — `Аудит ПС/` linter: base structure, express-row identity with the base, banned tokens and system-card references
- `check_system_cards.py` — `Методология ПС/Карточки-систем.md` linter: 14 cards, 12-field count, base-id criterion refs, process-code resolution, artifact ids, project-interface lines, orphan marking, no project-type appendices, S14 model reference

## Publication rules (learned 2026-10-26)

- **Publication placeholders vs template fields.** `[дата]`, `{дата}`, `[организация-публикатор]`, `[указать лицензию…]` are banned in the title/metadata block only. Fill-in fields inside forms (`[роль]`, `[N]`, `[X]%`, `[порог]`, `[дата]` in a table row) are legitimate and must not be "filled" with invented values.
- **`md_to_partial.convert()` leaves Markdown links literal** (it only rewrites `[[wiki]]`). Any generator that publishes vault text must promote `[text](url)` to `<a>`; see `gen_documents_pages.py` and `gen_article_partials.py`.
- **Binary artifact churn.** `npm run render:pdf` rewrites every tracked PDF (metadata differs each run). Render only after content changes, and before commit restore untouched tracked artifacts with `git checkout -- site/materials`, keeping only the new ones.
- **`documents.json` is public metadata; the vault path map lives in the generator** (`SOURCES`), and the generator refuses a source whose frontmatter is not `public: true` — the internal СНУ regulation is never a source.

## MCP (1 project + 1 global)

- obsidian — batch note processing, vault **reads** (project `.kilo/kilo.json`); writes/moves on Cyrillic paths are broken — see §7
- context7 — library/framework reference docs (global `kilo.jsonc`; disabled until the token is rotated)
- github — not an MCP on this machine; use `gh`/git with `GH_TOKEN`

---

## New machine setup

1. Install Node.js (26+), Python 3.14, git + git-lfs, Pandoc 3.13 (DOCX generation), Obsidian + remotely-save.
2. Clone: `git clone https://github.com/AntiManager/AntiManager`.
3. `python -m pip install ftfy python-docx openpyxl pytest`; `cd site; npm ci; npx playwright install chromium`.
4. Copy `.env.example` → `.env` and fill `REMOTE_*` (VPS), `VAULT_DIR`/`ARTICLES_DIR` (local vault), `TELEGRAM_*`; copy `.kilo/kilo.json.example` → `.kilo/kilo.json` and fill the paths.
5. Restore the SSH deploy key to `~/.ssh/id_ed25519` (VPS: `chemule@5.129.221.85:2222`), mode user-only.
6. Sync the vault (remotely-save pulls content only); it stays outside the repo.
7. Verify: `cd site; npm run build; npm run test:unit; npx playwright test; npm run check:redirects`; `python .kilo/scripts/check_documents.py --vault "<vault>"`; each generator with `--check`; `.\site\scripts\verify-deploy.ps1`.
8. Generators default to `C:\Work\Personal Vault`; pass `--vault <path>` on another host. `check_system_cards.py` takes the vault as a positional argument.

---

## Security protocol (absolute priority)

1. **Back up before editing.** Any write operation starts with a backup under `$env:TEMP\kilo\backups\` (the encoding guard uses a flat `<timestamp>_<file>` naming).
2. **PowerShell for ASCII and simple operations only.** Handle Cyrillic through Python (ftfy).
3. **Guard Encoding: mandatory before and after.** Before any `edit`/`write` to vault files, run `python pipelines/common/guard_encoding.py --backup <file>`. After the operation, run `python pipelines/common/guard_encoding.py <file>`. If CORRUPT — restore from the backup and alert the user.
4. **Verify.** Check the result after every change. If the algorithm did not produce the expected result — roll back.
5. **No bulk runs.** One file → verify → commit. No mass applies.
6. **Cyrillic through Write/Edit.** If a file contains Cyrillic, modify content with Python only (`ftfy.fix_text`). Never pass Cyrillic through PowerShell.
7. **Do not use the Obsidian MCP for writes/moves on Cyrillic paths.** On this host `create_note` / `move_note` / `edit_note` roll back deterministically: the transaction journal stores the path as UTF-8→cp1251 mojibake (`РђСѓРґРёС‚ РџРЎ/...`). Use `Write`/`Edit` for content and a file-based Python script (ASCII source, `chr()`-built paths) for delete/move, with a backup under `%TEMP%\kilo\backups`. MCP stays reliable for reads.
