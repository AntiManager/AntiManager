# AntiManager — Active Context
> Updated: 2026-11-23 · Harness `53107e4`. Plans → `.kilo/plans/`.

## State

- **Conversion & measurement plan + review follow-up (2026-11-23, `VERSION 20261123a`,
  uncommitted):**
  - T1: `analytics.js send()` mirrors every goal to GA4; contact success now dispatches
    `am:goal` → `lead_sent` (`pack` param), separate from Metrika auto-goal
    `contact_data_sent`, so GA4 sees leads and Metrika does not double-count.
  - T2: `workshopFilesHtml()` on 14 articles + all `/full/`; T3 message optional end-to-end;
    T4 `docs/measurement-runbook.md`; T5 a11y 11 pages; T6 AX16 mobile sweep; T7 `VERSION`.
  - Review fixes: tracked `kilo.json` reverted (machine path + auto-`npx` live only in
    gitignored `.kilo/kilo.json`); `<pre>` gets `tabindex="0"` at build (`focusablePre`) and
    AX16 includes `pre`; PDFs regenerated for the 3 chapters with `<pre>`
    (dengi/bey-begi/slozhnye), the other 38 restored; nginx `docx|xlsx` now cached;
    inert `data-toc` removed from the workshop section; contact success wording aligned;
    harness counters 418/8; hot rule: `npm run test:unit` also wipes the Pagefind index.

- Gate 2026-11-23 (after fixes): feedback 51/51; unit 43/43; playwright 418 passed / 8 skipped;
  links 85/85; redirects no drift.

## Next

- Commit (tracked `kilo.json` stays clean), then deploy **service first**, site second;
  run `site/scripts/verify-deploy.ps1`; record live `20261123a` ↔ SHA. Live: no-message lead
  reaches Telegram (`reason=ok`); `lead_sent` appears in Metrika + GA4; «Рабочие файлы»
  downloads; docx/xlsx carry `Cache-Control`. If MCP config is wanted on a new machine,
  copy it into the gitignored `.kilo/kilo.json`.
- User-owned: 12.1 hero, 12.3 author, 12.6 goal names, auto-goal decision (runbook §3),
  `/start/`.

### Resume commands

```powershell
cd site; npm test
cd site; .\scripts\verify-deploy.ps1
```

## Hot rules

- Paths: workspace `C:\Work\Python`; vault `C:\Work\Personal Vault`; `.env` at repo root.
- Python 3.14, Pandoc 3.13, Node 26, Pagefind 1.6, Playwright chromium; E2E port 3100
  (`PLAYWRIGHT_PORT`), never 3000; a foreign app on the port fails every test (rerun 3105).
- `/playbook/` canonical; `/book/` 301; `/cases/` retired.
- `npm test` = unit + redirects + build (Pagefind) + links + E2E; never `node build.js` or
  `npm run test:unit` before E2E — both rewrite `dist/` without the search index.
- Deploy only from a committed tree; `npm test` first; record `VERSION` ↔ SHA; feedback service
  before the site when the API contract changes; SSH 2222 timeouts are transient.
- nginx behind Caddy: keep `real_ip_header X-Forwarded-For` + private `set_real_ip_from`.
- Cyrillic: `Write`/`Edit` or Python, never PowerShell; Obsidian MCP writes are broken.
- Data SSOT: `articles.json` + topics + series; only `published` renders; no Mermaid.
- Long `<pre>`/tables scroll inside the container; AX16 guards at 375px.
