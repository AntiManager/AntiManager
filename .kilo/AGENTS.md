# AntiManager — Agent Instructions

> Auto-loaded by Kilo. Keep ≤60 lines. Detail lives in `.kilo/harness.md` and `.memory/`.

## What this repo is

Static brutalist playbook site (`site/`, Node `build.js`, vanilla HTML/CSS/JS) generated from an
Obsidian vault outside the repo; Python generators in `.kilo/scripts/` publish `/method/` and
`/articles/`. Deploys to a VPS (nginx behind Caddy): antimanager.pro.

- Vault map: `Roadmap/Дорожная карта доработок.md`; documents: `Методология ПС/Типовые документы/`.
- Plans: `.kilo/plans/` is gitignored and local; tracked plans are history — do not touch;
  completed plans → `.kilo/plans/archive/`; do not modify `.gitignore`.
- Ambiguous multi-session work gets a SPEC first (`/spec`); a one-file fix with an obvious test skips it.

## Commands

| Job | Command | Success |
|---|---|---|
| site gate | `cd site; npm test` | 0 failed (counts from output) |
| site build only | `cd site; npm run build` | site + Pagefind index written |
| links / routes | `cd site; npm run check:links; npm run check:redirects` | 0 broken / no drift |
| harness lint | `python -X utf8 ..\harness-playbook\scripts\harness_lint.py --repo AntiManager` | `total findings: 0` |
| repo verify | `pwsh -NoProfile -File "$env:USERPROFILE\.config\kilo\scripts\verify_repo.ps1" -Repo "C:\Work\Python\AntiManager"` | `STATUS: OK` |
| closeout | `/closeout` | gate passes, memory written once |

Full gate, generators, deploy verification: `.kilo/harness.md` §Verify.

## Rules that must always hold

- Never commit `.env*`, tokens or personal data; deploy only from a committed tree; record live
  `VERSION` ↔ SHA in `.memory`.
- Cyrillic content changes go through `Write`/`Edit` or Python (`ftfy`), never PowerShell; back up
  to `$env:TEMP\kilo\backups\` first and run the encoding guard.
- Obsidian MCP writes/moves on Cyrillic paths are broken (journal mojibake) — MCP for reads only.
- One file → verify → commit; no bulk applies. Destructive commands are ask-guarded in `kilo.json`.
- `/playbook/` is canonical; legacy URLs 301; `/cases/` retired. Data SSOT is `articles.json` +
  topics + series; only `published` renders; no Mermaid.
- Generator `--check` regions are regenerated, never hand-edited; restore untouched PDFs with
  `git checkout -- site/materials`.

## Delegation

- Delegate mechanical sweeps, vault-wide `rg` reports, bulk reads/summaries and DOCX/PDF
  regeneration to `cheap-worker`; require a compact summary, not raw output.
- Do not delegate Cyrillic vault writes, editorial/design decisions, deploy, permissions changes,
  or anything needing visual validation.

## Closeout and memory

- `/closeout`: matching gate → artifact check → one full-file `Write` per memory file → stop; it
  never commits.
- `.memory/active_context.md` ≤3 KB, `.memory/progress.md` ≤8 KB; older details → `.memory/archive/`.

## Where to look

- Harness provenance, verify gate, new-machine setup, known exceptions: `.kilo/harness.md`.
- Site IA, language policy, scripts, publication rules, security protocol: `.kilo/harness.md`.
- Skills: `.kilo/skills/` (8, load on demand); commands: `.kilo/command/` (11).
