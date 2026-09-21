# AntiManager — Progress
> Updated: 2026-09-21

## Done
- [x] Brutalist rebuild v2: Black+Red+White, 32 pages, star map (static SVG)
- [x] SEO: OG, canonical, structured data, favicon, sitemap
- [x] UX fixes: A11y, hamburger menu, scroll-top, mobile grids, hover guards
- [x] Cache-busting `?v=`, nginx hardening, permission fix
- [x] Playwright tests: 84 (28 × 3 viewports)
- [x] Secrets extracted to .env, sensitive data scrubbed
- [x] Repo restructured: site/ + manifestos root
- [x] Harness audit & optimization cascade (C1–C5): docs/config repaired, skills rewritten to fact, portable config, harness map, E2E made hermetic (66/66). Log + retrospective in `.kilo/plans/1790002457744-*`.
- [x] Follow-up QA: AX08 mobile-nav, AX09 arsenal zone-filter, AX10 system-map presence added; suite 84/84. Committed + pushed.
- [x] Security hardening (audit 2026-09-21): output escaping in `build.js` (text fields, slug/zone/status, JSON-LD), DOM-XSS fixed in live widgets 04/16/19 (+AX11 regression, falsifiability-checked), dead JS removed (4 files / 682 lines + `dist` clean), nginx security headers, broken OG image fixed, username leak in `add-fm-00.py` fixed. Suite 93/93. Log: `.kilo/plans/1790006200000-*`.
- [x] Security hardening follow-up: closed review findings — extracted `site/src/lib/escape.js` (+`assertSlug` slug/id validation, closes output-dir traversal), weapon zone badge via `zoneBadgeHtml()`, canonical URL escaped; added automated regression tests `site/unit/escape.test.js` + `site/unit/build-escape.test.js` (`WEAPONS_FILE` seam, falsifiability-checked); npm `test:unit`/`test:e2e`. Unit 4/4, suite 93/93. Not committed.

## Planned
None on this laptop.

## Technical Debt
- **GitVerse token** embedded in `.git/config` `origin.pushurl` (plaintext credential) — rotate + move to credential helper/SSH. Not a repo file.
- F16.3 — `config_validation ERROR` when writing `.kilo/command|agent/*.md` (environment/validator, not content).
- Metrika `webvisor:true` vs `/privacy/` claim — deferred by user (compliance risk remains).
