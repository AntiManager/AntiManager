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
- [x] Security hardening follow-up: closed review findings — extracted `site/src/lib/escape.js` (+`assertSlug` slug/id validation, closes output-dir traversal), weapon zone badge via `zoneBadgeHtml()`, canonical URL escaped; added automated regression tests `site/unit/escape.test.js` + `site/unit/build-escape.test.js` (`WEAPONS_FILE` seam, falsifiability-checked); npm `test:unit`/`test:e2e`. Unit 4/4, suite 93/93. Committed `789755c`, pushed to GitHub + GitVerse, deployed to `antimanager.pro` (verified 200 + security headers).
- [x] SEO & content hardening — Phase 1 (technical): dynamic `BUILD_DATE` → sitemap `lastmod` + JSON-LD dates; landing featured 4 cards (was 1); related-links fallback for 6 zone-less weapons; `article:modified_time`/`article:tag`, `og:image` dims, static `BreadcrumbList`; landing meta fixed («4 контура, 22 главы»); raster `og-image.png` (`site/scripts/render-og.js`, `npm run render:og`); tests `site/unit/build-seo.test.js` + `AX12`, `test:unit` serialized. Unit 5/5, suite 96/96. Log: `.kilo/plans/1790008000000-*`. Phase 2 (statuses/stats) pending decision.
- [x] Content readiness audit + harness skill: scanned 30 vault articles (12-point rubric). 22 site articles structurally READY; 23 NEEDS-EDIT; appendices 30–35 DRAFT. Added skill `article-readiness`, command `/article-readiness`, script `.kilo/scripts/article_readiness.py` (report in gitignored `.kilo/reports/`); wired into `book-writing` + `book-editor`. Publication blocked by frontmatter `review`/`book/draft`, not by content.
- [x] SEO review fixes: `plural()` helper in `build.js` (landing meta), dropped duplicate `.slice(0,4)`, guarded `og:image:width/height` for `opts.ogImage` override, `render-og.js` temp-file leak fixed, brittle sitemap assertion dropped. `VERSION`/`BUILD_DATE` coupling deferred to next release. Unit 5/5, suite 96/96.
- [x] Harness cleanup: `/check-site` now runs the full suite (unit + e2e, expected 5 + 96); removed stale `.gigacode/` from `vault-indexer`; compacted `active_context` 6.5 KB → 2.0 KB (history → `.memory/archive/active_context-2026-09.md`). Committed + pushed.

## Planned
- SEO plan Phase 2 (decision): publish 21 `review` weapons; replace fabricated landing stats.
- Deploy after commit (`site/deploy.ps1`) if SEO Phase 1 should go live.

## Technical Debt
- **GitVerse token** embedded in `.git/config` `origin.pushurl` (plaintext credential) — rotate + move to credential helper/SSH. Not a repo file.
- **F16.3 (diagnosed, closed as upstream/cosmetic)** — `config_validation ERROR: Failed to parse frontmatter: No context found for instance` on writes under `.kilo/command|agent/**` is an **upstream Kilo 7.7.5 bug**, content-independent: the write-path validation helper reads the `instance` `LocalContext` (AsyncLocalStorage, `Jo`) outside the scope that provides it, so `GfD()` throws `NotFound("instance")`. The write still succeeds; commands/agents load normally. Secondary upstream defect: `trusted` uses `path.isAbsolute(P) && path.posix.isAbsolute(P)` → `false` for Windows paths. No local fix.
- Metrika `webvisor:true` vs `/privacy/` claim — deferred by user (compliance risk remains).
