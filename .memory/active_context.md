# AntiManager — Active Context
> Updated: 2026-09-21

## Current Task
Publish-readiness hardening of source vault articles, **one at a time** (Layer 1
screen + Layer 2 editorial). Articles **00 «Маятник управления»**, **01 «Manifestum
Imperii Rationalis»**, **02 «Управление сложными системами» DONE → 12/12**, and
**00/01 are DEPLOYED** to `antimanager.pro` (verified live). Next: article **03**
«Системная динамика в производстве» — Layer 2 editorial pass.
Parked: SEO plan Phase 2 (publish 21 `review` weapons; replace fabricated landing stats).

- Phase 1 (was uncommitted): dynamic `BUILD_DATE` → sitemap `lastmod` + JSON-LD dates;
  landing featured block = 4 cards; related-links fallback for 6 zone-less weapons;
  `article:modified_time`/`article:tag`, `og:image` dims, static `BreadcrumbList`;
  landing meta «4 контура, 22 главы»; raster `og-image.png`
  (`site/scripts/render-og.js`, `npm run render:og`).
- Tests: unit 5/5; Playwright 99/99 (33 × 3). Run all: `cd site; npm test`.
- Log: `.kilo/plans/1790008000000-seo-content-execution-log.md`; article-readiness
  log: `.kilo/plans/1790010500000-article-readiness-execution-log.md`.

## Harness state (this session)
- Article 01 site: `build.js` manifesto now rendered from structured
  `manifestoValues/manifestoPrinciples/manifestoClosing` (drives both `/manifesto/`
  and the landing teaser — no drift); `brutalist.css` +`.manifesto-preamble`/
  `.manifesto-value-body`; `ux-critical.spec.js` +`AX13`. Suite 99/99.
- New: skill `article-readiness`, command `/article-readiness`,
  script `.kilo/scripts/article_readiness.py` (report in gitignored `.kilo/reports/`);
  wired into `book-writing` + `book-editor`.
- `.kilo/AGENTS.md` map: skills 8, commands 9.
- `/check-site` now runs the full suite (`npm test`); `vault-indexer` stale `.gigacode/`
  exclusion removed.
- Memory compacted: old `active_context` history → `.memory/archive/active_context-2026-09.md`.

## Next step
- Continue article-by-article readiness: article **03 «Системная динамика в производстве»**
  — Layer 2 editorial pass (facts, related tools/chapters, style), then site sync if
  the content changes.
- Articles 00/01 site work: DONE and **deployed** (00 `content/00-*.html`; 01 full
  `/manifesto/` page). Build OK, suite 99/99.
- Article 02: vault Layer 2 done (no site sync needed — no content change).
- SEO Phase 2 decision gates remain parked (publish 21 `review` weapons; replace
  fabricated landing stats 2 847 / 113 / 47).

## Hot rules / deferred
- Metrika/Webvisor untouched; `webvisor:true` vs `/privacy/` wording — deferred by user (compliance risk).
- `yandex-verification` meta needs the user's code.
- GitVerse token in `.git/config` `origin.pushurl` (plaintext) — rotate + move to credential helper/SSH (HIGH).
- `chapters.json`/`tools.json` — unreferenced dead data (remove or wire), decide separately.
- `build.js` `VERSION` static vs dynamic `BUILD_DATE` — couple on next release.
- Residual: `content_body` is raw HTML (malicious PR to `src/content/*.html`); rely on PR review/branch protection.
