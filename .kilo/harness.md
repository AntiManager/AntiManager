# Harness provenance — AntiManager

> Written by `/harness-init` 2026-11-05; updated 2026-11-06 (deploy provenance, budgets) and
> 2026-11-15 (HP-003/004/005/010/013 closed; AGENTS.md trimmed to the 60-line budget, detail
> moved here). Not autoloaded — read on demand.

Counts: skills 8 / agents 0 / commands 11.

## Composition

- Archetype: `content-site` (Obsidian vault → static site → VPS)
- Patterns: `HP-001, HP-002, HP-003, HP-004, HP-005, HP-007, HP-008, HP-009, HP-010, HP-011, HP-012, HP-013, HP-015, HP-016`
- Decisions followed: `ADR 0001, ADR 0003, ADR 0005`
- Initialized: `2026-11-05`

## Layout

- Tracked config: root `kilo.json` (model, 4-file autoload, permissions).
- Local config: `.kilo/kilo.json` (gitignored) adds the `obsidian` MCP, `external_directory` for
  the vault and indexing; deep-merged over the root file. **It must not set `permission.bash` or
  any other permission** — a local overlay wins over the root and would bypass HP-003. The
  template `.kilo/kilo.json.example` follows that rule.
- Instructions: `.kilo/AGENTS.md` (not root) — ≤60 lines, boot-only facts; detail is this file.
- Plans: `.kilo/plans/` is gitignored and local; tracked plans are history — do not touch:
  `site-development-plan.md`, `antimanager-repo-restructure.md`, `1784652237510-site-brutalist-rebuild.md`.
  Completed local plans → `.kilo/plans/archive/`; only the active plan stays at the root.
- Skills: 8 under `.kilo/skills/`; commands: 11 under `.kilo/command/`; agents: 0.

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

- Agent-facing docs (skills, agents, commands, new plans, new execution-log entries, this file,
  `AGENTS.md`) — English. `.memory/active_context.md` and `progress.md` — English;
  `project_brief.md`/`tech_context.md`/`system_patterns.md` still carry Russian domain wording
  (grandfathered — translate on the next substantial edit).
- Human-facing content (articles, UI strings, `manifesto-*`) — Russian.
- Agent reasoning — English; answers to the user — Russian.
- Russian literals that are real product UI strings or vault paths inside agent docs stay
  verbatim. Existing Russian plans, execution log and `.memory` remain as history.

## Skills (8)

- web-developer — design system, page template, performance
- content-publisher — move Obsidian articles into HTML
- book-writing — article writing and editing
- article-readiness — publish-readiness screen + editorial checklist
- vault-indexer — full vault inventory (structure, links, health)
- site-designer — site design and UX for antimanager.pro
- diagram-architect — Mermaid diagrams
- management-research — concept research

## Commands (11)

- `/closeout` — matching gate, artifact check, one memory write per file
- `/fix-encoding` — check and repair broken encoding in vault `.md` files
- `/link-ideas` — link ideas across notes
- `/new-article`, `/new-chapter`, `/new-tool` — create an article, chapter draft, tool note
- `/vault-audit`, `/vault-index` — audit vault structure, full vault inventory
- `/check-site` — build the site and run the full test suite (unit + Playwright)
- `/article-readiness` — score vault articles for publish-readiness
- `/full-article` — migrate one article's full text to its `/full/` page (TOC, materials, PDF) and deploy

## Agents (0)

No dedicated agents. Book/article editing is the `book-writing` skill (the retired `book-editor`
added only duplicate-grep before writing and the concept→mechanism→case style, both merged).
Vault structure audit is `/vault-audit` (health mode of `vault-indexer`).

## Scripts (8)

- `genome_doc_build.py` — regenerate `/method/role/` documents from the vault
- `gen_article_partials.py` — regenerate `/articles/` long-read partials from the vault
- `gen_documents_pages.py` — regenerate `/method/documents/` body partials, the hub card region
  and `materials/<slug>.docx`; `--check` exits 1 on drift (missing vault → 2)
