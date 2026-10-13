# AntiManager — Active Context
> Updated: 2026-10-13 · status: **parked** (artifact chain DONE + committed; next session: editorial series 30–35)

## Last session — artifact chain close-out (DONE, committed)
Reviewed the uncommitted Phase E+F diff (`/review uncommitted`) and fixed: 1 **IMPORTANT** —
`traceability.py` printed `OK`/exit 0 on an empty/wrong vault (false «acceptance green») →
`build()` reports `artifact_files`, `main()` exits 2 when 0; 3 **COSMETIC** — `ktk_rows`→`ktk_links`,
H1b documented (checker docstring + `T4.8 §3`), docstring exit-2 narrowed. New regression test.
**pytest 119**; checker `OK`; `--cross --semantic` H\*=0 (W1×5 waived, W2×21 signed off);
traceability 171/201/45 gaps 0/0; `specs/T4.8` re-mirrored (byte-identical). Six sub-plans →
`.kilo/plans/archive/`; harness 7/7/9 + 8/2/10, `/check-harness` clean.

## Completed — artifact chain (plan 1791810263662) — DONE + committed
Phases A–F: `specs/T4.0/1/2/3/8/9`, `role_registry.json`, 10 `КТК/<КОД>_КТК.md`, `Роли.md`,
`Приоритеты_руководителей.md`, `Сетка_регулярных_событий.md` (vault `library/artifacts/` +
`library/INDEX.md`). Tooling `pipelines/proc-library/`; vault env `PROC_LIB_VAULT`.

## Next editorial (resume) — DRAFT series 30–35
JDR-аудит/экспресс/middle/plant-manager, сборник тестов, концепция развития НЦ/НС — each needs
frontmatter + related sections + case/conclusion before `/full/`. Procedure: `content-publisher`
skill + `/full-article <slug>`.
- Tests: unit **8/8**; Playwright **99/99** (33 × 3) — `cd site; npm test`. Docker Desktop holds
  port 3000 → if Playwright `webServer` aborts, use a temp config on another port.
- Two-pass PDF rule: `build → render:pdf → build → render:pdf → build`; each render rewrites
  `/CreationDate` → `git checkout -- site/materials` restores untouched PDFs.

## Harness state
- Skills 8, commands 10, agents 2. MCP: obsidian, github (project `.kilo/kilo.json`), context7 (global `kilo.jsonc`).
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
- Full history → `.memory/archive/active_context-2026-10.md`.
