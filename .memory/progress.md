# AntiManager — Progress
> Updated: 2026-11-23 · Full pre-compaction log → `.memory/archive/progress-history-2026-10-24.md`

Rolling log, recent first. Keep this file under 8 KB; older entries → `.memory/archive/`.

## Done

- **Review follow-up on the measurement plan (2026-11-23, uncommitted):** reverted the tracked
  `kilo.json` MCP block (machine vault path + auto-`npx` remain only in gitignored
  `.kilo/kilo.json`); added `lead_sent` — `contact.js` dispatches `am:goal` on a successful POST,
  `analytics.js` mirrors it to Metrika and GA4, keeping it distinct from the Metrika auto-goal
  `contact_data_sent`; new Playwright assertion for both systems. Added build-time
  `focusablePre()` (`tabindex="0"` on scrollable `<pre>`, fixes the axe
  `scrollable-region-focusable` regression) and included `pre` in the AX16 mobile sweep;
  regenerated PDFs for the 3 chapters containing `<pre>` and restored the other 38; added
  `docx|xlsx` to the nginx asset cache; removed the inert `data-toc` from the workshop section;
  aligned the contact success wording with the form; updated runbook §3/§5/§6, the Metrica
  analysis note, harness counters (418/8) and the "test:unit wipes Pagefind" hot rule.
  Evidence: feedback 51/51; unit 43/43; playwright 418 passed / 8 skipped; links 85/85;
  redirects no drift. Not committed or deployed.
- **Conversion & measurement plan (2026-11-23, `VERSION 20261123a`, uncommitted):** T1 mirrors
  every Metrika goal to GA4 via `gtag('event', …)` (independent try/catch); Playwright blocks both
  tags and asserts `window.dataLayer`. T2 adds «Рабочие файлы» (`workshopFilesHtml`) to all 14
  articles and every `/full/` page: express-audit XLSX, system-card DOCX, one context DOCX mapped
  from zone/topic, documents hub; `data-toc="skip"`, print-hidden, existence-gated. T3 makes the
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
- **Harness optimization (2026-11-06):** turn/audit budgets, bounded reviewer, deploy provenance;
  `session_audit.py` counts deploy/live checks; local `.kilo/kilo.json` paths repaired.
- **Site IA releases A/B/C + S7.5 (2026-11-06):** routes cutover and 301 map, header/footer,
  `/start/`, `/method/` hub, `/about/`, Pagefind `/search/`, a11y, CTA/analytics, prev/next,
  free lead magnet. Closure gate: unit 43/43, `npm test` 378/6 skipped, check-links 85 pages
  0/0/0/0, Pagefind 82 / 15,946. Deployed `20261106d`; plan closed and archived.
- **Plan committed (2026-11-06):** `455d25b` (112 files) pushed to GitHub + GitVerse; live
  `VERSION` ↔ SHA recorded. Session audit: 18 sessions, $4.24, 0 secrets, 0 dangerous commands.
- **Work stream closed (2026-11-06):** Yandex.Webmaster confirmed; remaining queue closed by user.
- **Earlier 2026-10:** methodology suite, SEO, IndexNow, systems map, PS-audit, vault split,
  articles 53–55 → `.memory/archive/progress-history-2026-10-24.md`.

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
