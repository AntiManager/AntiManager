# AntiManager — archived active context (2026-09)

Append-only history. Compacted out of `.memory/active_context.md` on 2026-09-21 to keep
the auto-loaded boot trio within its size caps (`memory-bank` skill). Do not rewrite.

## Archive append 2026-09-21 (SEO Phase 1, security review follow-up, content-readiness audit)

### Current Task (as of compaction)
SEO & content hardening (`.kilo/plans/1790008000000-seo-content.md`) — **Phase 1 DONE**, Phase 2 pending user decision.

- Trigger: SEO/content audit 2026-09-21 (this session).
- Phase 1 done (uncommitted): dynamic `BUILD_DATE` (env seam) → sitemap `lastmod` + JSON-LD dates; landing featured block = 4 cards (was 1); related-links fallback for 6 zone-less weapons (zone → thinker → tags → zone-less); `article:modified_time`, `article:tag`, `og:image:width/height`, static `BreadcrumbList`; landing meta «4 контура, 22 главы»; raster `og-image.png` via new `site/scripts/render-og.js` (Playwright, 1200×630) + `npm run render:og`.
- Tests: new `site/unit/build-seo.test.js`; `test:unit` now `--test-concurrency=1` (build-based files share `dist/`); Playwright `AX12`. Verification: `npm run test:unit` → **5 passed**; `npx playwright test` → **96 passed** (32 × 3).
- Phase 2 (decision gates): publish 21 `review` weapons; replace fabricated landing stats (2 847 / 113 / 47).
- Log: `.kilo/plans/1790008000000-seo-content-execution-log.md`.

### Recent Activity
- User decisions: Metrika/Webvisor **untouched** (compliance risk remains); dead JS **removed**.
- Negative test: reverting one widget made AX11 fail (`window.__xss` set), proving the test is not vacuous.
- Skills updated to drop references to deleted JS (`web-developer`, `site-designer`).
- Committed `789755c` and pushed to GitHub + GitVerse; deployed via `site/deploy.ps1`; verified `https://antimanager.pro/` → 200 with all new security headers.
- Deploy note: final optional Caddy-reload SSH step hit a transient timeout; the site/headers are live, no impact.
- F16.3 diagnosed (debug session) — **upstream Kilo 7.7.5 bug, content-independent**. On every write under `.kilo/command|agent/**` the app appends `<config_validation>ERROR … Failed to parse frontmatter: No context found for instance</config_validation>` to the tool result. Mechanism (from `kilo.exe` bundle): validator `I(P)` fires only when the parent dir is `command(s)`/`agent(s)`/`mode(s)`; it then reads `s9.current` → `GfD()` → `Jo.use()` where `Jo = LocalContext("instance")` (AsyncLocalStorage). Run outside the scope that provides the instance context, `Jo.use()` throws `NotFound("instance")`, which is caught and wrapped as `Failed to parse frontmatter`. The write itself succeeds (`Wrote file successfully` precedes the block), and the real loader works (`book-editor`/`vault-auditor` are registered in the `Task` list). Secondary upstream defect: `trusted` = `path.isAbsolute(P) && path.posix.isAbsolute(P)` → `false` for Windows paths. No local fix; cosmetic noise only.
- Content readiness audit (this session): scanned all 30 numbered vault articles with a 12-point rubric. All 22 site articles are structurally **READY** (11–12/12; only «case» heading missing on 00,07,10,15,17,18,20,21, and one heading-level jump on 22); `23_Коммуникационный_конструктор` is NEEDS-EDIT (no frontmatter/cross-links); appendices 30–35 are DRAFT (questionnaires, 32/33 have no headings; 31 has a 1991-word monolithic block). Publication is blocked by the `review`/`book/draft` frontmatter, not by missing content.
- New harness: skill `article-readiness` + command `/article-readiness` + `.kilo/scripts/article_readiness.py` (objective screen → `.kilo/reports/article-readiness.md`, self-ignored); linked from `book-writing` and the `book-editor` agent. Note: `.env` is cp1251 (script decodes it), not UTF-8.

### Manual / deferred
- [ ] **GitVerse token** in `.git/config` `origin.pushurl` (plaintext) — user must rotate + switch to credential helper/SSH. HIGH priority.
- [ ] Metrika `webvisor:true` vs `/privacy/` wording — deferred by user.

### Review findings — resolved (follow-up session)
- [x] `site/build.js:483` — weapon-page zone badge now uses `zoneBadgeHtml(w.zone)`.
- [x] `site/build.js:523` — `canonicalUrl` now uses `escapeHtml(w.slug)`.
- [x] `site/build.js:36-39` — build-time escaping now has automated regression tests:
  `site/src/lib/escape.js` + `site/unit/escape.test.js` (unit) and
  `site/unit/build-escape.test.js` (integration, `WEAPONS_FILE` seam, falsifiability-checked).
- [x] Slug validation (`assertSlug`) closes the traversal path via the output dir.
- [ ] Accepted residual risk: `content_body` is raw HTML (malicious PR to `src/content/*.html`);
  mitigate via PR review/branch protection.
- [x] PNG og-image generated (`site/scripts/render-og.js`, `npm run render:og`); build now prefers `/og-image.png`.
- [ ] COSMETIC: JSON-LD pre-escaped; `escHtml` duplication; nginx header duplication.
- Verification: `node build.js` exit 0; `npm run test:unit` → 5 passed; Playwright → 96 passed.

### SEO review fixes (applied)
Source: `/review uncommitted` 2026-09-21 (report-only). All changes remain uncommitted.
- [x] **IMPORTANT** plural helper added (`build.js` `plural()`); landing meta now `plural(scenarios.length, 'контур','контура','контуров')` + `plural(weapons.length, 'глава','главы','глав')` → «4 контура, 22 главы».
- [x] COSMETIC `build.js` — dropped the second `.slice(0, 4)` in the related-weapons map.
- [x] COSMETIC `render-og.js` — temp file write moved inside `try`; `finally` guards `browser`/`tmp` existence (no leak if `chromium.launch()` throws).
- [x] COSMETIC `unit/build-seo.test.js` — dropped the brittle `!sitemap.includes('2026-07-28')` assertion (positive check remains).
- [x] COSMETIC `build.js` — `og:image:width/height` only emitted for the built-in card; suppressed when `opts.ogImage` is overridden.
- [ ] **PENDING COMMIT** `site/src/templates/og-image.png` + `site/scripts/` are **untracked** (verified not gitignored) — must be committed together, else a fresh clone's build silently falls back to `/og-image.svg`.
- [ ] DEFERRED `build.js:11` — `VERSION` static while `BUILD_DATE` dynamic; review says couple on next release.
- Verification after fixes: `npm run test:unit` → **5 passed**; `npx playwright test` → **96 passed**; `node build.js` exit 0.

### Open Questions / Follow-ups
- [ ] SEO plan Phase 2 — publish 21 `review` weapons? Replace fabricated landing stats?
- [ ] `chapters.json` / `tools.json` — unreferenced dead data (remove or wire up).
- [ ] `yandex-verification` meta + placeholder file — needs the user's code.
- [ ] Next content update for the site?
