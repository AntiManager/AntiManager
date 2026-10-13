# AntiManager — Active Context
> Updated: 2026-10-13 · status: **in progress** (prototype ported to the site build — `/genome/` + `/genome/role/`; RESUME: controlled deploy + live verify)

## In progress — «Геном завода» section integrated (RESUME = deploy + live verify)
Prototype → production section, now part of the static build (plan `1791902606513`):
- **Pages:** `/genome/` (landing: model + free PLAN-group sample + 6 doc cards) and `/genome/role/` (full КУ package + recruiter profile). Both indexable, in sitemap (0.7 / 0.6) and nav («Геном»).
- **Content:** authored partials `site/src/content/genome/{landing,role}.html`. The role page's KU/profile block is generated offline by `.kilo/scripts/genome_doc_build.py` (ported from the prototype `_build-doc.py`, idempotent, fills `<!--KU:*-->` / `<!--PROFILE:*-->` markers from the vault) — **build stays vault-independent**.
- **Wiring:** `site/build.js` writes both pages (`renderPage` + static BreadcrumbList), `VERSION` bumped `20261013a`; styles in `brutalist.css` §GENOME; CTAs → `https://t.me/antimanager`, one → `/headquarters/`.
- **Tests:** `site/unit/build-genome.test.js` (unit **9/9**), `site/tests/genome.spec.js` + no-hscroll paths (Playwright **120/120**). Fixed a mobile/tablet overflow (`.anchor-code` nowrap → wraps).
- **Deploy control:** `site/scripts/verify-deploy.ps1` (post-deploy GET 200 + sitemap check). Full detail → `.memory/progress.md` (2026-10-13 entry).

**RESUME (next session):** controlled deploy — commit the integration (rollback point), `cd site; .\deploy.ps1`, then `.\scripts\verify-deploy.ps1` + browser spot-check. SSH 2222 flaky → verify live before re-running. Then close the plan (`/retro`, fold a lesson). Optional cleanup: `docs/prototype/` is now redundant (still untracked) — remove after verify (user-confirmed).


## Next editorial (resume) — DRAFT series 30–35
JDR-аудит/экспресс/middle/plant-manager, сборник тестов, концепция развития НЦ/НС — each needs frontmatter + related sections + case/conclusion before `/full/`. Procedure: `content-publisher` skill + `/full-article <slug>`.
- Tests: unit **9/9**; Playwright **120/120** (40 × 3) — `cd site; npm test`. Docker Desktop holds port 3000 → if Playwright `webServer` aborts, use a temp config on another port.
- Two-pass PDF rule: `build → render:pdf → build → render:pdf → build`; each render rewrites `/CreationDate` → `git checkout -- site/materials` restores untouched PDFs.

## Harness state
- Skills 8, commands 10, agents 2. MCP: obsidian, github (project `.kilo/kilo.json`), context7 (global `kilo.jsonc`). `/check-harness` clean: global 7/7/9, project 8/2/10, 0 real orphans.
- `content-publisher` + `/full-article`; `article-readiness` + `/article-readiness`; `pipelines/obsidian-to-site/{article_readiness,md_to_partial}.py`; `/check-site` = `npm test`.

## Hot rules / deferred
- Plans policy (`.kilo/AGENTS.md`): `.kilo/plans/` is gitignored; the 3 tracked plans (`site-development-plan.md`, `antimanager-repo-restructure.md`, `1784652237510-site-brutalist-rebuild.md`) are history — do not touch.
- **SSH 2222 flaky (VPS):** `deploy.ps1` may abort on a mid-run ssh timeout although the upload landed — verify live (GET 200) before re-running.
- `yandex-verification` meta needs the user's code.
- Open tech debt (Metrika `webvisor` vs `/privacy/`, GitVerse token rotation, `chapters.json`/`tools.json` dead data, `VERSION`/`BUILD_DATE`, raw `content_body`) → `.memory/progress.md` §Technical Debt.
- Full history → `.memory/archive/`; completed-session detail → `.memory/progress.md`.
