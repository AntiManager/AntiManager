# AntiManager — Active Context
> Updated: 2026-10-13 · status: **parked** (resume with Phase E, conformance)

## Current track — artifact chain (plan 1791810263662)
Phases A–D DONE (КТК, priority matrix, event grid). Next: **sub-plan 05 (Phase E,
conformance validation)** — `specs/T4.8`; run `check_artifacts.py <vault> --cross
--semantic`; review W1 (5, КТК keystones absent from matrix/grid), W2 (21,
meeting-convener vs process-owner — signed off in log), W6; traceability gaps 0;
then F (closeout/INDEX). Log: `.kilo/plans/1791810263662-…-execution-log.md`.
- Tooling: `pipelines/proc-library/` (`check_artifacts.py`, `token_scan.py`,
  `author_*.py` incl. `author_event_grid.py`, `engine.py`); vault path env-driven
  (`PROC_LIB_VAULT`).

## Session 6 (2026-10-13) — deferred list DONE
(1) Phase D review fixes F1–F6 (T4.3 mirror `4167 043A`; pytest 115); (2) archived
completed plans/reports → `.kilo/plans/archive/` (18) + `.kilo/reports/archive/` (10);
harness map verified consistent (skills 8 / commands 10 / agents 2 / MCP 3); (3) commit
`5085d3f` pushed to **GitHub + GitVerse**. **Next: Phase E** (sub-plan 05, conformance
validation) — resume from the checkpoint below; do not start it in session 6.

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
