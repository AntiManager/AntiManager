# AntiManager — Progress
> Updated: 2026-11-23 · Full pre-compaction log → `.memory/archive/progress-history-2026-10-24.md`

Rolling log, recent first. Keep this file under 8 KB; older entries → `.memory/archive/`.

## Done

- **`/products/` commercial page (2026-11-23, `8b87547`, live `20261123b`):** new
  static route `siteRoutes.products()` → `/products/`, authored `src/content/products.html`:
  seven owner questions → seven products (`#dengi`…`#peredacha`) with result / artifacts / term /
  KPI / format, the 0–7 order ladder with explicit "not before" bans, and the product-vs-interim
  table. No prices, client names or case numbers (test-asserted). Seven `?pack=` slugs added to
  `js/contact.js` and `feedback/server.py`; `unit/build-products.test.js` parses both `PACK_LABELS`
  maps and fails on drift, plus Playwright cases for `?pack=dengi|peredacha` and four home project
  cards sharing one row at 1280px. Home project block is now 4 cards
  (`repeat(4, minmax(0, 1fr))` ≥1025px); footer and sitemap entries; `--color-surface` token
  replaces `#111` literals; `no aria-current` asserted (deliberately not in the header nav);
  `/products/` added to the axe smoke list and the no-hscroll sweep; `verify-deploy.ps1` checks
  the live page and sitemap. Evidence: unit 45/45; `npm test` 427 passed / 8 skipped; `check:links`
  86/86; redirects no drift; `verify_repo.ps1` STATUS OK. Deployed: service first (verify probe
  aborted spuriously; container `Up (healthy)`), then the site (`VERSION 20261123b`);
  `verify-deploy.ps1` passed (`/products/` 200, sitemap match, 301 matrix); live CSS
  `?v=20261123b`. Untracked by design: `docs/seo-analysis-2026-11-23.md`,
  `site/prototype/products.html`.
- **Review follow-up on the measurement plan (2026-11-23, `a695776`, live `20261123a`):**
  reverted the tracked `kilo.json` MCP block (machine settings stay in gitignored
  `.kilo/kilo.json`); added `lead_sent` (`am:goal` on a successful POST → Metrika + GA4, distinct
  from Metrika's `contact_data_sent`); build-time `focusablePre()` (`tabindex="0"` on scrollable
  `<pre>`, fixes the axe regression) + `pre` in the AX16 sweep; regenerated 3 PDFs and restored
  the other 38; `docx|xlsx` nginx cache; runbook §3/§5/§6 and the harness counters (418/8).
  Evidence: feedback 51/51; unit 43/43; playwright 418/8; links 85/85; redirects no drift.
  Deployed `20261123a`: service first; `verify-deploy.ps1` passed; live no-message lead →
  `deliver reason=ok`; IndexNow 82 URLs.
- **Conversion & measurement plan (2026-11-23, committed `a695776`, live `20261123a`):** T1 mirrors
  every Metrika goal to GA4 via `gtag('event', …)` (independent try/catch); Playwright blocks both
  tags and asserts `window.dataLayer`. T2 adds «Рабочие файлы» (`workshopFilesHtml`) to all 14
  articles and every `/full/` page: express-audit XLSX, system-card DOCX, one context DOCX mapped
  from zone/topic, documents hub; print-hidden, existence-gated. T3 makes the
  contact message optional end-to-end (no `required`, hint, reply-window note; server accepts
  empty/omitted, prints «Сообщение: —», `short_no_detail` only on non-empty text). T4 adds
  `docs/measurement-runbook.md` and fixes the Metrica P1 recommendations. T5 extends a11y to 11
  pages and attaches `serious` findings. T6 adds the AX16 mobile sweep and fixes page-level
  horizontal scroll from unwrapped `<pre>` blocks in ch.07. T7 bumps `VERSION`, adds the feedback
  unittest to the harness full gate. Evidence: feedback 51/51; unit 43/43; `npm test` 415 passed /
  8 skipped; `check:links` 85/85; `check:redirects` no drift; `verify_repo.ps1` STATUS OK.
- **Contact phone published (2026-11-15, `57d3a94`, live `20261115b`):** `+7 922 180-43-61` on
  `/contact/`, in the footer «Связаться» column and as `Organization.telephone`; `tel:` link +
  crawlable text, no obfuscation. Evidence: unit 43/43; `check:links` 85/85; E2E 393 passed /
  6 skipped (port 3105 — 3100 was a foreign app); live contact/schema checked; deploy verified.
