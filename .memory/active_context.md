# AntiManager — Active Context
> Updated: 2026-10-13 · «Геном завода» live + SEO-хардening built & tested (robots/JSON-LD/breadcrumb/og/h1/.md) — готово к деплою

## Done this session — «Геном завода» live + SEO
- Pages `/genome/` (landing + free PLAN sample + 6 doc cards) and `/genome/role/` (full КУ + recruiter profile) — indexable, sitemap (0.7/0.6), nav «Геном». First deploy `0d87762` → `verify-deploy.ps1` **3/3 OK**.
- Partials `site/src/content/genome/{landing,role}.html`; role KU/profile filled offline by `.kilo/scripts/genome_doc_build.py` (idempotent, 43 tables) — build stays vault-independent.
- **SEO audit + fixes (built & tested):** `robots: index, follow, max-image-preview:large, max-snippet:-1` on indexable pages; JSON-LD `Organization` added to the static `@graph` (dangling `publisher` fixed site-wide); `/genome/role/` breadcrumb 2→3 уровней; `og:image:alt` без дубля бренда; `<h1>` без склейки (`Геном завода`); битая `.md`-ссылка → plain text (генератор нейтрализует `.md`/relative-ссылки); `<title>` лендинга усилен. Tests unit **9/9**, Playwright **120/120**.
- Cleanup: removed `docs/prototype/` (backup `%TEMP%\kilo\backups`); compacted `.memory`; harness clean.

**Open COSMETIC (продуктовое, не баг):** hero-CTA «Заказать проработку» ведёт на `#offer`, а не прямо в Telegram.

## Next editorial (resume) — DRAFT series 30–35
JDR-аудит/экспресс/middle/plant-manager, сборник тестов, концепция развития НЦ/НС — each needs frontmatter + related sections + case/conclusion before `/full/`. Procedure: `content-publisher` skill + `/full-article <slug>`.
- Tests: unit **9/9**; Playwright **120/120** (40 × 3) — `cd site; npm test`. Docker holds port 3000 → if Playwright `webServer` aborts, use a temp config on another port.
- Two-pass PDF rule: `build → render:pdf → build → render:pdf → build`; each render rewrites `/CreationDate` → `git checkout -- site/materials` restores untouched PDFs.

## Harness state
- Skills 8, commands 10, agents 2. MCP: obsidian+github (project `.kilo/kilo.json`), context7 (global). `/check-harness` clean: global 7/7/9, project 8/2/10, 0 orphans. `/check-site` = `npm test`.

## Hot rules / deferred
- Plans policy (`.kilo/AGENTS.md`): `.kilo/plans/` gitignored; the 3 tracked plans are history — do not touch.
- **SSH 2222 flaky (VPS):** `deploy.ps1` may abort on a mid-run ssh timeout although the upload landed — verify live (GET 200) before re-running.
- `yandex-verification` meta needs the user's code.
- Open tech debt (Metrika `webvisor` vs `/privacy/`, GitVerse token rotation, `chapters.json`/`tools.json` dead data, `VERSION`/`BUILD_DATE`, raw `content_body`) → `.memory/progress.md` §Technical Debt.
- Full history → `.memory/archive/`; completed-session detail → `.memory/progress.md`.
