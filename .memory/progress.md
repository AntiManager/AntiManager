# AntiManager — Progress
> Updated: 2026-09-21

## Done
- [x] Brutalist rebuild v2: Black+Red+White, 32 pages, star map (static SVG)
- [x] SEO: OG, canonical, structured data, favicon, sitemap
- [x] UX fixes: A11y, hamburger menu, scroll-top, mobile grids, hover guards
- [x] Cache-busting `?v=`, nginx hardening, permission fix
- [x] Playwright tests: 84 (28 × 3 viewports)
- [x] Secrets extracted to .env, sensitive data scrubbed
- [x] Repo restructured: site/ + manifestos root
- [x] Harness audit & optimization cascade (C1–C5): docs/config repaired, skills rewritten to fact, portable config, harness map, E2E made hermetic (66/66). Log + retrospective in `.kilo/plans/1790002457744-*`.
- [x] Follow-up QA: AX08 mobile-nav, AX09 arsenal zone-filter, AX10 system-map presence added; suite 84/84. Committed + pushed.

## Planned
None on this laptop.

## Technical Debt
- F16.3 — `config_validation ERROR` on writing `.kilo/command|agent/*.md` (environment/validator, not content).
- F16.8 — `.kilo/scripts/add-fm-00.py` hardcoded absolute user path (portability).
- Dead code unreferenced by the build: `site/js/map.js`, `site/js/common.js`, `site/js/interactive/*`. Star map is static (`build.js starSvg()`); either wire interactivity or remove.
