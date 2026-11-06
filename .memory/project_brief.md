# AntiManager — Project Brief
> Updated: 2026-11-05

## Overview
Интерактивная книга-сайт для руководителей производства. Бруталистский редизайн (v2): Black+Red+White, карта звёзд (статичный data-driven SVG), каталог `/weapons/` и библиотека лонгридов `/articles/`.

🌐 [antimanager.pro](https://antimanager.pro)

## Stack
- **Site**: vanilla HTML/CSS/JS, Node.js build.js (static site generator)
- **Fonts**: Golos Text, PT Serif, JetBrains Mono (self-hosted woff2)
- **Deploy**: nginx behind Caddy, cache-busting `?v=`, deploy.ps1
- **Analytics**: Yandex Metrika (id: 111010335)
- **Feedback**: Python stdlib microservice (`site/feedback/`) behind a same-origin nginx proxy
- **Tooling**: Python 3.14 + `ftfy`, `python-docx`, `openpyxl`, `pytest`; Pandoc 3.13 for DOCX
- **Hosts**: workspace `C:\Work\Python`; vault `C:\Work\Personal Vault`
- **Tests**: unit (Node) + Playwright in `site/unit/` + `site/tests/`; run `cd site; npm test` (counts grow per feature — read them from the run output)

## Structure
- `site/` — website (css/, deploy/, fonts/, js/, src/, unit/, tests/, feedback/, build.js, package.json)
- `.kilo/` — commands, plans, reports, scripts (generators + linters), skills (no dedicated agents — `book-writing` skill covers editing)
- `manifesto-ru.md`, `manifesto-en.md` — manifestos

## Constraints
- No numbering in UI (articles not chapters)
- No sidebar, no glassmorphism, no old fonts (Inter/Manrope)
- Static by default: the only server-side piece is the feedback microservice
