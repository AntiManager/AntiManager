# AntiManager — Active Context
> Updated: 2026-11-15 · Harness commit `53107e4`. New plans go to `.kilo/plans/`.

## State

- **Feedback anti-spam (2026-11-15, uncommitted):** signed `GET /api/feedback/challenge` +
  SHA-256 PoW, fill-time trap, `url` honeypot, heuristics, **quarantine instead of drop**
  (`⚠️` prefix or `TELEGRAM_QUARANTINE_CHAT_ID`). Gate: Python 48/48, unit 43, `npm test`
  393/6. Not deployed.
- **Live:** `VERSION 20261106d` ↔ commit `455d25b`; the site tree is unchanged since, so live content
  still maps to `455d25b`. Gate: unit 43/43, `npm test` 378/6, `check:links` 85 pages 0/0/0/0,
  Pagefind 82 / 15,946.
- **Harness (`53107e4`):** HP-003/004/005/010/013 closed; `/closeout` added; `.kilo/AGENTS.md`
  trimmed to 59 lines; local `.kilo/kilo.json` no longer overrides `permission.bash`.
  Checks: `verify_repo.ps1` OK; `check_harness.py` 0; `harness_lint.py` 0.
- **Repo hygiene:** `.run/*` gitignored except the 8 tracked `a3_*` scripts; `.kilo/reports/`
  local-only; untracked scratch removed (`b975270`).

## Next

- **Deploy feedback anti-spam:** `site/feedback/deploy.ps1` then `site/deploy.ps1` (nginx conf
  changed: challenge location + `limit_req_zone`), then re-record `VERSION` ↔ SHA. Verify live
  with one clean submission and one probe.
- **User-owned:** 12.1 hero value proposition, 12.3 named author/experience facts, Metrika goal
  names (12.6), `/start/` editorial approval.
- **Draft:** `site/prototype/team-landing.html` (`dc90922`, `noindex`, out of the build) — needs
  real contacts, number reconciliation (17 vs 15+ plants; >350 vs >500 млн ₽), publish decision.
- No open technical P0/P1. New work starts as a fresh local plan; ambiguous work gets a SPEC first.

### Resume commands

```powershell
cd site; npm test
cd site; .\scripts\verify-deploy.ps1
cd site; npm run check:links; npm run check:redirects
```

## Hot rules

- Paths: workspace `C:\Work\Python`; vault `C:\Work\Personal Vault`; `.env` at repo root.
- Toolchain: Python 3.14 + ftfy/python-docx/openpyxl/pytest; Pandoc 3.13; Node 26 + Pagefind 1.6;
  Playwright chromium; tests use port 3100 (`PLAYWRIGHT_PORT`), never 3000.
- `/playbook/` canonical; `/book/` single-hop 301; `/cases/` retired. Series «Имитация развития».
- `npm test` = unit + `check:redirects` + build (site + Pagefind) + `check:links` + Playwright.
- Deploy only from a committed tree; `npm test` first; record `VERSION` ↔ SHA. Gotchas:
  `.kilo/harness.md` §Deploy provenance.
- Generators default to the vault (`--vault`; `check_system_cards.py` positional); `--check`
  compares marker regions — re-run the generator, never hand-edit markers.
- Obsidian MCP writes on Cyrillic paths are broken — use `Write`/`Edit` + Python; guard encoding.
- Data SSOT: `articles.json` + topics + series; only `published` renders; no Mermaid.
  `render:pdf` two-pass; restore untouched PDFs with `git checkout -- site/materials`.
- Front-end/search gotchas: `.kilo/harness.md` §Front-end gotchas.
