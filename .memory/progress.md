# AntiManager — Progress
> Updated: 2026-11-05 · Full pre-compaction log → `.memory/archive/progress-history-2026-10-24.md`

Rolling log, recent first. Keep this file under 8 KB; move older entries to `.memory/archive/`.

## Done

- **Mini-PC migration + readiness (2026-11-05):** restored the repo, vault, harness, `.env` secrets and SSH key from the 2026-10-29 handover. Fixed every stale host path: `.env` vault paths, four `.kilo/scripts` `DEFAULT_VAULT`s, 18 `pipelines/proc-library` files, `.kilo/kilo.json.example`, `.run/a3_build.py`, workspace `evals/tasks/*.json`. Reinstalled Node deps + Playwright Chromium, Pandoc 3.13 and Python `ftfy/python-docx/openpyxl/pytest`. Evidence: build OK, unit 25/25, Playwright 231/231, feedback 26/26, proc 47 passed/72 skipped, all document checkers 0, generators no drift, IndexNow dry-run 84 URLs, live `verify-deploy.ps1` 6/6, VPS SSH/SCP/docker/nginx OK. Moved transient caches and migration scratch out of the workspace.
- **A3 regulation published (2026-11-04, `3160f92`):** unified `Форма-А3.md` in `Методология ПС/Типовые документы/` assembled from edition 3 (`Archive/Исходники А3/`); site page `/genome/documents/a3-reshenie-problem/` with TOC, PDF, DOCX and hub card; `.run/a3_*` builders retained as scratch.
- **Methodology suite published locally (2026-10-26):** four vault notes moved from the vault root into `Методология ПС/Типовые документы/` (ритм совещаний v2.0, Gemba-обход v1.0, СНУ-регламент v2.0 — internal) + new public `СНУ-концепт-бриф`; article 56 moved to `Книга/01_Статьи/56_Ритм_управления.md`. Content pass per plan: metadata/separators, SQDCP↔SQDCPME mapping, filled level-1 charter, 95% vs 80–94% reconciliation, named benchmarks removed, duplicated schema removed. New site section `/genome/documents/` + 3 pages with static TOC, PDF and DOCX; new `documents.json`, `gen_documents_pages.py`, `check_documents.py`; article 56 in `management` with 4 FAQ and interlinks; `documents` contact pack in `contact.js` + `feedback/server.py`. Evidence: `check_documents.py` 0 errors, generator `--check` no drift, unit 25/25, feedback 26/26, Playwright 231/231, 40 PDFs rendered. Deployed `?v=20261026a`; IndexNow 83 URLs (HTTP 200); `verify-deploy.ps1` 6/6; feedback container redeployed with the `documents` pack.
- **Harness rollout (2026-10-24):** `.kilo/AGENTS.md` wired into `instructions` (`HARNESS_LOADED`); local `.kilo/kilo.json` restored with obsidian MCP v2 (`connected`); GitHub MCP not restored (use `gh`/`GH_TOKEN`); `.kilo/kilo.json.example` and MCP map aligned; memory compacted to caps (active 2.85 KB, progress 6.0 KB; full snapshots archived). Global harness installed at `~/.config/kilo/`.
- **SEO package deployed (2026-10-22):** `npm test` unit 22/22 + Playwright 228/228; `deploy.ps1`; container `antimanager-web` restarted; final `caddy reload` hit SSH timeout. `$ErrorActionPreference="Stop"` aborted the script before IndexNow, so ran `npm run indexnow` manually → 78 URLs, HTTP 202. `verify-deploy.ps1` 6/6; live 7/7 practice pages 200, sitemap 78, `?v=20261022a`, footer link. **Lesson:** optional `caddy reload` can abort deploy and skip IndexNow; verify "Deploy complete", else `cd site; npm run indexnow`.
- **SEO diagnostics + tech package (2026-10-22):** disproved the third-party report (sitemap 200, robots correct, Timeweb `5.129.221.85`, Googlebot 27 requests/17 URLs, YandexBot 0). Real cause: no Webmaster/GSC registration. Added verification meta via env, IndexNow key + deploy hook, shortened 2 titles >70, expanded 8 descriptions to 125–154 chars, build warnings for title >70 / description >200. New `practice` topic + 5 articles (ids 60–64). Review fixes applied. Unit 22/22, Playwright 228/228, 0 replacement chars/BOM.
- **Линейные системы: product knowledge base (2026-10-22):** four vault notes — assortment architecture (19 groups, segments A–G), distribution catalog (17 groups), ROSCA production (families, envelope, process, pricing, gaps), positioning/marketing (4 platforms, 3 offers A/B/E, evidence matrix, channels, benchmark, KPI), plus marketing audit. Contradictions flagged (rolling vs turning, 6 vs 8 years, 6 vs 7 m, two prices, seller IP); segment drift A–E vs A–G. Index and next-session note updated.
- **Owner meeting kit + client `.docx` (2026-10-21):** landscape A4 docx for forms and express audit; 63 owner questions / 7 blocks / 17 ★; meeting plan and summary template; `КАБЭКС.md` provenance updated. Evidence: 40/40 criteria, 6/6 forms, 0 BOM/replacement chars.
- **Client set cleaned for КАБЭКС (2026-10-21):** forms doc 31,155 → 23,572 B; removed preamble/provenance/internal paths; added client express audit 54,990 B with 40 criteria; provenance recorded.
- **Vault split (2026-10-21):** moved universal methodology (`Методология ПС/`) vs client docs (`Заказчики/КАБЭКС/`); 5 notes relocated; wikilinks verified by basename; generators/checkers updated; SHA-256 match; backup `%TEMP%\kilo\backups\20261021-171100_vault-split`.
- **Systems map (2026-10-21):** `/genome/systems/` page with 14 cards × 12 fields, summary, blank template; owner `.md/.docx`; generator `gen_systems_page.py --check` = no drift; unit 18/18, Playwright 210/210; deployed, `a0d06a3`.
- **Terminology «ворота» → ТПР (2026-10-21):** 98 occurrences / 17 vault files; glossary defines `ТПР (точка принятия решения, decision gate)`; English `Gate/DecisionPoint` kept in ontology; checkers 0.
- **Card correction + project model (2026-10-21):** project types/classes moved to `Проектная-модель.md`; appendices A–D removed from cards; S14 13th field removed; filled artifact examples; `check_system_cards.py` extended; 0 errors.

