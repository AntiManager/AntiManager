---
name: web-developer
description: Developing the antimanager.pro site — vanilla HTML/CSS/JS, design system, performance
---

# Skill: web-developer

## Technologies

- Vanilla HTML/CSS/JS — no frameworks or bundlers
- Static generation: `node site/build.js` → `site/dist/`
- CSS Custom Properties (design tokens) in `site/css/brutalist.css`
- CSS Grid / Flexbox, `@media`; container queries are not used in the current CSS
- No external JS libraries are connected. The only mention of `mermaid` is a tool entry in `site/src/data/tools.json` (the tools catalog), not a library

## Design system (`site/css/brutalist.css`)

```css
:root {
  --color-bg: #0A0A0A;
  --color-text: #FFFFFF;
  --color-accent: #DC2626;
  --color-accent-dark: #991B1B;
  --color-steel: #6B7280;
  --color-warning: #EAB308;
  --font-heading: 'Golos Text', sans-serif;
  --font-body: 'PT Serif', Georgia, serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

The single source of tokens is `brutalist.css`. All pages use these variables; new colors — only via variables, do not duplicate values.

## Fonts

- `Golos Text` (headings, 700–900 variable), `PT Serif` (body: 400 / 400 italic / 700), `JetBrains Mono` (mono, 400)
- Self-hosted woff2 in `site/fonts/`; loading — `site/css/fonts.css` (`font-display: swap`, separate `unicode-range` for Cyrillic and Latin)

## Structure

```
site/
  build.js            # generator: src/ → dist/
  css/brutalist.css   # design system
  css/fonts.css        # @font-face
  fonts/              # woff2 (Cyrillic/Latin)
  js/brutalist.js     # shared script (defer)
  js/common.js        # shared utilities
  js/map.js           # dynamic star map
  js/interactive/     # JS widgets
  src/templates/      # base.html + og-image.svg
  src/components/     # header.html, footer.html
  src/data/           # chapters/weapons/cases/scenarios/thinkers/tools .json
  src/content/        # XX-slug.html — chapter content
  tests/              # Playwright (ux-critical.spec.js)
  deploy.ps1          # deploy to VPS
```

## Page template

Source file is `site/src/templates/base.html` — a skeleton with placeholders `{{title}}`, `{{description}}`, `{{version}}`, `{{head_extra}}`, `{{header}}`, `{{content}}`, `{{footer}}`, `{{scripts}}`. The common script is connected as `/js/brutalist.js?v={{version}}` with `defer`.

## URLs

Clean URLs (`dist/<path>/index.html`):

- `/` — landing
- `/weapons/<slug>/` — article (e.g. `/weapons/antikrizis/`)
- `/manifesto/`, `/archive/`, `/scenarios/`, `/cases/`, `/hq/`, `/about/`

Domain: https://antimanager.pro

## Interactive widgets

- One question per screen, progress bar
- «Назад» (Back) button (allow rethinking), step counter
- Result — a profile/recommendation, not a score
- JS does not block the flow

## Performance

- Fonts self-hosted, `font-display: swap`, separate `unicode-range` (see `fonts.css`)
- Explicit width/height for images and containers (CLS)
- Lighthouse target: Performance / Accessibility / SEO ≥ 90

## Responsiveness and accessibility

- Semantic markup, aria attributes, `:focus-visible`
- Skip-link, `@media (prefers-reduced-motion: reduce)`
- Hamburger menu at ≤768px (`.menu-toggle` + `.header-nav.open`)