- **Feedback anti-spam deployed (2026-11-15, `848f4f1`, live `20261115a` ↔ `5a68d9c`):** layered
  defence for `/contact/` — signed challenge + SHA-256 proof of work (`GET /api/feedback/challenge`),
  fill-time trap, `url` honeypot, content heuristics (`latin_only`, `short_no_detail`,
  `price_probe`, `random_mailbox`, `link_in_message`, `latin_name`), per-IP + global limits, nginx
  `limit_req`, and quarantine delivery instead of silent drops. Turnstile/reCAPTCHA rejected (unreachable/unlawful for the Russian audience); no
  third-party script, CSP untouched. Pre-commit review fixed a `TypeError` path: challenge
  signatures are now compared as bytes, so a non-ASCII signature is `bad_challenge`, not a 500.
  Evidence: Python 49/49; unit 43/43; `npm test` 393 passed / 6 skipped; `check:links` 85 pages
  clean; live clean PoW lead → `deliver reason=ok`; no-challenge probe → `quarantine` with 6
  reasons; honeypot POST → `drop reason=honeypot`, no delivery; `verify-deploy.ps1` passed.
- **Real client IP behind Caddy fixed (2026-11-15, `5a68d9c`):** live logs showed `ip=172.19.0.6`
  (Caddy's bridge address), so the nginx `limit_req` zone and the service per-IP limiter were one
  global bucket — 5 submissions / 10 min for the whole site. Added `real_ip_header
  X-Forwarded-For` + private `set_real_ip_from` ranges to `deploy/nginx.conf` (validated with
  `nginx -t` on `nginx:alpine`), redeployed the site. Confirmed live: after the fix a honeypot
  POST logged a public client `ip=` (`drop reason=honeypot`), where every earlier event carried
  Caddy's bridge address.
- **Harness optimization (2026-11-15, `53107e4`):** `.kilo/AGENTS.md` cut 123 → 59 lines
  (10.8 → 3.2 KB) per HP-001; site IA, language policy, skills/commands/scripts, publication
  rules, MCP, security protocol and new-machine setup moved to `.kilo/harness.md` (on demand).
  Local `.kilo/kilo.json` and `kilo.json.example` no longer set `permission.bash: allow` (it
  overrode the root asks); force-push patterns cover `-f*`/`--force*` and `rm`/`del`/`rmdir`.
  Evidence: `verify_repo.ps1` `STATUS: OK`; `check_harness.py .kilo` `problems: 0`;
  `harness_lint.py --repo AntiManager` `total findings: 0`; all JSON parses.
- **Harness completion (2026-11-15, `53107e4`, 5 files):** added `/closeout` (gate → artifacts →
  one memory write per file); `kilo.json` `bash` now asks on `Remove-Item`, `git reset --hard`,
  `git clean`, force-push, `docker compose down -v` (HP-003); memory budgets enforced (HP-004);
  Delegation + SPEC-before-plan in `.kilo/AGENTS.md` (HP-010/013); provenance updated. HP-006 N/A
  (largest skill 4.7 KB); HP-014 deferred.
- **Repo hygiene (2026-11-15):** `.run/*` gitignored except 8 tracked `a3_*` scripts (`b975270`);
  untracked scratch (~15 MB) and `site/tmp-widget-*.mjs` removed; `README.md` and
  `.kilo/harness.md` refreshed.
- **Prototype tracked (2026-11-15):** `site/prototype/team-landing.html` (`dc90922`, `noindex`, out
  of the build). Content review pending.
- **2026-11-06 summary entries moved to** `.memory/archive/progress-history-2026-11-06-summary.md`
  (IA cutover, plan commit, harness optimization); detailed evidence stays in
  `.memory/archive/progress-history-2026-11-06.md`.

## Planned

- **No active plan.** User-owned: `/start/` editorial approval, named author (12.3), hero value
  proposition (12.1), Metrika goal names (12.6).
- Process-library refactor (`1791721561689`) paused 2026-11-06 — not resumed; resume point in its
  execution log.
- **Cancelled 2026-11-06:** DRAFT series 30–35.
- Publish per-article extras into `site/materials/<slug>/` + `materials.json`.
- Deferred: CSP `script-src`/`default-src`, Metrika `webvisor` `/privacy/` wording.

## Technical Debt

- **Accepted risks (2026-11-06):** GitVerse token in `.git/config` pushurl, VPS SSH key, Metrika
  `webvisor:true` vs `/privacy/`.
- **GitVerse token** in `.git/config` (plaintext) — rotate + move to credential helper/SSH.
- **F16.3:** Kilo 7.7.5 frontmatter parse warning on `.kilo/command|agent/**` writes
  (content-independent; write succeeds). No local fix.
