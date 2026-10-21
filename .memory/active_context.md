# AntiManager — Active Context
> Updated: 2026-10-21 · systems map deployed; next session: harness/docs/plans cleanup + commit/push.

## State
- **Methodology set (vault, outside git):** 14 system cards (all 12 fields, S14 no longer carries a 13th field) + full checklist 132 criteria / 7 blocks (`version: "1.1"`) + express 40 (unchanged, blocks 1–6 only) + diagnostics doc with 14 systems. Cards use base ids `1.1–6.18` / `7.1–7.12`; FPY, COQ, KPI-passport, master data are marked «вне полного чек-листа».
- **Project model (vault root):** `Проектная-модель.md` — separate detailed document (6 execution types, A–G effect classes, lifecycle/ТПР, handover/benefits, portfolio rules, 13×6 system interface). Cards only reference it; appendices A–D removed from `Карточки-систем.md`.
- **Terminology (2026-10-21):** canonical term is **ТПР / точка принятия решения** (not «ворота»); replaced across the whole vault incl. artifact codes, КТК artifacts and `PLAN-04`. Do not reintroduce «ворота» for project decision points.
- **Appendix (vault root):** `Приложение-формы-артефактов.md` now carries filled examples from library artifacts for `Ф-КТК`, `Ф-ПР`, `Ф-СРС`, `Ф-KPI`, `Ф-БП` (21 groups incl. `PRJ`), `Ф-СХ`; no empty tables.
- **Process library (vault `Библиотека процессов/`):** 21 groups / 83 processes / 259 subprocesses / 1041 operations. New `PRJ` group (4 processes, owner ГД); `T0.1` §T1.7 records the additive extension. `PRJ` has no `## Потоки (Flow Links)` table yet — next flow tranche.
- **Checkers:** `check_ps_audit.py` (132/7, pinned fingerprint of `1.1–6.18`) → 0/0; `check_system_cards.py` (14 cards, 12 fields each, ids, codes, orphans, no project appendices, S14 model reference) → 0; `check_artifacts.py` on the **library root** (`<vault>\Библиотека процессов`) → OK, 26 pre-existing warnings; `token_scan` on `library\artifacts` → 0.
- **Systems map (2026-10-21):** `/genome/systems/` published from the vault cards via `gen_systems_page.py` (14 × 12 fields, summary, blank template); owner doc `Карта-систем-собственнику.md/.docx` in the vault; template `materials/ps-systems-map/`. **Deployed 2026-10-21** (live 200 verified); not committed.
- **PS express audit (`/genome/audit/`):** untouched by this plan (express hash, generator hash, XLSX hash verified unchanged).
- **Articles:** 40, 41, 50–55 published; unit **18/18**, Playwright **210/210**, PDF 31; Release C live `?v=20261019c`.
- **Git:** Release A–C + docs cleanup pushed 2026-10-21. Uncommitted: `check_ps_audit.py` (block 7), `check_system_cards.py`, `gen_systems_page.py`, the `/genome/systems/` page + unit test + template, `.memory` — commit on request.

## Next
1. **Next session (user-requested):** harness/docs/plans cleanup + optimization, then commit + push the systems-map change set (site page, generator, owner doc, template, tests, `.memory`). Card defects are fixed; no follow-up needed unless the user brings corrections.
2. Process-library: author `PRJ` flow links (`author_*_flows.py` pattern), then Phase 2 T2.6 tranche 2 — `MFG-02/03`, then `MFG-04/05`.
3. PS-audit: human blind-scoring of 5 criteria; publish only via a separate plan.
4. Editorial: DRAFT series 30–35 before `/full/`.

## Open cosmetic
- «Штаб»/club framing; hero CTA → `#offer`; README contours 22 vs weapons 23.
- Card content defects not covered by the plan: master data is now scoped (S01 planning vs S13 registry), school of masters and crane/fire artifacts carry explicit «совместно с» marks; remaining: S03 5S target (≥4.0 monthly) and S05 6–15 min read as level 4, not 3; S11 target state still describes a gap; S02 lists 4 QUAL processes without artifacts; S06 omits `HRP-01-05/-07`.

## Hot rules
- Skills 8 / commands 10 / agents 2; `/check-site` = `npm test`.
- Obsidian MCP writes on Cyrillic paths are broken — use `Write`/`Edit` + Python (`.kilo/AGENTS.md` §7).
- `check_artifacts.py` takes the **library root**, not the vault root.
- Data SSOT: `articles.json` + topics + series; only `published` renders; tests derive from data.
- Every article `.md` needs title block + `---`; no Mermaid — tables/lists.
- `render:pdf` two-pass; deploy may time out on Caddy reload — verify live.
- History → `.memory/archive/`.
