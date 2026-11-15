# AntiManager — Active Context
> Updated: 2026-11-15 · Harness commit `53107e4`. New plans go to `.kilo/plans/`.

## State

- **Live `VERSION 20261115a` ↔ `5a68d9c`** (deployed 2026-11-15). Feedback anti-spam is in
  production: signed `GET /api/feedback/challenge` + SHA-256 PoW, fill-time trap, `url` honeypot,
  heuristics, quarantine instead of drop. Live evidence: clean PoW lead → `deliver reason=ok`;
  no-challenge probe → `quarantine reason=latin_only,short_no_detail,price_probe,latin_name,
  random_mailbox,no_challenge`; honeypot POST → `drop reason=honeypot`, no delivery.
  Gate: Python 49/49, unit 43/43, `npm test` 393 passed / 6 skipped, `check:links` 85 pages
  clean, Pagefind 82 / 15,946, `verify-deploy.ps1` passed.
- **Real client IP fixed (`5a68d9c`):** Caddy runs as a container, so nginx saw one bridge address
  and every feedback limit (nginx `limit_req`, service per-IP) was effectively global.
  `real_ip_header X-Forwarded-For` + private `set_real_ip_from` restore `$remote_addr`; `nginx -t`
  on `nginx:alpine` first. Confirmed live: after the fix a honeypot POST logged a public client
  `ip=` (`drop reason=honeypot`), where every earlier event carried Caddy's bridge address.
- **Harness (`53107e4`):** HP-003/004/005/010/013 closed, `/closeout` added; checks green.

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
  Playwright chromium; tests use port 3100 (`PLAYWRIGHT_PORT`), never 3000.
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
