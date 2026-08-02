# AntiManager — System Patterns
> Updated: 2026-08-02

## Design System
- **Name**: Brutalist (Black+Red+White)
- **CSS**: `brutalist.css`
- **Motto**: «Система не врёт, человек — да»

## Content Architecture
- Weapons catalog (`weapons.json` → dynamic star map)
- Zones: each weapon belongs to a zone (production management areas)
- Articles: Markdown → HTML via build.js
- No numbering: articles are standalone, not chapters

## URL Structure
- Root: landing page
- `/arsenal` — weapons catalog with zone filter
- `/[weapon-slug]` — individual article
- `/archive`, `/scenarios`, `/cases`, `/hq`, `/about`, `/manifesto`, `/404`

## Encoding Rules (CONSTITUTION.md §0.1)
- Все Markdown-файлы (manifesto, статьи, content): UTF-8 без BOM
- `build.js`: Node.js, UTF-8 по умолчанию — но проверять вывод (HTML-файлы должны быть UTF-8)
- `weapons.json`: UTF-8 (кириллические названия оружия/зон)
- PowerShell-скрипты: `Out-File -Encoding UTF8` при записи HTML/MD
- Git: `i18n.commitEncoding = utf-8`

## Cache Strategy
- Static assets: `?v=` query param for cache busting
- Nginx: immutable for hashed assets, must-revalidate for HTML
