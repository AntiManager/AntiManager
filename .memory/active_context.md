# AntiManager — Active Context
> Updated: 2026-11-05 · Mini-PC migration verified; previous snapshot → `.memory/archive/active_context-2026-10-24.md`

## State

- **Mini-PC migration + readiness (2026-11-05):** restored repo, vault, harness, `.env` and SSH key; fixed all stale host paths. Evidence: build OK; unit 25/25; Playwright 231/231; feedback 26/26; proc 47 passed; checkers 0; no drift; IndexNow 84; live verify-deploy 6/6.
- **A3 regulation (2026-11-04, `3160f92`):** `Методология ПС/Типовые документы/Форма-А3.md` + site page `/genome/documents/a3-reshenie-problem/` (PDF, DOCX, hub card); `.run/a3_*` scratch builders.
- **Methodology suite (2026-10-26):** `/genome/documents/` (4 docs) + article 56.
- **SEO:** verification meta, IndexNow, `practice` topic + articles 60–64; GSC/Webmaster pending.
- **Methodology:** 14 system cards (12 fields), full checklist 132/7 (v1.1), express 40 (blocks 1–6), project model; canonical **ТПР**.
- **Process library:** 21 groups / 83 processes / 259 subprocesses / 1041 operations; only known `PRJ-*` dangling links remain; checkers 0/0, artifacts OK.
- **Articles:** 42 vault notes; published 40, 41, 50–56, 60–64; materials under `site/materials/`.
- **Линейные системы:** ООО + ИП Санников (ROSCA); base 60. Next: 100–150 companies, 10 SKU benchmark, 10 calls.
- **Git:** `main` = `3160f92`; `origin/main` = `gitverse/main`; `origin` pushes to GitHub + GitVerse.

## Next

1. Register in Yandex.Webmaster/GSC; set `YANDEX_VERIFICATION`/`GOOGLE_VERIFICATION`; redeploy, submit sitemap.
2. Линейные системы: enrich base, top-30, 10 calls; ROSCA positioning (ICP A/B/E, offer, proof, objections, landing, KPI).
3. Process library: `PRJ` flow links → T2.6 tranche 2 (`MFG-02/03`) → `MFG-04/05`.
4. PS-audit: human blind-scoring of 5 criteria; publish via separate plan.
5. Editorial: DRAFT series 30–35 before `/full/`.
6. After content changes: `.\site\deploy.ps1`, then `.\site\scripts\verify-deploy.ps1`.
7. Security: rotate tokens exposed by the public Yandex mirror + regenerate the VPS SSH key.

## Hot rules

- **Paths:** workspace `C:\Work\Python`; vault `C:\Work\Personal Vault` (no `D:`).
- **Toolchain:** Python 3.14 + `ftfy python-docx openpyxl pytest`; Pandoc 3.13; `cd site; npm ci; npx playwright install chromium`.
- Skills 8 / commands 10 / agents 0; `/check-site` = `npm test`.
- Generators default to the vault; override with `--vault`; `check_system_cards.py` takes it positionally.
- Obsidian MCP writes on Cyrillic paths are broken — use `Write`/`Edit` + Python.
- `check_artifacts.py` takes the **library root**, not the vault root.
- Data SSOT: `articles.json` + topics + series; only `published` renders.
- Every article `.md`: title block + `---`; no Mermaid.
- `render:pdf` two-pass; deploy may time out on Caddy reload — verify live.
- History → `.memory/archive/`.
