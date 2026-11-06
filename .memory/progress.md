# AntiManager — Progress
> Updated: 2026-11-06 · Full pre-compaction log → `.memory/archive/progress-history-2026-10-24.md`

Rolling log, recent first. Keep this file under 8 KB; move older entries to `.memory/archive/`.

## Done

- **Release B/C deployed (2026-11-06, S12, uncommitted tree).** Live is VERSION `20261106d`, deployed after a fresh `npm test` gate (unit 43/43, Playwright 384 = 378 passed / 6 skipped, `check-links` 85 pages 0/0/0/0). The first `deploy.ps1` run copied `dist` and both nginx files but timed out on the SSH 2222 restart hop; the port recovered on the next probe, `antimanager-web` was recreated and Caddy reloaded. Evidence: `verify-deploy.ps1` 8/8 pages 200, 15/15 single-hop 301, IndexNow 82 URLs HTTP 200.
- **Site IA refactor CLOSED (2026-11-06, S11, plan `1793969494727`, plan+log archived).** Conversion audit per phase: 12 converted, 1 partial (12.1 hero copy and 12.3 named author/experience are user-owned). `/session-audit`: 17 sessions, 9/11 implementation sessions validated after the last code edit (10/11 any validation), $4.13, 0 secrets, 0 dangerous commands, median context peak 160.6k. Doc drift repaired (`site/AGENTS.md` `/playbook/` + retired HQ CTA + series name, `.kilo/AGENTS.md` canonical routes/no active plan, `.kilo/harness.md` gate baselines, `.memory/system_patterns.md` route map). `task-conversion` gained the rename-sweep rule; global `HARNESS.md` updated. Final gate on a fresh build: unit 43/43, `npm test` 378 passed / 6 skipped, `check-links` 85 pages 0/0/0/0, `check:redirects` no drift, Pagefind 82 indexed / 15,946 words. No commit (not requested); tree uncommitted.
- **Release C (2026-11-06, S10, uncommitted, partial):** 12.2 CTA hierarchy (`data-cta` on header/hero/next-step/offer, outline secondary), 12.4 offer clarity («Что получаете / Как идёт работа / Следующий шаг», no invented prices or timelines), 12.5 free lead magnet (40-criterion XLSX + PLAN sample, no email gate) on home and `/method/#offer`, 12.6 `site/js/analytics.js` Metrika goals (`search_open`, `search_query`, `search_result_click`, `cta_click`, `download`, `scroll_75`, `outbound_telegram`) + Telegram UTM with `am:*` events from `search.js`, 12.3 `/about/` «Как мы работаем». 12.1 hero copy and the named author stay user-owned. `VERSION` → `20261106d`. Evidence: unit 43/43, analytics 9/9, `npm test` 378/6 skipped, check-links 85 pages 0/0/0/0.
- **Release B (2026-11-06, S9, uncommitted):** 7.3 prev/next on chapter landing + full in catalog id order; 7.4 cross-type related derived from the catalog (chapters add «Связанные материалы», articles add «Из плейбука и методологии»); 9.3 origins cards have 2–3 destinations; 11.6 `@axe-core/playwright` + `tests/a11y.spec.js` (6 pages × 3 viewports, critical only); 11.7 `nextStepBand` on content pages and hubs. `VERSION` → `20261106c`. Evidence: unit 42/42, axe 18/18, `npm test` 369/6 skipped.
- **Release A deployed (2026-11-06, S8).** Live from the uncommitted S1–S7.5 tree (no commit). Pre-deploy `npm test` 351/6 skipped, `nginx -t` OK on both confs, dist secret scan clean. SSH 2222 timed out on the restart hop after the copy succeeded; container recreated once the port reopened. Caddy admin API refused `localhost:2019` (non-fatal). IndexNow 82 URLs 200. `verify-deploy.ps1` fixed: `/start/` probe → `start-page`; 3xx probing switched to `HttpClient` (PS 7.6 `Invoke-WebRequest -MaximumRedirection 0` is fatal under `$ErrorActionPreference=Stop`). Result: 8/8 pages 200, 15/15 single-hop 301, sitemap 82 URLs (0 `/book/`, `/cases`, HQ, `/search/`). Report `.kilo/reports/deploy-2026-11-06.md`.
- **S7.5 pre-deploy review + rename (2026-11-06):** «Плейбук» + `/playbook/` 301; series «Имитация развития»; compact series list; H1 mid-word breaks fixed; `/about/headquarters/` retired → `/contact/`; `/about/` «Кто пишет» + «Личный опыт»; `/method/` option A (H1 «Методология производственной системы», «Геном завода» = model name); SEO title/description budgets. Report `.kilo/reports/pre-deploy-review-2026-11-06.md`.
- **S1–S7 site IA (2026-11-06):** routes cutover + 301 map, header/footer, `/start/`, `/book/` facets, `/method/` hub + `/about/`, six-section home, Pagefind + `/search/`, a11y P0 + `check:links`. Details → archived execution log and `.memory/archive/progress-history-2026-11-06.md`.
- **Work stream closed (2026-11-06):** Yandex.Webmaster confirmed; remaining queue (Линейные системы, process-library continuation, PS-audit blind scoring, DRAFT 30–35, token rotation) closed by user decision.
- **Methodology suite published locally (2026-10-26)** → `.memory/archive/progress-history-2026-10-24.md`.
- **Harness rollout (2026-10-24)** → `.memory/archive/progress-history-2026-10-24.md`.
- Earlier 2026-10-20/21/22 entries (SEO diagnostics, IndexNow deploy, systems map, PS-audit, vault split, articles 53–55) → `.memory/archive/progress-history-2026-10-24.md`.

## Planned

- **No active plan.** User-owned and still open: `/start/` editorial approval, `/about/` named-author/experience block (12.3), 12.1 hero value proposition, Metrika goal names (12.6).
- Process-library refactor (plan `1791721561689`): Phase 1 frozen (20/79/238/999); additive `PRJ` → 21/83/259/1041; Phase 2 stopped at T2.6 tranche 1. **Paused 2026-11-06 by user decision — not resumed**; resume point stays in the plan's execution log.
- **Cancelled 2026-11-06:** DRAFT series 30–35 (JDR audit/express/middle/plant-manager, test collection, NC/NS development concept).
- Publish per-article extras into `site/materials/<slug>/` + `materials.json`.
- SEO Phase 2 DONE (`410d706`); deferred CSP `script-src`/`default-src` and Metrika `webvisor`/`/privacy/` wording.

## Technical Debt

- **Accepted risks (2026-11-06, no rotation planned):** GitVerse token in `.git/config` `origin.pushurl`, VPS SSH key, Metrika `webvisor:true` vs `/privacy/`.
- **GitVerse token** in `.git/config` `origin.pushurl` (plaintext) — rotate + move to credential helper/SSH. Not a repo file.
- **F16.3** — `Failed to parse frontmatter: No context found for instance` on `.kilo/command|agent/**` writes is an upstream Kilo 7.7.5 bug (content-independent; write succeeds). No local fix.
- Metrika `webvisor:true` vs `/privacy/` claim — deferred by user (compliance risk).