- `check_documents.py` — `Методология ПС/Типовые документы/` + article 56 linter: frontmatter,
  separator, publication placeholders (header block only), heading jumps, duplicate H2, wiki
  resolution by basename/alias, public→internal leak guard; writes `.kilo/reports/documents-lint.md`
- `gen_ps_audit_page.py` — regenerate `/method/audit/` regions and the fillable
  `express-audit-ps.xlsx`; `--check` exits 1 on drift
- `gen_systems_page.py` — regenerate `/method/systems/` regions, the owner document
  (`Заказчики/КАБЭКС/Карта-систем-собственнику.md/.docx`) and the blank card template from
  `Методология ПС/Карточки-систем.md`; `--check` exits 1 on drift
- `check_ps_audit.py` — `Аудит ПС/` linter: base structure, express-row identity with the base,
  banned tokens and system-card references
- `check_system_cards.py` — `Методология ПС/Карточки-систем.md` linter: 14 cards, 12-field count,
  base-id criterion refs, process-code resolution, artifact ids, project-interface lines, orphan
  marking, no project-type appendices, S14 model reference

## Publication rules (learned 2026-10-26)

- **Publication placeholders vs template fields.** `[дата]`, `{дата}`, `[организация-публикатор]`,
  `[указать лицензию…]` are banned in the title/metadata block only. Fill-in fields inside forms
  (`[роль]`, `[N]`, `[X]%`, `[порог]`, `[дата]` in a table row) are legitimate and must not be
  "filled" with invented values.
- **`md_to_partial.convert()` leaves Markdown links literal** (it only rewrites `[[wiki]]`). Any
  generator that publishes vault text must promote `[text](url)` to `<a>`; see
  `gen_documents_pages.py` and `gen_article_partials.py`.
- **Binary artifact churn.** `npm run render:pdf` rewrites every tracked PDF (metadata differs each
  run). Render only after content changes, and before commit restore untouched tracked artifacts
  with `git checkout -- site/materials`, keeping only the new ones.
- **`documents.json` is public metadata; the vault path map lives in the generator** (`SOURCES`),
  and the generator refuses a source whose frontmatter is not `public: true` — the internal СНУ
  regulation is never a source.

## MCP (1 project + 1 global)

- obsidian — batch note processing, vault **reads** (project `.kilo/kilo.json`); writes/moves on
  Cyrillic paths are broken — see §Security protocol 7.
- context7 — library/framework reference docs (global `kilo.jsonc`; disabled until the token is
  rotated).
- github — not an MCP on this machine; use `gh`/git with `GH_TOKEN`.

## Safety (HP-003)

- `permission.bash` allows routine work and **asks** on `Remove-Item`, `git reset --hard`,
  `git clean`, `git push --force*`/`-f*`, `docker compose down -v`.
- `git checkout -- <path>` stays allowed: the publication rule restores untouched PDFs with it.
- `read` and `edit` deny `.env*`, `_private/**` and `.git/**`; `edit` asks outside
  `site/**`, `*.md`, `.kilo/**`, `.memory/**`.

## Closeout and memory (HP-004, HP-005)

- `/closeout` is the executable closeout: matching gate → artifact check → one full-file `Write`
  per memory file → stop. It never commits (do not commit unless the user asked).
- Budgets: `.memory/active_context.md` ≤3 KB, `.memory/progress.md` ≤8 KB. Older details move to
  `.memory/archive/`; the header carries the archive pointer.
- Do not edit `AGENTS.md`/`kilo.json`/`.memory` mid-task: they are autoloaded and invalidate the
  prefix cache; batch writes at closeout.

## SPEC before plan (HP-013)

- Ambiguous, multi-session work writes `.kilo/plans/<id>-spec.md` first (problem, numbered
  requirements, non-goals, edge cases, acceptance command); the plan links it. One-file fixes skip it.

## Security protocol (absolute priority)

