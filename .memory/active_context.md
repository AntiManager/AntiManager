# AntiManager — Active Context
> Updated: 2026-10-13 · **PARKED до 2026-10-14** · «Геном завода» + SEO-хардening live & verified (commit `241092e`)

## Session done — «Геном завода» live + SEO-хардening
- `/genome/` (landing + PLAN sample + 6 doc cards) и `/genome/role/` (КУ + recruiter profile) — индекс, sitemap 0.7/0.6, nav «Геном». Deploy `0d87762`, затем SEO `241092e` → `verify-deploy.ps1` **3/3 OK** (live 200).
- Role KU/profile — offline `.kilo/scripts/genome_doc_build.py` (idempotent, 43 tables); build stays vault-independent.
- SEO: `robots index, follow, max-image-preview:large, max-snippet:-1`; JSON-LD `Organization` в static `@graph` (висячий `publisher` устранён); role breadcrumb 3 уровня; `og:image:alt` без дубля бренда; `<h1>` без склейки; битая `.md`-ссылка → plain text (генератор нейтрализует `.md`/rel-ссылки); `<title>` лендинга усилен. Unit **9/9**, Playwright **120/120**.
- Cleanup: `docs/prototype/` удалён (backup `%TEMP%\kilo\backups`); memory compacted; harness clean (global 7/7/9, project 8/2/10, 0 orphans).

## RESUME (2026-10-14)
- **Editorial:** DRAFT series **30–35** (JDR-аудит/экспресс/middle/plant-manager, сборник тестов, концепция НЦ/НС) — frontmatter + related + case/conclusion, затем `/full/` (`content-publisher` + `/full-article <slug>`).
- **Open COSMETIC** (продуктовое): hero-CTA «Заказать проработку» → `#offer`, не прямой Telegram.
- Tests: unit **9/9**; Playwright **120/120** (40×3) — `cd site; npm test`. Docker держит порт 3000 → при abort `webServer` — временный config на другом порту.
- Two-pass PDF: `build → render:pdf → build → render:pdf → build`; render переписывает `/CreationDate` → `git checkout -- site/materials`.

## Harness / hot rules
- Skills 8, commands 10, agents 2. MCP: obsidian+github (project), context7 (global). `/check-site` = `npm test`.
- Plans policy (`.kilo/AGENTS.md`): `.kilo/plans/` gitignored; 3 tracked plans — history, не трогать.
- **SSH 2222 flaky:** `deploy.ps1` может упасть на mid-run ssh timeout, хотя upload прошёл — проверить живой сайт (GET 200) перед повтором.
- `yandex-verification` meta нужен код пользователя.
- Tech debt (Metrika `webvisor` vs `/privacy/`, GitVerse token rotation, dead `chapters.json`/`tools.json`, `VERSION`/`BUILD_DATE`, raw `content_body`) → `.memory/progress.md` §Technical Debt.
- Full history → `.memory/archive/`; completed-session detail → `.memory/progress.md`.
