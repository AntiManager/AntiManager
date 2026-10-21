# AntiManager — Active Context
> Updated: 2026-10-21 · PS express audit published at `/genome/audit/`; no active plan.

## State
- **PS express audit (`/genome/audit/`):** generated from vault v3.0 by `.kilo/scripts/gen_ps_audit_page.py` (7 markers) + fillable XLSX `materials/ps-express-audit/express-audit-ps.xlsx`; entry from `/genome/` and footer; `pack=audit` in both PACK_LABELS copies. Vault note is now `status: published`.
- **PS-audit (vault `Аудит ПС/`, outside git):** full 120-criteria checklist + express v3.0 (40 criteria, strict subset, rows identical to base) + index. Linter `check_ps_audit.py` → 0/0.
- **Articles:** 40, 41, 50–55 published; unit 16/16, Playwright 192/192, PDF 31; Release C live `?v=20261019c`.
- **Git:** Release A–C + docs cleanup pushed 2026-10-21. Uncommitted: `check_ps_audit.py`, `.kilo/AGENTS.md`, `.memory` — commit on request.

## Next
1. PS-audit: human blind-scoring of 5 criteria; publish only via a separate plan.
2. Editorial: DRAFT series 30–35 before `/full/`.
3. Process-library (`1791721561689`): Phase 2 T2.6 tranche 2 — `MFG-02/03`, then `MFG-04/05`.
4. Content extras: `site/materials/<slug>/` + `materials.json`.

## Open cosmetic
- «Штаб»/club framing; hero CTA → `#offer`; README contours 22 vs weapons 23.

## Hot rules
- Skills 8 / commands 10 / agents 2; `/check-site` = `npm test`.
- Obsidian MCP writes on Cyrillic paths are broken — use `Write`/`Edit` + Python (`.kilo/AGENTS.md` §7).
- Data SSOT: `articles.json` + topics + series; only `published` renders; tests derive from data.
- Every article `.md` needs title block + `---`; no Mermaid — tables/lists.
- `render:pdf` two-pass; deploy may time out on Caddy reload — verify live.
- History → `.memory/archive/`.
