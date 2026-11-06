# AntiManager — System Patterns
> Updated: 2026-11-06

## Design System
- **Name**: Brutalist (Black+Red+White)
- **CSS**: `brutalist.css`
- **Motto**: «Система не врёт, человек — да»

## Content Architecture
- Book chapters (`weapons.json` + `chapters.json`, joined/asserted by `src/lib/catalog.js`) → `/playbook/`
- Situations: each chapter belongs to `crisis` / `team` / `changes` / `system` (scenarios.json)
- Articles: vault Markdown → HTML partials via `.kilo/scripts/gen_article_partials.py` (offline);
  `build.js` only reads the generated partials, so re-run the generator after every vault edit
- Article archive: `articles.json` drives URLs/order/status, `article-topics.json` the hubs,
  `article-series.json` the cross-topic series; only `published` entries render
- Generator precondition: the converter drops everything through the first `---` after the
  frontmatter, so every article needs a title block followed by `---`
- No numbering: articles are standalone, not chapters

## URL Structure (source of truth: `site/src/routes.js`)
- `/` — landing
- `/playbook/` — chapter catalog with situation filter; `/playbook/<slug>/` interactive, `/playbook/<slug>/full/` full text + materials
- `/start/` — four situations with anchors (`#crisis`, `#team`, `#changes`, `#system`)
- `/articles/`, `/articles/<topic>/`, `/articles/<topic>/<slug>/`
- `/method/`, `/method/audit/`, `/method/systems/`, `/method/documents/`, `/method/documents/<slug>/`, `/method/role/`
- `/about/`, `/about/manifesto/`, `/about/origins/`, `/contact/`, `/privacy/`, `/search/`, `/404/`
- Legacy URLs → single 301: `/weapons/` → `/playbook/`, `/genome/` → `/method/`, `/arsenal/` → `/playbook/`,
  `/book/` → `/playbook/`, `/scenarios/` → `/start/`, `/manifesto/` → `/about/manifesto/`,
  `/archive/` → `/about/origins/`, `/about/headquarters/` → `/contact/`, `/headquarters/` → `/contact/`,
  `/cases/` → `/`. Map: `site/deploy/redirects.conf`
  (generated, `npm run check:redirects`). `/strategy/...` → `/articles/strategy/...` stays nginx-only.

## Encoding Rules (source of truth: pipelines/common/guard_encoding.py)
- Все Markdown-файлы (manifesto, статьи, content): UTF-8 без BOM
- `build.js`: Node.js, UTF-8 по умолчанию — но проверять вывод (HTML-файлы должны быть UTF-8)
- `weapons.json`: UTF-8 (кириллические названия оружия/зон)
- PowerShell-скрипты: `Out-File -Encoding UTF8` при записи HTML/MD
- Git: `i18n.commitEncoding = utf-8`

## Cache Strategy
- Static assets: `?v=` query param for cache busting
- Nginx: immutable for hashed assets, must-revalidate for HTML
