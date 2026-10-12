# AntiManager — Active Context
> Updated: 2026-10-12

## Current track — artifact chain (plan 1791810263662)
Phases A–C DONE (КТК, priority matrix). Next: **sub-plan 04 (Phase D, event grid)** —
`specs/T4.3`; author `library/artifacts/Сетка_регулярных_событий.md` (11 source sections →
cadence sections, H3/H4, W2, token 0), depends on 01+02+03. Then E (conformance), F
(closeout/INDEX). Log: `.kilo/plans/1791810263662-…-execution-log.md`.
- Tooling: `pipelines/proc-library/` (`check_artifacts.py`, `token_scan.py`, `author_*.py`,
  `engine.py`); vault path is env-driven (`PROC_LIB_VAULT`).

## Next editorial (resume)
DRAFT series **30–35** (JDR-аудит/экспресс/middle/plant-manager, сборник тестов, концепция
развития НЦ/НС) — each needs frontmatter + related sections + case/conclusion before `/full/`.
Procedure is codified: `content-publisher` skill + `/full-article <slug>`.
- Tests: unit **8/8**; Playwright **99/99** (33 × 3) — `cd site; npm test`. Docker Desktop holds
  port 3000 → if Playwright `webServer` aborts, use a temp config on another port.
- Two-pass PDF rule: `build → render:pdf → build → render:pdf → build`; each render rewrites
  `/CreationDate` → `git checkout -- site/materials` restores untouched PDFs.

## Harness state
- Skills 8, commands 10 (+`/full-article`), agents 2. MCP: obsidian, github (project
  `.kilo/kilo.json`), context7 (global `kilo.jsonc`).
- `content-publisher` + `/full-article`; `article-readiness` + `/article-readiness`;
  `pipelines/obsidian-to-site/{article_readiness,md_to_partial}.py`; `/check-site` = `npm test`.

## Hot rules / deferred
- Metrika `webvisor:true` vs `/privacy/` wording — deferred (compliance risk).
- `yandex-verification` meta needs the user's code.
- GitVerse token in `.git/config` `origin.pushurl` (plaintext) — rotate + move to credential helper/SSH (HIGH).
- `chapters.json`/`tools.json` — unreferenced dead data (decide separately).
- `build.js` `VERSION` static vs dynamic `BUILD_DATE` — couple on next release.
- Residual: `content_body` is raw HTML (malicious PR risk) — rely on PR review/branch protection.
- **SSH 2222 flaky (VPS):** `deploy.ps1` may abort on a mid-run ssh timeout although the upload
  landed — verify live (GET 200) before re-running.
- SEO Phase 2: only CSP `script-src`/`default-src` deferred.
- Full history → `.memory/archive/active_context-2026-10.md`.
