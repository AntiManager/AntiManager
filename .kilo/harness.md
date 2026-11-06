# Harness provenance — AntiManager

> Written by `/harness-init` 2026-11-05; updated when the harness changes. Not autoloaded.

## Composition

- Archetype: `content-site` (Obsidian vault → static site → VPS)
- Patterns: `HP-001, HP-002, HP-003, HP-005, HP-007, HP-008, HP-009, HP-011, HP-012, HP-014, HP-015, HP-016`
- Decisions followed: `ADR 0001, ADR 0003, ADR 0005`
- Initialized: `2026-11-05`

## Layout

- Tracked config: root `kilo.json` (model, 4-file autoload, permissions).
- Local config: `.kilo/kilo.json` (gitignored) adds the `obsidian` MCP and
  `external_directory` for the vault; deep-merged over the root file.
- Instructions: `.kilo/AGENTS.md` (not root) — vault/site map, skills, commands, scripts.
- Skills: 8 under `.kilo/skills/`; commands: 10 under `.kilo/command/`; agents: 0.

## Verify

- Command: `powershell -NoProfile -File "$env:USERPROFILE\.config\kilo\scripts\verify_repo.ps1" AntiManager`
- Success: `STATUS: OK`, exit 0
- Scope: git state, remotes, harness files, encoding (names only for `.env`)
- Not covered: site tests, vault generators, live deploy — run the full gate below
- Full gate (2026-11-06 S11 baseline):
  - `cd site; npm run build; npm run test:unit` → unit 43 pass
  - `cd site; npx playwright test` → 378 passed / 6 skipped (3 projects)
  - `cd site; npm run check:links` → 85 pages, 0 duplicate ids / heading skips / broken links / anchors
  - `cd site; npm run check:redirects` → `redirects.conf: no drift`
  - `python .kilo/scripts/check_documents.py --vault "<vault>"` → 0 findings
  - `python .kilo/scripts/gen_documents_pages.py --check`, `gen_ps_audit_page.py --check`,
    `gen_systems_page.py --check` → exit 0 (missing vault → exit 2)
  - `.\site\deploy.ps1`, then `.\site\scripts\verify-deploy.ps1` → live checks pass (301 matrix)

## Known exceptions

| Finding | Why accepted | Review by |
|---|---|---|
| `verify_repo.ps1` reports `TESTS: skipped` | site tests need `site/node_modules` + Playwright Chromium; run as the full gate | 2026-12-05 |
| Vault outside the repo | content SSOT is the user's Obsidian vault; generators/checkers take `--vault` | 2026-12-05 |
| `.kilo/kilo.json` untracked | local MCP/external paths; template is `.kilo/kilo.json.example` | 2026-12-05 |
| `npm run render:pdf` binary churn | PDF metadata differs per run; render only after content changes | 2026-12-05 |
| Obsidian MCP writes on Cyrillic paths | journal stores UTF-8→cp1251 mojibake; use Write/Edit + Python | 2026-12-05 |
