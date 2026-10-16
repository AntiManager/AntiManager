# AntiManager — Active Context
> Updated: 2026-10-16 · **PARKED.** Harness quality + built-in agent-mode optimization committed (plan `1792179538920`, phases 1–5). RESUME: editorial DRAFT series 30–35.

## Current task
- **Plan `1792179538920` — complete & committed.** Boot-trio compaction (≤ caps), drift-proofing, global-harness consistency, built-in-mode matrix, hygiene + review fixes. Log: `.kilo/plans/1792179538920-execution-log.md`.

## RESUME (next session — first action)
Editorial DRAFT series **30–35** (JDR-аудит/экспресс/middle/plant-manager, сборник тестов, концепция НЦ/НС): frontmatter + related + case/conclusion, then `/full/` (`content-publisher` + `/full-article <slug>`).

## Open COSMETIC (product)
- «Штаб»/club framing on `/headquarters/` + landing hq-section still describes a community, though the entry point is the bot.
- hero-CTA «Заказать проработку» → `#offer`, not a Telegram link.
- `README.md` contour table sums 22 while weapons=23 (article 23 unplaced) — decide its contour.

## Harness / hot rules
- Skills 8, commands 10, agents 2; MCP 2 project + 1 global. `/check-site` = `npm test`.
- **`/check-harness` = global script** `~/.config/kilo/scripts/check_harness.py` (counts/manifest + orphan `/command`/agent/mode refs; excludes built-ins; accepts any config dir) — currently **0 problems**.
- Plans policy (`.kilo/AGENTS.md`): `.kilo/plans/` gitignored; 3 tracked plans are history — don't touch.
- **SSH 2222 flaky:** `deploy.ps1` may abort on a mid-run ssh timeout though the upload landed — verify the live site (GET 200) before retrying.
- Two-pass PDF: `build → render:pdf → build → render:pdf → build`; every render rewrites `/CreationDate` → `git checkout -- site/materials`.
- `yandex-verification` meta needs the user's code.
- Tech debt (Metrika `webvisor` vs `/privacy/`, GitVerse token rotation, dead `chapters.json`/`tools.json`) → `progress.md` §Technical Debt.
- Full session history → `.memory/archive/`; completed-session detail → `progress.md`.
