# AntiManager — Progress
> Updated: 2026-10-12

## Done

- **Harness cleanup + optimization (2026-10-12):** audited both harnesses (no orphan refs; global 7/7/9, project 8/2/10); compacted the auto-loaded memory trio losslessly — `active_context` 16.7→2.5 KB, `progress` 11.4→4.1 KB (caps 3/8 KB), history appended to `.memory/archive/` (+ new `active_context-2026-10.md`); dropped the dead `web-search` MCP from `.kilo/kilo.json` + `.kilo/kilo.json.example` and updated `.kilo/AGENTS.md`. Commits `497095e` (proc-library phases B–C) + `80f0ac1` (harness); pushed GitHub + GitVerse.
- **Artifact chain (plan 1791810263662) — Phase C (priority matrix) DONE (2026-10-12):** `specs/T4.2-priority-matrix.md` (repo + vault mirror, byte-identical `57F5F7EF…`) plus the unified `library/artifacts/Приоритеты_руководителей.md` — 10 role sections `ГД, РП, ГИ, ГТ, РК, РС, ГМ, HR, НЦ, НС`, 201 rows. Rule-based derivation via the new versioned `pipelines/proc-library/author_priority_matrix.py`: §10/§11 (action roles) dropped; §6 ПЭО→ГД, §13 ИПП→РП, §12 РПС→ГТ (section dropped, rows re-anchored and deduped on `(quadrant, task)`); §5 ОТК→РК; §8 Мастер→НС; code-less rows dropped (H7); case-aware de-identification; `ГИ`/`РС` authored from the library (INF/ENV/EMG/HRP; SL_LOG/PLAN-03/HRP/ORG). **`check_artifacts.py` `OK`; `--semantic` no W3/W4/W5; token scan identity 0; pytest 110 passed; guard OK.** Lessons folded: a role-heading display name must itself be paren-free beyond its code (else H1a); a bare token-swap breaks RU grammar → phrase+case substitutions; drop the whole `(…%…)` group. Log `.kilo/plans/1791810263662-…-execution-log.md` §"Phase C — priority matrix". Next: sub-plan 04 (Phase D, event grid).
- **Artifact chain (plan 1791810263662) — Phase B (КТК) DONE (2026-10-12):** `specs/T4.1` (+ vault mirror) + 10 unified `library/artifacts/КТК/<CODE>_КТК.md`; rule-based (`roles_for_string` + aggregated library `Критичность`); `ГИ` authored from `INF`+`ENV`, `РС` from `SL_*`; folds `ИПП`→РП and `ПЭО`→ГД/РП. **`check_artifacts.py` `OK`; `--semantic` no W4/W5; token scan 0; pytest 110.** Lessons → `specs/T4.9` §3, `specs/T4.1` §3.
- **Artifact chain — Phase A foundations DONE + reviewed (2026-10-12):** 10-role register (`specs/T4.0` + `role_registry.json`), machine-readable format contract `specs/T4.9`, RU register `Роли.md`, `check_artifacts.py` (+ tests). `/review` + fixes (fold/event maps wired, H6 `ориентир` money, `parse_library` prunes `artifacts/`). Suite 38 passed / 72 skipped.
- **Pipelines consolidation + proc-library vendoring (2026-10-12):** all tooling under `pipelines/` (`common/`, `obsidian-to-site/`, `proc-library/`); engine versioned in-repo, generated artifacts ignored, specs mirrored; vault path env-driven (`PROC_LIB_VAULT`). Boot trio auto-loaded only. `main` pushed (GitHub + GitVerse).
- **Process library final verification + de-client-ification (2026-10-12):** `engine.py` VALID (20/79/238/1121; 0 errors / 0 warnings); `token_scan` identity 0; idempotent `unify_library.py` removed client refs/tokens and normalised 396 role strings.
- Older sessions (SEO & a11y hardening + deploy, site v2, security hardening, content-readiness harness, two-tier theme pages, publish-readiness 00/02–23, proc-lib Phase 1 freeze) → `.memory/archive/progress-history-2026.md`.

## Planned
- Process-library refactor: Phase 1 **frozen**. Next **Phase 2** — operations + flow graph, pilot **Planning** (`PLAN` + `SL_PLAN`).
- Artifact chain: next **Phase D** (event grid, `specs/T4.3`), then E (conformance), F (closeout/INDEX).
- Next editorial: the DRAFT series **30–35** (JDR-аудит/экспресс/middle/plant-manager, сборник тестов, концепция развития НЦ/НС) — each needs frontmatter + related sections + case/conclusion before `/full/`.
- Publish per-article extras into `site/materials/<slug>/` + `materials.json`.
- SEO Phase 2 — DONE (`410d706`); only CSP `script-src`/`default-src` and the Metrika `webvisor`/`/privacy/` wording deferred.

## Technical Debt
- **GitVerse token** in `.git/config` `origin.pushurl` (plaintext) — rotate + move to credential helper/SSH. Not a repo file.
- **F16.3** — `Failed to parse frontmatter: No context found for instance` on `.kilo/command|agent/**` writes is an **upstream Kilo 7.7.5 bug** (content-independent; write succeeds). No local fix.
- Metrika `webvisor:true` vs `/privacy/` claim — deferred by user (compliance risk).
