# AntiManager — Progress
> Updated: 2026-10-24 · Full pre-compaction log → `.memory/archive/progress-history-2026-10-24.md`

Rolling log, recent first. Keep this file under 8 KB; move older entries to `.memory/archive/`.

## Done

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
- **S14 + audit block 7 + PRJ (2026-10-21):** 14th system «Управление портфелем проектов и изменений»; `PRJ.md` 4/21/42; 132 criteria; cards rewritten; checker + negative tests; evidence clean.
- **PS express audit page (2026-10-21):** `/genome/audit/` from vault express v3.0 (40 rows, 6 blocks), fillable XLSX, generator `--check`; unit 17/17, feedback 25/25, audit+UX Playwright 120/120.
- **Boot-trio compaction (2026-10-21):** progress 14.6 → 8.0 KB, active_context 5.5 → 1.5 KB; archives updated; harness 7/7/9 and project 8/10/2, 0 problems.
- **PS-audit express v3.0 (2026-10-21):** 40 base criteria copied verbatim; removed cross-cutting rows/weights/system dimension; checker extended; 0 errors; backups.
- **PS-audit neutralization + derived express (2026-10-21):** 120-criterion client-neutral base, 40-criterion express; linter `check_ps_audit.py` 0/0; MCP move/create rolled back on Cyrillic paths → Write + Python; lesson folded into `.kilo/AGENTS.md`.
- **Docs/plans/harness cleanup + commit (2026-10-21):** archived completed plans; fixed README/`site/AGENTS.md`/`.kilo/AGENTS.md` drift; harness 0 problems; committed/pushed.
- **Articles 53–55 (2026-10-20):** three digital articles published, fact-check reports, unit 16/16, Playwright 192/192, PDF 31, live 200s.
- Earlier sessions → `.memory/archive/progress-history-2026.md` and `progress-history-2026-10-24.md`.

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
