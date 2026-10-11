# AntiManager — Progress
> Updated: 2026-10-11

## Done

- **Site (2026-08…09):** brutalist rebuild v2 (Black+Red+White, 32 pages, static SVG star map); SEO (OG/canonical/structured data/sitemap) + SEO Phase 1 technical (dynamic `BUILD_DATE`, featured cards, related-links fallback, raster `og-image`); a11y/UX + cache-busting; repo restructured to `site/` + manifestos at root.
- **Security hardening (2026-09):** output escaping in `build.js` (`site/src/lib/escape.js`, `assertSlug`), DOM-XSS fixed in widgets (04/16/19), nginx security headers, secrets → `.env`. Suite grew 84 → 99 (33 × 3).
- **Content-readiness harness:** skill `article-readiness` + `/article-readiness` + `.kilo/scripts/article_readiness.py` (report in gitignored `.kilo/reports/`); vault audit of 30 articles.
- **Two-tier theme pages:** `/weapons/<slug>/` (interactive) + `/weapons/<slug>/full/` (full text + `.materials-section`); `{{read_more}}` placeholder; reusable `.kilo/scripts/md_to_partial.py`; `scripts/render-pdf.js` (`npm run render:pdf`). Fake site-wide `download-section` removed.
- **Publish-readiness full cycle, article-by-article:** **00, 02–21** done (01 has no weapon entry — its full text is `/manifesto/`). Each: vault Layer 2 + site sync + `/full/` + PDF + tests + deploy. **19 «Цифровой двойник»** (two-part), **20 «Выученная беспомощность»** and **21 «Два типа управления»** are live-verified deployed — 19's SSH block cleared, the whole-`dist/` deploy shipped them. 20: `{{read_more}}` landing with the Пролог hook hoisted above the audience section so the auto-lede is a strong standfirst. 21: vault restructured to the norm (title block `---` + «Ключевые идеи за 1 минуту»; nested list flattened) so the Пролог survives conversion. unit 8/8, e2e 99/99. **Per-article detail → `.memory/archive/progress-history-2026.md`.**
- **Process-library refactor (plan 1791721561689):** Phase 0 specs + engine (`.kilo/process-engine/`) + T1.1 split `Proc_lib.md` → vault `Библиотека процессов\library\` (regression gate PASS; engine tests 11/11).

## Planned
- Process-library refactor: T1.2 normalize hierarchy per group (`LIBRARY→GROUP→PROCESS→SUBPROCESS`) + goal per PROCESS/SUBPROCESS; then T1.3 APQC crosswalk, T1.4 seams, T1.5 freeze subprocess-level v1.
- Roll `/full/` out article-by-article as vault readiness allows (00 pilot, 02–21 done; 01 has no weapon entry — its full text is `/manifesto/`).
- Then article **22 «Ударить по траектории»** (`review` in vault) — restructure the top to the norm first (title block not separated by `---`), fix the heading jump, then Layer 2 pass + site sync; continue for the remaining `review` chapters.
- Publish per-article extras (checklists/templates) into `site/materials/<slug>/` + `materials.json`.
- SEO plan Phase 2 (decision): publish 21 `review` weapons; replace fabricated landing stats.

## Technical Debt
- **GitVerse token** embedded in `.git/config` `origin.pushurl` (plaintext credential) — rotate + move to credential helper/SSH. Not a repo file.
- **F16.3 (diagnosed, closed as upstream/cosmetic)** — `config_validation ERROR: Failed to parse frontmatter: No context found for instance` on writes under `.kilo/command|agent/**` is an **upstream Kilo 7.7.5 bug**, content-independent: the write-path validation helper reads the `instance` `LocalContext` (AsyncLocalStorage, `Jo`) outside the scope that provides it, so `GfD()` throws `NotFound("instance")`. The write still succeeds; commands/agents load normally. Secondary upstream defect: `trusted` uses `path.isAbsolute(P) && path.posix.isAbsolute(P)` → `false` for Windows paths. No local fix.
- Metrika `webvisor:true` vs `/privacy/` claim — deferred by user (compliance risk remains).
