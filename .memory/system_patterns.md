# AntiManager — System Patterns
> Updated: 2026-10-19

## Design System
- **Name**: Brutalist (Black+Red+White)
- **CSS**: `brutalist.css`
- **Motto**: «Система не врёт, человек — да»

## Content Architecture
- Weapons catalog (`weapons.json` → dynamic star map)
- Zones: each weapon belongs to a zone (production management areas)
- Articles: vault Markdown → HTML partials via `.kilo/scripts/gen_article_partials.py` (offline);
  `build.js` only reads the generated partials, so re-run the generator after every vault edit
- Article archive: `articles.json` drives URLs/order/status, `article-topics.json` the hubs,
  `article-series.json` the cross-topic series; only `published` entries render
- Generator precondition: the converter drops everything through the first `---` after the
  frontmatter, so every article needs a title block followed by `---`
- No numbering: articles are standalone, not chapters

## URL Structure
- `/` — landing
- `/weapons/` — weapons catalog with zone filter (`/arsenal/` also resolves)
- `/weapons/<slug>/` — article (interactive) + `/weapons/<slug>/full/` (full text + materials)
- `/genome/`, `/genome/role/`, `/articles/`, `/articles/<topic>/`, `/articles/<topic>/<slug>/`, `/contact/`
- `/strategy/...` → 301 → `/articles/strategy/...` (nginx; legacy route)
- `/archive/`, `/scenarios/`, `/cases/`, `/headquarters/`, `/about/`, `/manifesto/`, `/privacy/`, `/404`

## Encoding Rules (source of truth: pipelines/common/guard_encoding.py)
- Все Markdown-файлы (manifesto, статьи, content): UTF-8 без BOM
- `build.js`: Node.js, UTF-8 по умолчанию — но проверять вывод (HTML-файлы должны быть UTF-8)
- `weapons.json`: UTF-8 (кириллические названия оружия/зон)
- PowerShell-скрипты: `Out-File -Encoding UTF8` при записи HTML/MD
- Git: `i18n.commitEncoding = utf-8`

## Cache Strategy
- Static assets: `?v=` query param for cache busting
- Nginx: immutable for hashed assets, must-revalidate for HTML
