# AntiManager — Active Context
> Updated: 2026-10-21 · **Plan `1792404697747` complete: Releases A, B and C deployed and committed.** No active plan.

## Current state
- **Articles library.** `/articles/` hub → topic hub → article page. Topics live: `strategy`, `economics`, `management`, `digital`. Articles 40, 41, 50–55 published; series «Управление способностью» has 6 members. Release C: 53 «Цифровизация 1.0», 54 «Цифровизация 2.0», 55 «ИИ-зоопарк» — readiness 12/12, 12/12, 11/12; `?v=20261019c`; unit **16/16**, Playwright **192/192**; PDF **31**; live 200/301/sitemap/PDF checks green.
- Deploy hit the known optional Caddy-reload SSH :2222 timeout after the container restart; live verified instead.

## Next (in priority order)
1. **Editorial:** DRAFT series 30–35 (JDR-аудит/экспресс/middle/plant-manager, сборник тестов, концепция развития НЦ/НС) — frontmatter + related sections + case/conclusion before `/full/`.
2. **Process-library** (plan `1791721561689`): Phase 2, T2.6 tranche 2 — convert `MFG-02/03`, then `MFG-04/05`; then MFG flow links → economics → roll-up (`author_operations.py` + `mfg_operations.json`).
3. **Content extras:** publish per-article extras into `site/materials/<slug>/` + `materials.json`.

## Next session (user agenda, 2026-10-20)
- **PS-audit docs (done this session):** `Экспресс-чек-лист-аудита-ПС.md`, `Карточки-систем.md`, `Приложение-формы-артефактов.md` written to the Personal Vault root (outside git). Plan `1792500184362` executed. Validated: 40 criteria, 13 systems × 12 fields, exact T4.9 headers, 20 groups, 0 forbidden tokens, UTF-8 clean. Review fixes applied (S01 artifact numbering, S02 boundaries wording, system double-count disclosed, artifact↔form mapping).
- **Docs/plans/harness cleanup (done 2026-10-21):** archived completed local plans (`1792179538920`, `1792500184362`, `articles-library-brief`), fixed README structure/commands and `site/AGENTS.md` drift (`unit/`, `feedback/`, date sources), added the plan-archive convention + scripts map to `.kilo/AGENTS.md`; harness checker `EXIT=0`.

## Open COSMETIC (product)
- «Штаб»/club framing on `/headquarters/` + landing hq-section still describes a community, though the entry point is the bot.
- hero-CTA «Заказать проработку» → `#offer`, not a Telegram link.
- `README.md` contour table sums 22 while weapons=23 (article 23 unplaced).

## Harness / hot rules
- **Working tree:** Release A+B+C and the docs/plans cleanup were **committed and pushed on 2026-10-21** after an explicit user request. Vault edits (40/41/50–55) live outside git.
- Skills 8, commands 10, agents 2; MCP 2 project + 1 global. `/check-site` = `npm test`.
- Single source of truth: `articles.json` + `article-topics.json` + `article-series.json`; `strategy.json` is gone.
- Only `status: published` renders; empty topic hubs are suppressed. Tests derive article/topic/sitemap expectations from data — do not re-freeze lists.
- **Generator precondition:** `md_to_partial.convert` drops everything through the first `---` after the frontmatter — every article needs a title block followed by `---`.
- **No Mermaid renderer.** The converter has no code-fence support, so diagrams must be tables/lists; a fenced block leaks as paragraph text.
- `render:pdf` reads `articles.json`; two-pass rule: `build → render:pdf → build → render:pdf → build`. It retries a just-written PDF 3× (Windows antivirus locks).
- **SSH 2222 flaky:** deploy may abort on the optional Caddy-reload step after the container restart — verify live before retrying.
- Test counts: unit 16, Playwright 192 (Release C baseline); counts grow with new articles (read from output).
- Full session history → `.memory/archive/`; completed-session detail → `progress.md`.