- Earlier 2026-10-20/21 entries (systems map, PS-audit, vault split, articles 53–55) → `.memory/archive/progress-history-2026-10-24.md`.

## Planned

- Articles library (plan `1792404697747`): complete — Releases A/B/C deployed and committed.
- Process-library refactor (plan `1791721561689`): Phase 1 frozen (20/79/238/999); additive `PRJ` → 21/83/259/1041. Phase 2 in progress — Planning pilot (`PLAN`+`SL_PLAN`) done (T2.1–T2.6 tranche 1). Next: `PRJ` flow links, then T2.6 tranche 2 (`MFG-02/03`), then `MFG-04/05`; then MFG flow links → economics → roll-up.
- Next editorial: DRAFT series 30–35 (JDR audit/express/middle/plant-manager, test collection, NC/NS development concept) — frontmatter + related + case/conclusion before `/full/`.
- Publish per-article extras into `site/materials/<slug>/` + `materials.json`.
- SEO Phase 2 DONE (`410d706`); deferred CSP `script-src`/`default-src` and Metrika `webvisor`/`/privacy/` wording.

## Technical Debt

- **GitVerse token** in `.git/config` `origin.pushurl` (plaintext) — rotate + move to credential helper/SSH. Not a repo file.
- **F16.3** — `Failed to parse frontmatter: No context found for instance` on `.kilo/command|agent/**` writes is an upstream Kilo 7.7.5 bug (content-independent; write succeeds). No local fix.
- Metrika `webvisor:true` vs `/privacy/` claim — deferred by user (compliance risk).
