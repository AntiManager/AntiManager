# AntiManager — Active Context
> Updated: 2026-09-21

## Current Task
Security hardening cascade (`.kilo/plans/1790006200000-security-hardening.md`) — **DONE** (committed `789755c`, pushed GitHub+GitVerse, deployed 2026-09-21).

- Trigger: security audit of the public repo + site (report-only, 2026-09-21).
- Done: `build.js` output escaping (text fields via `sanitize`, slug/zone/status, JSON-LD `\u003c`); DOM-XSS fixed in live widgets 04/16/19 with local `escHtml()`; **AX11** regression added to `ux-critical.spec.js` (falsifiability-checked — fails on the unfixed widget); dead JS removed (`map.js`, `common.js`, `interactive/*` — 682 lines) + `dist/` clean step in `build.js`; nginx security headers; broken OG image (`/og-image.png` → `/og-image.svg`); username leak removed from `add-fm-00.py`.
- Verification: `node build.js` exit 0; `npx playwright test` → **93 passed** (31 × 3 viewports).
- Log: `.kilo/plans/1790006200000-security-hardening-execution-log.md`.

## Recent Activity
- User decisions: Metrika/Webvisor **untouched** (compliance risk remains); dead JS **removed**.
- Negative test: reverting one widget made AX11 fail (`window.__xss` set), proving the test is not vacuous.
- Skills updated to drop references to deleted JS (`web-developer`, `site-designer`).
- Committed `789755c` and pushed to GitHub + GitVerse; deployed via `site/deploy.ps1`; verified `https://antimanager.pro/` → 200 with all new security headers.
- Deploy note: final optional Caddy-reload SSH step hit a transient timeout; the site/headers are live, no impact.

## Manual / deferred
- [ ] **GitVerse token** in `.git/config` `origin.pushurl` (plaintext) — user must rotate + switch to credential helper/SSH. HIGH priority.
- [ ] Metrika `webvisor:true` vs `/privacy/` wording — deferred by user.

## Review findings — resolved (follow-up session)
- [x] `site/build.js:483` — weapon-page zone badge now uses `zoneBadgeHtml(w.zone)`.
- [x] `site/build.js:523` — `canonicalUrl` now uses `escapeHtml(w.slug)`.
- [x] `site/build.js:36-39` — build-time escaping now has automated regression tests:
  `site/src/lib/escape.js` + `site/unit/escape.test.js` (unit) and
  `site/unit/build-escape.test.js` (integration, `WEAPONS_FILE` seam, falsifiability-checked).
- [x] Slug validation (`assertSlug`) closes the traversal path via the output dir.
- [ ] Accepted residual risk: `content_body` is raw HTML (malicious PR to `src/content/*.html`);
  mitigate via PR review/branch protection.
- [ ] COSMETIC: generate PNG og-image; JSON-LD pre-escaped; `escHtml` duplication; nginx header duplication.
- Verification: `node build.js` exit 0; `npm run test:unit` → 4 passed; Playwright → 93 passed.

## Open Questions / Follow-ups
- [ ] F16.3 — `config_validation ERROR` when writing `.kilo/command|agent/*.md` (environment/validator, not content).
- [ ] Next content update for the site?
- [ ] SEO optimisation follow-up?
