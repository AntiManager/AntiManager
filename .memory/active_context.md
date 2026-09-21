# AntiManager — Active Context
> Updated: 2026-09-21

## Current Task
SEO & content hardening (`.kilo/plans/1790008000000-seo-content.md`) — **Phase 1 DONE**,
Phase 2 pending a user decision.

- Phase 1 (was uncommitted): dynamic `BUILD_DATE` → sitemap `lastmod` + JSON-LD dates;
  landing featured block = 4 cards; related-links fallback for 6 zone-less weapons;
  `article:modified_time`/`article:tag`, `og:image` dims, static `BreadcrumbList`;
  landing meta «4 контура, 22 главы»; raster `og-image.png`
  (`site/scripts/render-og.js`, `npm run render:og`).
- Tests: unit 5/5; Playwright 96/96 (32 × 3). Run all: `cd site; npm test`.
- Log: `.kilo/plans/1790008000000-seo-content-execution-log.md`.

## Harness state (this session)
- New: skill `article-readiness`, command `/article-readiness`,
  script `.kilo/scripts/article_readiness.py` (report in gitignored `.kilo/reports/`);
  wired into `book-writing` + `book-editor`.
- `.kilo/AGENTS.md` map: skills 8, commands 9.
- `/check-site` now runs the full suite (`npm test`); `vault-indexer` stale `.gigacode/`
  exclusion removed.
- Memory compacted: old `active_context` history → `.memory/archive/active_context-2026-09.md`.

## Next step
- Phase 2 decision gates: publish 21 `review` weapons; replace fabricated
  landing stats (2 847 / 113 / 47).
- Deploy after commit (site/deploy.ps1) if the SEO Phase 1 output should go live.

## Hot rules / deferred
- Metrika/Webvisor untouched; `webvisor:true` vs `/privacy/` wording — deferred by user (compliance risk).
- `yandex-verification` meta needs the user's code.
- GitVerse token in `.git/config` `origin.pushurl` (plaintext) — rotate + move to credential helper/SSH (HIGH).
- `chapters.json`/`tools.json` — unreferenced dead data (remove or wire), decide separately.
- `build.js` `VERSION` static vs dynamic `BUILD_DATE` — couple on next release.
- Residual: `content_body` is raw HTML (malicious PR to `src/content/*.html`); rely on PR review/branch protection.
