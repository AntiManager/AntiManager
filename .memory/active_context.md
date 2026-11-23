# AntiManager — Active Context
> Updated: 2026-11-23 · Harness `53107e4`. Plans → `.kilo/plans/`.

## State

- **`/products/` page (2026-11-23, committed this change, not deployed).** Static route
  `siteRoutes.products()`; `src/content/products.html`: 7 owner questions → 7 products
  (`#dengi`…`#peredacha`), order ladder 0–7, product-vs-mandate table; no prices/clients/cases
  (test-asserted). Pack slugs added to `js/contact.js` + `feedback/server.py`;
  `unit/build-products.test.js` parses both and fails on drift. Home project block is 4 cards
  (`repeat(4,…)` ≥1025px); footer + sitemap entries; `--color-surface` token. Not in the header
  nav (no `aria-current`). `docs/seo-analysis-2026-11-23.md` and `site/prototype/products.html`
  stay untracked.
- **Conversion & measurement (2026-11-23, `a695776`, live `20261123a`):** GA4 mirrors every
  Metrika goal; contact success dispatches `am:goal` → `lead_sent` (separate from Metrika's
  `contact_data_sent`); «Рабочие файлы» on 14 articles + `/full/`; message optional end-to-end;
  `docs/measurement-runbook.md`; a11y 11 pages + AX16; `VERSION` bump.
- Gate 2026-11-23: feedback 51/51; unit 45/45; playwright 427 passed / 8 skipped; links 86/86;
  redirects no drift; `verify_repo.ps1` STATUS OK.

## Next

- Deploy `/products/`: feedback service first (`site\feedback\deploy.ps1` — new packs must be
  accepted), then the site (`site\deploy.ps1`), then `scripts\verify-deploy.ps1`. Record
  `VERSION` ↔ SHA; push the branch.
- User-owned: hero 12.1, author 12.3, Metrika goal names 12.6, auto-goal decision (runbook §3),
  `/start/`. Check GA4 `lead_sent` in the first report; never merge Metrika/GA4.

### Resume commands

```powershell
cd site; npm test
cd site; .\scripts\verify-deploy.ps1
```

## Hot rules

- Paths: workspace `C:\Work\Python`; vault `C:\Work\Personal Vault`; `.env` at repo root.
- Python 3.14, Pandoc 3.13, Node 26, Pagefind 1.6, Playwright chromium; E2E port 3100
  (`PLAYWRIGHT_PORT`), never 3000; a foreign app on the port fails tests (rerun 3105).
- `/playbook/` canonical; `/book/` 301; `/cases/` retired.
- `npm test` = unit + redirects + build (Pagefind) + links + E2E; never `node build.js` or
  `npm run test:unit` before E2E — both rewrite `dist/` without the search index.
- Deploy only from a committed tree; `npm test` first; record `VERSION` ↔ SHA; feedback service
  before the site when the API contract changes; SSH 2222 timeouts are transient (retry).
- nginx behind Caddy: keep `real_ip_header X-Forwarded-For` + private `set_real_ip_from`.
- Cyrillic: `Write`/`Edit` or Python, never PowerShell; Obsidian MCP writes are broken.
- Data SSOT: `articles.json` + topics + series; only `published` renders; no Mermaid; long
  `<pre>`/tables scroll inside the container (AX16 at 375px).
