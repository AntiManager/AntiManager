# AntiManager — Active Context
> Updated: 2026-11-15 · Harness `53107e4`. Plans → `.kilo/plans/`.

## State

- **Contact phone published (2026-11-15, `57d3a94`, live `20261115b`):** `+7 922 180-43-61` on
  `/contact/` (`tel:` E.164, also in `<noscript>`), in the footer «Связаться» on every page, and
  as `Organization.telephone` in JSON-LD (country + area code). Live check:
  contact tel + visible number, home schema telephone, `20261115b` live;
  `verify-deploy.ps1` passed. Gate: unit 43/43, `check:links` 85/85, E2E 393/6.
- **Anti-spam deployed (`848f4f1`; was live as `20261115a` ↔ `5a68d9c`).** Signed challenge + SHA-256
  PoW, fill-time trap, `url` honeypot, heuristics, quarantine instead of drop. Live evidence and
  details in `progress.md`. Gate: Python 49/49, unit 43/43, E2E 393/6, `check:links` 85 pages.
- **Real client IP fixed (`5a68d9c`):** `real_ip_header X-Forwarded-For` + private
  `set_real_ip_from` in `deploy/nginx.conf`; without them every per-IP limit is one global bucket.

## Next

- Confirm `feedback … ip=<public>` in `docker logs antimanager-feedback` on the next submission
  (SSH port 2222 is intermittent; retry, do not force).
- Optional hardening: set `TELEGRAM_QUARANTINE_CHAT_ID` so quarantined probes stop landing in the
  main chat with a `⚠️` prefix.
- **User-owned:** 12.1 hero value proposition, 12.3 named author/experience facts, Metrika goal
  names (12.6), `/start/` editorial approval.
- **Draft:** `site/prototype/team-landing.html` (`noindex`) — contacts, numbers, publish decision.
- No open technical P0/P1.

### Resume commands

```powershell
cd site; npm test
cd site; .\scripts\verify-deploy.ps1
```

## Hot rules

- Paths: workspace `C:\Work\Python`; vault `C:\Work\Personal Vault`; `.env` at repo root.
- Toolchain: Python 3.14 + ftfy/python-docx/openpyxl/pytest; Pandoc 3.13; Node 26 + Pagefind 1.6;
  Playwright chromium; tests use port 3100 (`PLAYWRIGHT_PORT`), never 3000. Port 3100 can be
  taken by a foreign app: `reuseExistingServer` then tests it (384 false failures seen
  2026-11-15) — check the port and rerun with `PLAYWRIGHT_PORT=3105`.
- `/playbook/` canonical; `/book/` single-hop 301; `/cases/` retired. Series «Имитация развития».
- `npm test` = unit + `check:redirects` + build (site + Pagefind) + `check:links` + Playwright.
- Deploy only from a committed tree; `npm test` first; record `VERSION` ↔ SHA. Gotchas:
  `.kilo/harness.md` §Deploy provenance; SSH 2222 timeouts are transient — verify live, retry.
- nginx sits behind Caddy: keep `real_ip_header X-Forwarded-For` + private `set_real_ip_from`, or
  every per-IP limit becomes one global bucket.
- Generators default to the vault (`--vault`); `--check` compares marker regions — re-run the
  generator, never hand-edit markers.
- Obsidian MCP writes on Cyrillic paths are broken — use `Write`/`Edit` + Python; guard encoding.
- Data SSOT: `articles.json` + topics + series; only `published` renders; no Mermaid.
  `render:pdf` two-pass; restore untouched PDFs with `git checkout -- site/materials`.
