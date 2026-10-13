# AntiManager — Active Context
> Updated: 2026-10-13 · status: **deployed** («Геном завода» → `/genome/` + `/genome/role/` live & verified; plan `1791902606513` closed)

## Done this session — «Геном завода» live (plan `1791902606513`)
Prototype → production, **deployed + verified live**:
- Pages `/genome/` (landing + free PLAN-group sample + 6 doc cards) and `/genome/role/` (full КУ + recruiter profile) — indexable, sitemap (0.7/0.6), nav «Геном».
- Partials `site/src/content/genome/{landing,role}.html`; role KU/profile filled offline by `.kilo/scripts/genome_doc_build.py` (idempotent, 43 tables) — build stays vault-independent.
- `build.js` renders both, `VERSION` `20261013a`; styles `brutalist.css` §GENOME; CTAs → `t.me/antimanager`. Tests unit **9/9**, Playwright **120/120** (fixed mobile hscroll via `overflow-wrap:anywhere`).
- Deploy `0d87762` → `deploy.ps1` → `verify-deploy.ps1` **3/3 OK**; plan + log archived.
- Cleanup (2026-10-13): removed `docs/prototype/` (backup in `%TEMP%\kilo\backups`); compacted `.memory`; harness clean.

**Deferred review fixes (`0d87762`, COSMETIC):** (1) `landing.html` h1 `Геном<br>завода` → «Геномзавода» (a11y/SEO) — add space/`aria-label`; (2) JSON-LD breadcrumb `/genome/role/` flat (2 levels) → extend to 3; (3) hero-CTA «Заказать проработку» → `#offer` vs direct Telegram; (4) hardcoded `#141414`/`#1b1b1b` in §GENOME → `--color-surface`.

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
