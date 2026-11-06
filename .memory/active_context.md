# AntiManager — Active Context
> Updated: 2026-11-06 · No active plan. New plans go to `.kilo/plans/`.

## State

- **Live:** `VERSION 20261106d` ↔ commit `455d25b` (pushed to `origin`/`gitverse`; deployed before the
  commit from the identical tree). Gate: unit 43/43, `npm test` 378 passed / 6 skipped,
  `check:links` 85 pages 0/0/0/0, `check:redirects` no drift, Pagefind 82 / 15,946.
- **Harness optimization (2026-11-06):** global turn/audit budgets (≥2.5 calls/turn; ≤120/80
  turns), bounded reviewer (15 steps, diff-only), deploy provenance (`VERSION` ↔ SHA);
  `session_audit.py` now counts deploy/live checks and reports tools/turn + cache/turn. Local
  `.kilo/kilo.json` paths repaired to `C:\Work\...`; `verify_repo.ps1` needs `-Repo <path>`.
- **History:** site-IA plan closed; details → `.memory/archive/active-context-2026-11-06-site-ia.md`.

## Next

- **User-owned:** 12.1 hero value proposition, 12.3 named author/experience facts, Metrika goal
  names (12.6), `/start/` editorial approval.
- No open technical P0/P1. Start new work as a fresh local plan.

### Resume commands

```powershell
cd site; npm test
cd site; .\scripts\verify-deploy.ps1
cd site; npm run check:links; npm run check:redirects
```

## Hot rules

- Paths: workspace `C:\Work\Python`; vault `C:\Work\Personal Vault`; `.env` at repo root.
- Toolchain: Python 3.14 + `ftfy python-docx openpyxl pytest`; Pandoc 3.13; Node 26 + Pagefind 1.6;
  Playwright chromium; tests use port 3100 (`PLAYWRIGHT_PORT`), never 3000.
- `/playbook/` is canonical; `/book/` is a single-hop 301. Series «Имитация развития».
  `/about/headquarters/` and `/headquarters/` 301 to `/contact/` (club retired).
- `npm test` = unit + `check:redirects` + build (site + Pagefind) + `check:links` + Playwright.
  `node build.js` alone wipes `dist/` and skips the search index; unit tests share `dist/`
  (`--test-concurrency=1`); `check:links` scans `dist/`.
- Search: `/search/` noindex, not in sitemap, no `data-pagefind-body`; future CSP `script-src`
  needs `'self'` + `wasm-unsafe-eval`; Pagefind matches prefixes.
- Widgets: one static back button outside `#<id>Question` (AX15).
- Deploy: `npm test` first; `nginx -t` on a throwaway `nginx:alpine`; SSH 2222 is flaky; Caddy
  reload may refuse `localhost:2019` (non-fatal); `verify-deploy.ps1` probes 3xx with `HttpClient`.
  Deploy only from a committed tree; record `VERSION` ↔ SHA.
- Generators default to the vault (`--vault`; `check_system_cards.py` positional); `--check`
  compares marker regions — re-run the generator, never hand-edit markers.
- Obsidian MCP writes on Cyrillic paths are broken — use `Write`/`Edit` + Python; guard encoding.
- Data SSOT: `articles.json` + topics + series; only `published` renders. Every article `.md`:
  title block + `---`; no Mermaid. `render:pdf` two-pass; restore untouched PDFs before commit.
- Long H1 words are capped, not split (`.content-page h1`, `.hero-gen h1`, `.documents-hub h1`,
  `.privacy-page h1`); `/method/` `#offer` sits before `#problem`.
