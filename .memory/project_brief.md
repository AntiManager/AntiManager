# AntiManager — Project Brief
> Updated: 2026-10-16

## Overview
Интерактивная книга-сайт для руководителей производства. Бруталистский редизайн (v2): Black+Red+White, карта звёзд (статичный data-driven SVG), 32 страницы.

🌐 [antimanager.pro](https://antimanager.pro)

## Stack
- **Site**: vanilla HTML/CSS/JS, Node.js build.js (static site generator)
- **Fonts**: Golos Text, PT Serif, JetBrains Mono (self-hosted woff2)
- **Deploy**: nginx, cache-busting `?v=`, deploy.ps1
- **Analytics**: Yandex Metrika (id: 111010335)
- **Tests**: unit (Node) + Playwright in `site/unit/` + `site/tests/`; run `cd site; npm test` (counts grow per feature — read them from the run output)

## Structure
- `site/` — website (css/, deploy/, fonts/, js/, src/, build.js, package.json)
- `.kilo/` — agents (book-editor, vault-auditor), commands (fix-encoding, link-ideas, new-article, etc.), plans, scripts, skills
- `manifesto-ru.md`, `manifesto-en.md` — manifestos

## Constraints
- No numbering in UI (articles not chapters)
- No sidebar, no glassmorphism, no old fonts (Inter/Manrope)
- Content-driven static site, no backend