1. **Back up before editing.** Any write operation starts with a backup under
   `$env:TEMP\kilo\backups\` (the encoding guard uses a flat `<timestamp>_<file>` naming).
2. **PowerShell for ASCII and simple operations only.** Handle Cyrillic through Python (ftfy).
3. **Guard Encoding: mandatory before and after.** Before any `edit`/`write` to vault files, run
   `python pipelines/common/guard_encoding.py --backup <file>`. After the operation, run
   `python pipelines/common/guard_encoding.py <file>`. If CORRUPT — restore from the backup and
   alert the user.
4. **Verify.** Check the result after every change. If the algorithm did not produce the expected
   result — roll back.
5. **No bulk runs.** One file → verify → commit. No mass applies.
6. **Cyrillic through Write/Edit.** If a file contains Cyrillic, modify content with Python only
   (`ftfy.fix_text`). Never pass Cyrillic through PowerShell.
7. **Do not use the Obsidian MCP for writes/moves on Cyrillic paths.** On this host `create_note` /
   `move_note` / `edit_note` roll back deterministically: the transaction journal stores the path as
   UTF-8→cp1251 mojibake (`РђСѓРґРёС‚ РџРЎ/...`). Use `Write`/`Edit` for content and a file-based
   Python script (ASCII source, `chr()`-built paths) for delete/move, with a backup under
   `%TEMP%\kilo\backups`. MCP stays reliable for reads.

## Artifacts

- `.run/` is local scratch and is **gitignored** (`.run/*`), except the tracked A3
  regeneration scripts (`!.run/a3_*.py|js`). Screenshots (`shots/`, `review/`), smoke output and
  session scripts never reach git; delete them freely.
- `.kilo/reports/` is local-only (`*` ignored by its own `.gitignore`); generator output and
  deploy reports are never committed.
- `site/prototype/team-landing.html` — tracked draft landing for `team.antimanager.pro`
  (`dc90922`, `noindex`); not part of `build.js`, tests or the sitemap.

## Verify

- Command: `pwsh -NoProfile -File "$env:USERPROFILE\.config\kilo\scripts\verify_repo.ps1" -Repo "C:\Work\Python\AntiManager"`
- Success: `STATUS: OK`, exit 0
- Scope: git state, remotes, harness files, encoding (names only for `.env`)
- Harness kit check (Windows matches `.kilo/harness.md` as `HARNESS.md`):
  `python "$env:USERPROFILE\.config\kilo\scripts\check_harness.py" "C:\Work\Python\AntiManager\.kilo"`
  → `problems: 0`
- Workspace drift scan: `python -X utf8 C:\Work\Python\harness-playbook\scripts\harness_lint.py --repo AntiManager`
  → `total findings: 0` (it does not see `.kilo/AGENTS.md`; that is why HP-001 is checked by the kit check)
- Not covered: site tests, vault generators, live deploy — run the full gate below
- Full gate (2026-11-06 S11 baseline):
  - `cd site; python -m unittest discover -s feedback/tests -v` → feedback service tests pass
  - `cd site; npm run build; npm run test:unit` → unit 45 pass
  - `cd site; npx playwright test` → 427 passed / 8 skipped (3 projects)
  - `test:unit` shells out to `build.js`, so it overwrites `dist/` **without** the
    Pagefind index; run `npm run build` before any E2E run that touches search
    (`analytics.spec.js` `search_query` fails otherwise — not a branch defect)
  - `cd site; npm run check:links` → 86 pages, 0 duplicate ids / heading skips / broken links / anchors
  - `cd site; npm run check:redirects` → `redirects.conf: no drift`
  - `python .kilo/scripts/check_documents.py --vault "<vault>"` → 0 findings
  - `python .kilo/scripts/gen_documents_pages.py --check`, `gen_ps_audit_page.py --check`,
    `gen_systems_page.py --check` → exit 0 (missing vault → exit 2)
  - `git status --porcelain` → empty (or the deploy commit is tagged) before deploying
  - `.\site\deploy.ps1`, then `.\site\scripts\verify-deploy.ps1` → live checks pass (301 matrix)
  - record live `VERSION` ↔ commit SHA in `.memory` after the deploy

## Session budget

- Batch ≥2.5 independent tool calls per turn; stop at ~150–180k context.
- Implementation phase ≤120 turns; an audit ≤80 turns, one domain + file allowlist.
- `session_audit.py` counts deploy/live checks as validations (2026-11-06).

## Deploy provenance

- Deploy only from a committed tree; commit and tag (or record the SHA) first.
- A live version without a commit SHA is not acceptance: write `VERSION` ↔ SHA to
  `.memory/active_context.md` and `.memory/progress.md`.
- Run `npm test` first; validate nginx config on a throwaway `nginx:alpine` (`nginx -t`); SSH
  port 2222 is flaky; a Caddy reload may refuse `localhost:2019` (non-fatal).

## Front-end gotchas

- Long H1 words are capped, not split: `.content-page h1`, `.hero-gen h1`, `.documents-hub h1`,
  `.privacy-page h1`. On `/method/`, `#offer` sits before `#problem`.
- `/search/` is `noindex` and absent from the sitemap; a future CSP `script-src` needs `'self'` +
  `'wasm-unsafe-eval'` (Pagefind).
- `node build.js` alone wipes `dist/` and skips the search index; `npm test` builds site + Pagefind,
  runs unit + `check:redirects` + `check:links` (scans `dist/`) + Playwright.

## New machine setup

1. Install Node.js (26+), Python 3.14, git + git-lfs, Pandoc 3.13 (DOCX generation), Obsidian +
   remotely-save.
2. Clone: `git clone https://github.com/AntiManager/AntiManager`.
3. `python -m pip install ftfy python-docx openpyxl pytest`; `cd site; npm ci; npx playwright install chromium`.
4. Copy `.env.example` → `.env` and fill `REMOTE_*` (VPS), `VAULT_DIR`/`ARTICLES_DIR` (local vault),
   `TELEGRAM_*`; copy `.kilo/kilo.json.example` → `.kilo/kilo.json` and fill the paths.
5. Restore the SSH deploy key to `~/.ssh/id_ed25519` (VPS: `chemule@5.129.221.85:2222`), mode user-only.
6. Sync the vault (remotely-save pulls content only); it stays outside the repo.
7. Verify: `cd site; npm run build; npm run test:unit; npx playwright test; npm run check:redirects`;
   `python .kilo/scripts/check_documents.py --vault "<vault>"`; each generator with `--check`;
   `.\site\scripts\verify-deploy.ps1`.
8. Generators default to `C:\Work\Personal Vault`; pass `--vault <path>` on another host.
   `check_system_cards.py` takes the vault as a positional argument.

## Known exceptions

| Finding | Why accepted | Review by |
|---|---|---|
| `verify_repo.ps1` reports `TESTS: skipped` | site tests need `site/node_modules` + Playwright Chromium; run as the full gate | 2026-12-05 |
| Vault outside the repo | content SSOT is the user's Obsidian vault; generators/checkers take `--vault` | 2026-12-05 |
| `.kilo/kilo.json` untracked | local MCP/external paths; template is `.kilo/kilo.json.example` | 2026-12-05 |
| `npm run render:pdf` binary churn | PDF metadata differs per run; render only after content changes | 2026-12-05 |
| Obsidian MCP writes on Cyrillic paths | journal stores UTF-8→cp1251 mojibake; use Write/Edit + Python | 2026-12-05 |
| HP-006 (router skill) not applied | largest skill is 4.7 KB, well under the ~20 KB split threshold | 2026-05-15 |
| HP-014 (nested `site/AGENTS.md`) deferred | `.kilo/AGENTS.md` is load-bearing; revisit if autoload tokens become a problem | 2026-05-15 |
| `git checkout --` not ask-guarded | documented PDF-restore flow would prompt on every material change | 2026-05-15 |
| `harness_lint.py` reports `AGENTS L -` | the script counts only root `AGENTS.md`; the kit check covers `.kilo/AGENTS.md` | 2026-05-15 |
