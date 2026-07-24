# Plan: Brutalist Rebuild — Atomized Stories

> Для слабой модели: каждая история = 1 файл/компонент, 1 Playwright-тест, desktop + mobile.
> Запускать `npx serve site/dist` один раз в начале — все истории используют один сервер.

## Pre-flight (один раз перед Story 00)

```bash
cd site
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
New-Item -ItemType Directory -Force -Path fonts, css, js, src/templates, src/data, src/content
```

---

## Design Decisions (Clarified 2026-07-24)

| # | Decision | Rationale |
|---|----------|-----------|
| N1 | **Нумерация (00, 02, ...) — только внутренняя.** На сайте не отображается. `id` используется для имён файлов и связей в JSON, но НИКОГДА не показывается в UI. | Выглядит некрасиво. Нарушает концепцию отдельных статей. |
| N2 | **Статьи, не главы.** Каждая статья — самостоятельная единица. Никаких «Глава XX», «Часть I–VI», сквозной нумерации. | Пользователь будет добавлять статьи со временем. Это не законченная книга. |
| N3 | **Динамический подсчёт.** Везде, где упоминается количество оружий/статей, использовать `weapons.filter(w => w.status === 'published').length`. Никаких хардкодов «23 оружия». | Коллекция растёт. |
| N4 | **Зоны — по концепту пользователя.** Некоторые статьи могут быть без зоны (поле `zone: null`). Такие статьи видны только в Арсенале, не попадают в секцию «Выбери участок фронта». | Концепт назначает конкретные главы в конкретные зоны. Не все главы покрыты. |
| N5 | **Скачивание/инструменты.** Каждая статья может иметь ссылку на скачивание (PDF, чеклист). Механизм — кнопка «Скачать» внизу статьи. Пока заглушка (как текущая download-section), позже — реальные файлы. | Пользователь планирует добавлять материалы. |
| N6 | **Star map — динамическая.** SVG-карта рендерится из `weapons.json`: статьи группируются по зонам, лучи показывают количество статей в каждой зоне. Количество лучей = количество зон (сейчас 4, может вырасти). | Карта должна отражать реальное состояние коллекции, не хардкод. |
| N7 | **Исходные тексты — в vault.** Манифест, архив мыслителей, кейсы — исходные .md файлы лежат в Obsidian vault (`ARTICLES_DIR` из `.env`). В build.js они попадают как HTML-файлы в `site/src/content/` через content-publisher. Build.js читает их как и контент оружия. | Единый источник правды — vault. Сайт — публикация. |

---

## Story 00: Wipe clean — удалить старый CSS/шаблоны

**Что:** Удалить `common.css`, `fonts.css`, `print.css`, `components/`, старые `templates/`. Оставить `build.js`, `js/common.js`, `src/content/*`, `src/data/*.json` как резервные копии.

**Файлы:** удалить `site/css/common.css`, `site/css/fonts.css`, `site/css/print.css`, `site/src/components/` (папку), `site/src/templates/base.html`, `site/src/templates/chapter.html`

**Playwright-тест (после Story 00 build):**
```js
// Story 00: After wiping, a minimal build should produce at least index.html with no console errors
await page.goto('http://localhost:3000');
const errors = [];
page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
await page.waitForTimeout(1000);
if (errors.length > 0) throw new Error('Console errors: ' + errors.join(', '));
```

**Результат:** `node build.js` должен упасть (зависит от старых файлов) или выдать пустой dist. Это нормально — foundation ещё не создан.

---

## Story 01: Fonts — скачать и подключить woff2

**Что:** Скачать Golos Text (700, 900), PT Serif (400, 400i, 700), JetBrains Mono (400) с Google Fonts как woff2 в `site/fonts/`. Создать `site/css/fonts.css`.

**Файлы:** `site/fonts/GolosText-Bold.woff2`, `GolosText-Black.woff2`, `PTSerif-Regular.woff2`, `PTSerif-Italic.woff2`, `PTSerif-Bold.woff2`, `JetBrainsMono-Regular.woff2`, `site/css/fonts.css`

**fonts.css:**
```css
@font-face { font-family: 'Golos Text'; font-style: normal; font-weight: 700; font-display: swap; src: url('/fonts/GolosText-Bold.woff2') format('woff2'); }
@font-face { font-family: 'Golos Text'; font-style: normal; font-weight: 900; font-display: swap; src: url('/fonts/GolosText-Black.woff2') format('woff2'); }
@font-face { font-family: 'PT Serif'; font-style: normal; font-weight: 400; font-display: swap; src: url('/fonts/PTSerif-Regular.woff2') format('woff2'); }
@font-face { font-family: 'PT Serif'; font-style: italic; font-weight: 400; font-display: swap; src: url('/fonts/PTSerif-Italic.woff2') format('woff2'); }
@font-face { font-family: 'PT Serif'; font-style: normal; font-weight: 700; font-display: swap; src: url('/fonts/PTSerif-Bold.woff2') format('woff2'); }
@font-face { font-family: 'JetBrains Mono'; font-style: normal; font-weight: 400; font-display: swap; src: url('/fonts/JetBrainsMono-Regular.woff2') format('woff2'); }
```

**Playwright-тест:**
```js
// Story 01: Verify fonts load from woff2 files
const page = await context.newPage();
await page.goto('http://localhost:3000');
const fontRequests = [];
page.on('request', req => { if (req.url().includes('.woff2')) fontRequests.push(req.url()); });
await page.waitForTimeout(2000);
if (fontRequests.length < 4) throw new Error('Expected at least 4 woff2 font requests, got ' + fontRequests.length);
// Verify Golos Text renders correctly
const h1Style = await page.evaluate(() => {
  const el = document.querySelector('h1');
  if (!el) return null;
  return window.getComputedStyle(el).fontFamily;
});
if (!h1Style || !h1Style.includes('Golos Text')) throw new Error('Golos Text not applied to h1: ' + h1Style);
```

**Скачать можно так:**
```bash
# Golos Text Bold (700) + Black (900)
Invoke-WebRequest -Uri "https://fonts.google.com/download?family=Golos+Text:wght@700;900" -OutFile "golos.zip"
Expand-Archive golos.zip -DestinationPath temp_fonts
# PT Serif Regular + Italic + Bold
Invoke-WebRequest -Uri "https://fonts.google.com/download?family=PT+Serif:ital,wght@0,400;0,700;1,400" -OutFile "ptserif.zip"
Expand-Archive ptserif.zip -DestinationPath temp_fonts
# JetBrains Mono
Invoke-WebRequest -Uri "https://fonts.google.com/download?family=JetBrains+Mono" -OutFile "jbmono.zip"
Expand-Archive jbmono.zip -DestinationPath temp_fonts
# Copy only woff2 files to site/fonts/
Get-ChildItem temp_fonts -Recurse -Filter *.woff2 | Copy-Item -Destination site/fonts/
Remove-Item -Recurse -Force temp_fonts, golos.zip, ptserif.zip, jbmono.zip
```
> Если Google Fonts Download API не работает через Invoke-WebRequest, скачать вручную через браузер на https://fonts.google.com/ и положить woff2 в `site/fonts/`.

---

## Story 02: CSS foundation — tokens, reset, body, noise

**Что:** Создать `site/css/brutalist.css` — `:root`-токены, reset, базовые стили body, шумовая текстура.

**Файл:** `site/css/brutalist.css`
```css
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  font-family: 'PT Serif', Georgia, serif;
  background: #0A0A0A;
  color: #FFFFFF;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
  position: relative;
}

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
  --text-xs: 0.75rem; --text-sm: 0.875rem; --text-base: 1rem;
  --text-lg: 1.25rem; --text-xl: 1.5rem; --text-2xl: 2rem;
  --text-3xl: clamp(2rem, 5vw, 3rem); --text-hero: clamp(3rem, 8vw, 7rem);
  --space-2: 8px; --space-4: 16px; --space-6: 24px; --space-8: 32px;
  --space-12: 48px; --space-16: 64px;
}

::selection { background: #DC2626; color: #FFFFFF; }

/* Noise texture overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 9999;
  opacity: 0.035;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

h1, h2, h3, h4, .heading { font-family: var(--font-heading); font-weight: 700; line-height: 1.1; }
h1 { font-size: var(--text-hero); letter-spacing: -0.03em; text-transform: uppercase; }
h2 { font-size: var(--text-3xl); }
p { line-height: 1.7; }
a { color: var(--color-text); text-decoration: underline; transition: color 0.2s; }
a:hover { color: var(--color-accent); }
```

**Playwright-тест:**
```js
// Story 02: Verify black background, white text, noise texture
const page = await context.newPage();
await page.goto('http://localhost:3000');
const bg = await page.evaluate(() => window.getComputedStyle(document.body).backgroundColor);
if (bg !== 'rgb(10, 10, 10)') throw new Error('Background not black: ' + bg);
const color = await page.evaluate(() => window.getComputedStyle(document.body).color);
if (color !== 'rgb(255, 255, 255)') throw new Error('Text not white: ' + color);
// Check noise pseudo-element exists
const hasBefore = await page.evaluate(() => {
  const style = window.getComputedStyle(document.body, '::before');
  return style.backgroundImage !== 'none';
});
if (!hasBefore) throw new Error('Noise overlay missing');

// Mobile: verify body still black
await page.setViewportSize({ width: 480, height: 800 });
const bgMobile = await page.evaluate(() => window.getComputedStyle(document.body).backgroundColor);
if (bgMobile !== 'rgb(10, 10, 10)') throw new Error('Mobile bg not black: ' + bgMobile);
```

---

## Story 03: Header component

**Что:** Создать `site/src/components/header.html` — логотип «AntiManager» + навигация.

**Файл:** `site/src/components/header.html`
```html
<header class="site-header">
  <a href="/" class="logo"><span class="logo-accent">Anti</span>Manager</a>
  <nav class="header-nav">
    <a href="/manifesto/">Манифест</a>
    <a href="/archive/">Архив</a>
    <a href="/arsenal/">Арсенал</a>
    <a href="/scenarios/">Сценарии</a>
    <a href="/cases/">Дневники</a>
  </nav>
</header>
```

**CSS (добавить в brutalist.css):**
```css
.site-header {
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--space-4) var(--space-8);
  background: var(--color-bg);
  border-bottom: 2px solid var(--color-accent);
}
.logo {
  font-family: var(--font-heading); font-weight: 900; font-size: var(--text-xl);
  text-decoration: none; color: var(--color-text);
}
.logo-accent { color: var(--color-accent); }
.header-nav { display: flex; gap: var(--space-6); }
.header-nav a { text-decoration: none; font-family: var(--font-heading); font-weight: 700;
  font-size: var(--text-sm); text-transform: uppercase; letter-spacing: 0.05em; }
.header-nav a:hover { text-decoration: underline; }

@media (max-width: 768px) {
  .site-header { padding: var(--space-4); flex-wrap: wrap; }
  .header-nav { gap: var(--space-3); overflow-x: auto; width: 100%; margin-top: var(--space-2); }
  .header-nav a { font-size: var(--text-xs); white-space: nowrap; }
}
```

**Playwright-тест:**
```js
// Story 03: Header renders, logo red accent, border-bottom visible
const page = await context.newPage();
await page.goto('http://localhost:3000');
const logoColor = await page.evaluate(() => {
  const el = document.querySelector('.logo-accent');
  if (!el) return null;
  return window.getComputedStyle(el).color;
});
if (!logoColor || !logoColor.includes('220') || !logoColor.includes('38')) throw new Error('Logo accent not red: ' + logoColor);
// Header has border-bottom
const borderBottom = await page.evaluate(() => {
  return window.getComputedStyle(document.querySelector('.site-header')).borderBottom;
});
if (!borderBottom.includes('2px')) throw new Error('Header border missing: ' + borderBottom);

// Mobile: nav wraps, still visible
await page.setViewportSize({ width: 480, height: 800 });
const navVisible = await page.evaluate(() => {
  const nav = document.querySelector('.header-nav');
  return nav && window.getComputedStyle(nav).display !== 'none';
});
if (!navVisible) throw new Error('Header nav hidden on mobile');
```

---

## Story 04: Buttons — primary, secondary, crisis pulse

**Что:** CSS-классы для кнопок в brutalist.css.

**CSS (добавить в brutalist.css):**
```css
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  border: 2px solid var(--color-accent);
  font-family: var(--font-heading); font-weight: 700; font-size: var(--text-sm);
  text-transform: uppercase; letter-spacing: 0.05em;
  cursor: pointer; transition: all 0.15s;
  text-decoration: none; color: var(--color-text); background: transparent;
}
.btn:hover { background: var(--color-accent); color: #fff; }
.btn:active { transform: scale(0.97); }
.btn-primary { background: var(--color-accent); color: #fff; }
.btn-primary:hover { background: var(--color-accent-dark); }
.btn-crisis {
  background: var(--color-accent); color: #fff;
  animation: pulse-crisis 2s ease-in-out infinite;
}
@keyframes pulse-crisis {
  0%, 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.5); }
  50%      { box-shadow: 0 0 0 12px rgba(220, 38, 38, 0); }
}
```

**Playwright-тест:**
```js
// Story 04: Buttons render, crisis button pulses
const page = await context.newPage();
await page.goto('http://localhost:3000');
// Check primary button exists and is red
const btnBg = await page.evaluate(() => {
  const el = document.querySelector('.btn-primary');
  if (!el) return null;
  return window.getComputedStyle(el).backgroundColor;
});
if (!btnBg || !btnBg.includes('rgb(220')) throw new Error('Primary button bg not red: ' + btnBg);
// Check crisis button has animation
const hasAnim = await page.evaluate(() => {
  const el = document.querySelector('.btn-crisis');
  if (!el) return null;
  return window.getComputedStyle(el).animation.includes('pulse-crisis');
});
if (!hasAnim) throw new Error('Crisis button missing pulse animation');
// Hover changes color
await page.hover('.btn-primary');
await page.waitForTimeout(300);
const hoverBg = await page.evaluate(() => {
  return window.getComputedStyle(document.querySelector('.btn-primary:hover') || document.querySelector('.btn-primary')).backgroundColor;
});
// Mobile: buttons clickable
await page.setViewportSize({ width: 480, height: 800 });
const btnMobile = await page.evaluate(() => {
  const el = document.querySelector('.btn');
  return el && window.getComputedStyle(el).display !== 'none';
});
if (!btnMobile) throw new Error('Button hidden on mobile');
```

---

## Story 05: Red corner + diagonal dividers + torn edges

**Что:** Фиксированный красный уголок на каждой странице. Диагональные разделители секций. Эффект рваных краёв для карточек.

**CSS (добавить в brutalist.css):**
```css
.red-corner {
  position: fixed; top: 0; right: 0; z-index: 200;
  width: 48px; height: 48px; background: var(--color-accent);
}
@media (max-width: 768px) { .red-corner { width: 28px; height: 28px; } }

.section-diagonal {
  position: relative; padding: var(--space-12) 0; margin: var(--space-8) 0;
}
.section-diagonal::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 24px;
  background: var(--color-bg);
  clip-path: polygon(0 100%, 100% 0, 100% 100%);
  transform: translateY(-100%);
}

.torn-card {
  position: relative;
  border: 2px solid var(--color-steel);
  clip-path: polygon(
    0% 2%, 2% 0%, 8% 0%, 9% 1%, 20% 0%, 22% 2%, 50% 0%, 51% 2%,
    80% 0%, 82% 1%, 95% 0%, 98% 2%, 100% 5%, 98% 50%,
    100% 95%, 98% 98%, 95% 100%, 80% 99%, 75% 100%, 50% 99%,
    48% 100%, 20% 99%, 18% 100%, 5% 99%, 2% 98%, 0% 95%,
    2% 50%, 0% 5%
  );
}
```

**Playwright-тест:**
```js
// Story 05: Red corner visible, diagonal divider present
const page = await context.newPage();
await page.goto('http://localhost:3000');
const corner = await page.evaluate(() => {
  const el = document.querySelector('.red-corner');
  if (!el) return null;
  const s = window.getComputedStyle(el);
  return { bg: s.backgroundColor, pos: s.position };
});
if (!corner || corner.pos !== 'fixed') throw new Error('Red corner missing or not fixed');
// Mobile: red corner smaller
await page.setViewportSize({ width: 480, height: 800 });
const cornerW = await page.evaluate(() => {
  return parseInt(window.getComputedStyle(document.querySelector('.red-corner')).width);
});
if (cornerW > 32) throw new Error('Mobile red corner too big: ' + cornerW);
```

---

## Story 06: Weapon cards

**Что:** Карточка статьи-оружия с левой красной полосой, заголовком, subtitle, hover-эффектом. **Без нумерации** — только название и подзаголовок.

**CSS (добавить в brutalist.css):**
```css
.weapon-card {
  display: block;
  background: var(--color-bg);
  border: 2px solid var(--color-steel);
  border-left: 6px solid var(--color-accent);
  padding: var(--space-4) var(--space-6);
  text-decoration: none;
  transition: border-color 0.2s, transform 0.2s;
  position: relative;
}
.weapon-card:hover {
  border-color: var(--color-accent);
  transform: translateX(4px);
}
.weapon-title {
  font-family: var(--font-heading); font-weight: 700;
  font-size: var(--text-lg);
}
.weapon-subtitle {
  font-family: var(--font-body); font-size: var(--text-sm);
  color: var(--color-steel); margin-top: var(--space-1);
}
.weapon-status {
  display: inline-block; margin-top: var(--space-2);
  font-family: var(--font-mono); font-size: var(--text-xs);
  padding: 2px var(--space-2);
  border: 1px solid var(--color-steel);
}
.weapon-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}
@media (max-width: 768px) {
  .weapon-grid { grid-template-columns: 1fr; }
  .weapon-card { padding: var(--space-3) var(--space-4); }
}
```

**Playwright-тест:**
```js
// Story 06: Weapon cards render in grid, left red border visible, no numbering in UI
const page = await context.newPage();
await page.goto('http://localhost:3000');
const cards = await page.evaluate(() => document.querySelectorAll('.weapon-card').length);
if (cards < 2) throw new Error('Expected at least 2 weapon cards, got ' + cards);
// First card has red left border
const leftBorder = await page.evaluate(() => {
  const el = document.querySelector('.weapon-card');
  return window.getComputedStyle(el).borderLeft;
});
if (!leftBorder.includes('rgb(220')) throw new Error('No red left border: ' + leftBorder);
// Card title exists but NO number visible (no "00." prefix, no weapon-number element)
const title = await page.evaluate(() => {
  return document.querySelector('.weapon-title')?.textContent || '';
});
if (!title) throw new Error('Weapon card title missing');
const hasNumberSpan = await page.evaluate(() => !!document.querySelector('.weapon-number'));
if (hasNumberSpan) throw new Error('weapon-number class found — numbering should NOT be in UI');
// Hover effect works
await page.hover('.weapon-card');
await page.waitForTimeout(300);
const afterHover = await page.evaluate(() => {
  return window.getComputedStyle(document.querySelector('.weapon-card')).borderColor;
});
if (!afterHover.includes('rgb(220')) throw new Error('Hover did not turn border red: ' + afterHover);
// Mobile: single column
await page.setViewportSize({ width: 480, height: 800 });
const cols = await page.evaluate(() => {
  const grid = document.querySelector('.weapon-grid');
  return window.getComputedStyle(grid).gridTemplateColumns;
});
if (cols !== '1fr' && !cols.startsWith('repeat(1')) throw new Error('Mobile grid not single column: ' + cols);
```

---

## Story 07: Combat zone cards + case diary cards

**Что:** 4 прямоугольные карточки зон боевых действий (Crisis/Team/Changes/System) + карточки полевых дневников.

**CSS (добавить в brutalist.css):**
```css
.zone-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}
.zone-card {
  padding: var(--space-6); text-decoration: none; transition: transform 0.2s;
}
.zone-card:hover { transform: translateY(-4px); }
.zone-card.zone-crisis  { background: var(--color-accent); color: #fff; border: 2px solid var(--color-accent); }
.zone-card.zone-team    { background: var(--color-steel); color: #fff; border: 2px solid var(--color-steel); }
.zone-card.zone-changes { background: var(--color-bg); border: 2px solid var(--color-accent); }
.zone-card.zone-system  { background: var(--color-bg); border: 2px dashed var(--color-accent); }
.zone-icon { font-size: 2rem; }
.zone-title { font-family: var(--font-heading); font-weight: 900; font-size: var(--text-xl); margin-top: var(--space-2); }
.zone-subtitle { font-size: var(--text-sm); margin-top: var(--space-1); opacity: 0.8; }
.zone-count {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 50%;
  background: #fff; color: var(--color-bg);
  font-family: var(--font-heading); font-weight: 700; font-size: var(--text-xs);
  margin-top: var(--space-3);
}

.case-card {
  border: 2px dashed var(--color-steel); padding: var(--space-4) var(--space-6);
  text-decoration: none; transition: border-color 0.2s;
}
.case-card:hover { border-color: var(--color-accent); }
.case-headline { font-family: var(--font-heading); font-weight: 700; font-size: var(--text-lg); }
.case-headline span { color: var(--color-accent); margin-right: var(--space-2); }
.case-readtime { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-steel); margin-top: var(--space-1); }
.case-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}

@media (max-width: 768px) {
  .zone-grid, .case-grid { grid-template-columns: 1fr; }
}
```

**Playwright-тест:**
```js
// Story 07: Zone cards and case cards render with correct styles
const page = await context.newPage();
await page.goto('http://localhost:3000');
// 4 zone cards present
const zones = await page.evaluate(() => document.querySelectorAll('.zone-card').length);
if (zones !== 4) throw new Error('Expected 4 zone cards, got ' + zones);
// Crisis zone has red bg
const crisisBg = await page.evaluate(() => {
  return window.getComputedStyle(document.querySelector('.zone-crisis')).backgroundColor;
});
if (!crisisBg.includes('rgb(220')) throw new Error('Crisis zone not red: ' + crisisBg);
// Mobile: single column
await page.setViewportSize({ width: 480, height: 800 });
const zoneCols = await page.evaluate(() => {
  return window.getComputedStyle(document.querySelector('.zone-grid')).gridTemplateColumns;
});
if (zoneCols !== '1fr' && !zoneCols.startsWith('repeat(1')) throw new Error('Zone grid not 1-col on mobile');
```

---

## Story 08: Star map — dynamic brutalism restyle

**Что:** Создать функцию `starSvg(scenarios, weapons)` в build.js, которая генерирует SVG-карту динамически: один луч на каждую зону из `scenarios.json`, точки на лучах = статьи этой зоны. Чёрно-красная палитра, перекрестия, заглавные метки.

**Алгоритм starSvg():**
1. Читает `scenarios.json` — получает 4 зоны. Количество лучей = количество зон.
2. Для каждой зоны считает статьи через `scenario.weapons.length` (сколько id в массиве weapons).
3. Равномерно распределяет лучи по кругу (360° / N зон).
4. Рисует: внешние кольца, перекрестия → лучи → точки статей на лучах → метки зон → центр «АНТИМЕНЕДЖЕР».
5. Все цвета: `#DC2626` (красный), `#fff` (белый). Фон прозрачный (наследует чёрный).

**Код функции (вставить в build.js):**
```js
function starSvg(scenarios, weapons) {
  const CX = 300, CY = 300, R = 220;
  const n = scenarios.length;
  const angleStep = 360 / n;

  let svg = `<svg viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:600px;height:auto;">`;

  // Outer rings
  svg += `<circle cx="${CX}" cy="${CY}" r="250" fill="none" stroke="#DC2626" stroke-width="1" stroke-dasharray="8 8" opacity="0.3"/>`;
  svg += `<circle cx="${CX}" cy="${CY}" r="240" fill="none" stroke="#DC2626" stroke-width="0.5" opacity="0.15"/>`;

  // Crosshair rings
  svg += `<circle cx="${CX}" cy="${CY}" r="55" fill="none" stroke="#DC2626" stroke-width="0.5" stroke-dasharray="4 4" opacity="0.4"/>`;
  svg += `<circle cx="${CX}" cy="${CY}" r="75" fill="none" stroke="#DC2626" stroke-width="0.5" stroke-dasharray="4 4" opacity="0.2"/>`;

  // Rays + labels + article dots
  scenarios.forEach((s, i) => {
    const angle = (i * angleStep - 90) * Math.PI / 180; // start from top
    const ex = CX + R * Math.cos(angle);
    const ey = CY + R * Math.sin(angle);
    const labelR = R + 30;
    const lx = CX + labelR * Math.cos(angle);
    const ly = CY + labelR * Math.sin(angle);

    // Ray line
    svg += `<line x1="${CX}" y1="${CY}" x2="${ex}" y2="${ey}" stroke="#DC2626" stroke-width="3" opacity="0.3" stroke-linecap="round"/>`;

    // Article dots along the ray
    const count = s.weapons.length;
    for (let j = 0; j < Math.min(count, 8); j++) {
      const t = (j + 1) / (count + 1);
      const dx = CX + (R * 0.85 * t) * Math.cos(angle);
      const dy = CY + (R * 0.85 * t) * Math.sin(angle);
      svg += `<circle cx="${dx}" cy="${dy}" r="3" fill="#DC2626" opacity="${0.4 + j * 0.1}"/>`;
    }

    // Zone label
    svg += `<text x="${lx}" y="${ly}" fill="#DC2626" font-family="'Golos Text',sans-serif" font-weight="900" font-size="12" text-anchor="middle" letter-spacing="1">${s.title}</text>`;

    // Article count badge
    svg += `<circle cx="${lx}" cy="${ly + 18}" r="12" fill="#DC2626"/>`;
    svg += `<text x="${lx}" y="${ly + 22}" fill="#fff" font-family="'Golos Text',sans-serif" font-weight="700" font-size="10" text-anchor="middle">${count}</text>`;
  });

  // Center hub
  svg += `<circle cx="${CX}" cy="${CY}" r="40" fill="#0A0A0A" stroke="#DC2626" stroke-width="3"/>`;
  svg += `<text x="${CX}" y="${CY - 5}" fill="#fff" font-family="'Golos Text',sans-serif" font-weight="900" font-size="11" text-anchor="middle" letter-spacing="3">АНТИ</text>`;
  svg += `<text x="${CX}" y="${CY + 12}" fill="#DC2626" font-family="'Golos Text',sans-serif" font-weight="900" font-size="11" text-anchor="middle" letter-spacing="2">МЕНЕДЖЕР</text>`;

  svg += `</svg>`;
  return svg;
}
```

**Playwright-тест:**
```js
// Story 08: Star map SVG renders dynamically. Rays = number of scenarios (4). Red colors.
const page = await context.newPage();
await page.goto('http://localhost:3000');
const svg = await page.evaluate(() => {
  const el = document.querySelector('.map-container svg');
  if (!el) return null;
  return {
    viewBox: el.getAttribute('viewBox'),
    circles: el.querySelectorAll('circle').length,
    lines: el.querySelectorAll('line').length,
  };
});
if (!svg || !svg.viewBox) throw new Error('SVG star map missing');
// Lines = number of zones (4 rays)
if (svg.lines !== 4) throw new Error('Expected 4 rays (one per zone), got ' + svg.lines);
// Crosshair rings present
if (svg.circles < 4) throw new Error('Expected at least 4 circles (rings + badges), got ' + svg.circles);
// Central text contains АНТИМЕНЕДЖЕР
const centerText = await page.evaluate(() => {
  const texts = document.querySelectorAll('.map-container svg text');
  return Array.from(texts).map(t => t.textContent).join(' ');
});
if (!centerText.includes('АНТИ') || !centerText.includes('МЕНЕДЖЕР')) throw new Error('Center labels missing: ' + centerText);
// Mobile: SVG scales down
await page.setViewportSize({ width: 480, height: 800 });
const svgWidth = await page.evaluate(() => {
  const el = document.querySelector('.map-container svg');
  return el ? el.getBoundingClientRect().width : 0;
});
if (svgWidth < 200 || svgWidth > 500) throw new Error('SVG not responsive, width=' + svgWidth);
```

---

## Story 09: Data files — weapons.json, scenarios.json, thinkers.json

**Что:** Создать три JSON-файла данных для build.js.

**Файл:** `site/src/data/weapons.json` — на основе `chapters.json`. **`id` — внутреннее поле (имена файлов, связи), НЕ показывается в UI.** Поле `zone` может быть `null` (статья без зоны — видна только в Арсенале).
```json
[
  { "id": "00", "title": "Маятник управления", "slug": "mayatnik-upravleniya", "subtitle": "Почему управленческие моды приходят и уходят, а проблемы остаются", "zone": "system", "thinker": "клаузевиц", "tags": ["методология", "системное-мышление"], "status": "review" },
  { "id": "03", "title": "Системная динамика в производстве", "slug": "sistemnaya-dinamika", ... "zone": null, ... },
  ...
]
```
> **Важно:** Зоны назначаются вручную по концепту пользователя (см. Design Decisions N4). Главы без зоны: 03, 07, 09, 12, 17, 21 (плюс будущие). Убираем поле `ray` — оно заменено на `zone`. Поле `part` (части книги) удаляется.

**Файл:** `site/src/data/scenarios.json` — убираем "23" (несуществующая глава):
```json
[
  { "id": "crisis", "title": "КРИЗИС", "subtitle": "Завод в хаосе. Сроки горят. Собственник даёт 3 месяца.", "icon": "🔥", "weapons": ["16", "18", "20", "22"] },
  { "id": "team", "title": "КОМАНДА", "subtitle": "Люди заморожены. Инициативы нет. Боятся ошибок.", "icon": "🛡️", "weapons": ["20", "10", "14"] },
  { "id": "changes", "title": "ИЗМЕНЕНИЯ", "subtitle": "Внедряю новую систему. Сопротивление. Саботаж.", "icon": "⚔️", "weapons": ["13", "11", "06", "04"] },
  { "id": "system", "title": "СИСТЕМА", "subtitle": "Хочу понять, как всё связано. Видеть паутину.", "icon": "🗺️", "weapons": ["00", "02", "05", "08", "15", "19"] }
]
```
> `weapons` — массив внутренних `id`, ссылающихся на `weapons.json`. Используется для генерации карточек зон на главной и в `/scenarios/`.

**Файл:** `site/src/data/thinkers.json`:
```json
[
  { "id": "шухарт", "name": "Уолтер Шухарт", "idea": "Статистический контроль процессов", "weapon": "PDCA", "years": "1891–1967" },
  { "id": "деминг", "name": "Эдвардс Деминг", "idea": "Качество как философия", "weapon": "14 принципов", "years": "1900–1993" },
  { "id": "оно", "name": "Таити Оно", "idea": "Производственная система Toyota", "weapon": "Lean / TPS", "years": "1912–1990" },
  { "id": "богданов", "name": "Александр Богданов", "idea": "Тектология — всеобщая организационная наука", "weapon": "Системное мышление", "years": "1873–1928" },
  { "id": "гастев", "name": "Алексей Гастев", "idea": "Научная организация труда", "weapon": "Социальная инженерия", "years": "1882–1939" },
  { "id": "керженцев", "name": "Платон Керженцев", "idea": "Принципы организации", "weapon": "Тайм-менеджмент", "years": "1881–1940" },
  { "id": "медоуз", "name": "Донелла Медоуз", "idea": "12 рычагов воздействия на систему", "weapon": "Системная динамика", "years": "1941–2001" },
  { "id": "сенге", "name": "Питер Сенге", "idea": "Пятая дисциплина", "weapon": "Обучающаяся организация", "years": "1947–" },
  { "id": "клаузевиц", "name": "Карл фон Клаузевиц", "idea": "О войне — трение и неопределённость", "weapon": "Стратегия", "years": "1780–1831" }
]
```

**Файл:** `site/src/data/cases.json` — копия существующего `cases.json`, без изменений структуры:
```json
[
  { "id": "master-i-poddon", "title": "Мастер и поддон", "desc": "Как абстрактная команда чуть не стоила человеку работы", "readtime": "5 минут", "tags": ["коммуникация", "увольнение"] },
  { "id": "nochnoy-zvonok", "title": "Ночной звонок", "desc": "Как я перестал решать проблемы за подчинённых", "readtime": "7 минут", "tags": ["делегирование", "беспомощность"] },
  { "id": "7-zavodov", "title": "Семь заводов", "desc": "Антикризис: один протокол — разные результаты", "readtime": "6 минут", "tags": ["кризис", "протокол"] },
  ...
]
```
> Поле `readtime` добавляется для отображения на карточках. Берётся из существующих `cases.json` + ручное добавление.

**Playwright-тест:**
```js
// Story 09: All 4 JSON files are valid and have expected keys
// Run via bash: node -e "const w=require('./src/data/weapons.json'); if(w.length<22) throw 'weapons <22: '+w.length; console.log('OK weapons: '+w.length)"
// Run via bash: node -e "const s=require('./src/data/scenarios.json'); if(s.length!==4) throw 'scenarios not 4'; console.log('OK scenarios')"
// Run via bash: node -e "const t=require('./src/data/thinkers.json'); if(t.length<9) throw 'thinkers <9: '+t.length; console.log('OK thinkers')"
// Run via bash: node -e "const c=require('./src/data/cases.json'); if(c.length<10) throw 'cases <10: '+c.length; console.log('OK cases: '+c.length)"
```
> Skip browser test — this is a data validation story. Run the 3 node -e checks above.

---

## Story 10: Base template + Footer component

**Что:** Создать `site/src/templates/base.html` — минимальный каркас. Создать `site/src/components/footer.html`.

**Файл:** `site/src/templates/base.html`
```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{title}}</title>
  <meta name="description" content="{{description}}">
  <link rel="stylesheet" href="/css/fonts.css">
  <link rel="stylesheet" href="/css/brutalist.css">
  {{head_extra}}
</head>
<body>
  <div class="red-corner" aria-hidden="true"></div>
  {{header}}
  {{content}}
  {{footer}}
  {{scripts}}
</body>
</html>
```

**Файл:** `site/src/components/footer.html`
```html
<footer class="site-footer">
  <p class="footer-oath">Антименеджер — это не метод. Это присяга.</p>
  <p class="footer-sub">© {{year}} AntiManager. Никаких гарантий. Только твой выбор.</p>
</footer>
```

**CSS (добавить в brutalist.css):**
```css
.site-footer {
  border-top: 2px solid var(--color-accent);
  padding: var(--space-12) var(--space-8); text-align: center;
  margin-top: var(--space-16);
}
.footer-oath {
  font-family: var(--font-heading); font-weight: 900;
  font-size: var(--text-xl); text-transform: uppercase; letter-spacing: 0.05em;
}
.footer-sub { color: var(--color-steel); font-size: var(--text-sm); margin-top: var(--space-4); }
```

**Playwright-тест:**
```js
// Story 10: Base template renders <html lang="ru">, red corner visible, footer has oath text
const page = await context.newPage();
await page.goto('http://localhost:3000');
const lang = await page.evaluate(() => document.documentElement.lang);
if (lang !== 'ru') throw new Error('lang attribute not ru: ' + lang);
const oath = await page.evaluate(() => {
  const el = document.querySelector('.footer-oath');
  return el ? el.textContent.includes('Антименеджер') : false;
});
if (!oath) throw new Error('Footer oath text missing');
```

---

## Story 11: New build.js — static pages

**Что:** Переписать `site/build.js` для генерации статических страниц: index (пустой), manifesto, archive, arsenal, scenarios, cases, headquarters, about, 404, privacy, sitemap, robots.txt.

**Ключевые функции build.js:**
- `read(name)` — чтение файлов из `src/`
- `write(path, content)` — запись в `dist/`
- `copyDir(src, dst)` — копирование папок (css, js, fonts)
- `renderPage(title, desc, content, opts)` — сборка через base.html, замена `{{title}}`, `{{description}}`, `{{header}}`, `{{content}}`, `{{footer}}`, `{{head_extra}}`, `{{scripts}}`, `{{year}}`
- Каждая страница = вызов `renderPage()` с контентом из JavaScript-строки

**Структура build.js (псевдокод):**
```js
const fs = require('fs'); const path = require('path');
const SITE_URL = 'https://antimanager.pro';
function read(name) { return fs.readFileSync(path.join(__dirname, name), 'utf-8'); }
function write(filepath, content) { /* mkdir + writeFile */ }
function copyDir(src, dst) { /* recursive copy */ }

const base = read('src/templates/base.html');
const headerHtml = read('src/components/header.html');
const footerHtml = read('src/components/footer.html');

const weapons = JSON.parse(read('src/data/weapons.json'));
const scenarios = JSON.parse(read('src/data/scenarios.json'));
const thinkers = JSON.parse(read('src/data/thinkers.json'));
const cases = JSON.parse(read('src/data/cases.json'));

function renderPage(title, desc, content, opts = {}) {
  let html = base;
  html = html.replace('{{title}}', title);
  html = html.replace('{{description}}', desc);
  html = html.replace('{{header}}', headerHtml);
  html = html.replace('{{content}}', content);
  html = html.replace('{{footer}}', footerHtml.replace('{{year}}', '2026'));
  html = html.replace('{{head_extra}}', opts.headExtra || '');
  html = html.replace('{{scripts}}', opts.scripts || '');
  return html;
}

// === CONTENT GENERATION HELPERS ===

// Helper: find weapon by internal id
function weaponById(id) { return weapons.find(w => w.id === id); }

// Helper: zone badge HTML
function zoneBadgeHtml(zone) {
  const labels = { crisis: 'КРИЗИС', team: 'КОМАНДА', changes: 'ИЗМЕНЕНИЯ', system: 'СИСТЕМА' };
  if (!zone) return '';
  return `<span class="badge badge-zone badge-zone-${zone}">${labels[zone] || zone}</span>`;
}

// === PAGE CONTENT GENERATORS ===

const manifestoContent = `
<section class="content-page">
  <h1>Манифест</h1>
  <p class="weapon-subtitle">Manifestum Imperii Rationalis — Манифест рационального управления</p>
  <div class="manifesto-values">
    <div class="manifesto-value"><span>1.</span> Люди и их потенциал над слепым исполнением инструкций</div>
    <div class="manifesto-value"><span>2.</span> Работающая и справедливая система над героизмом и авралами</div>
    <div class="manifesto-value"><span>3.</span> Сотрудничество и доверие над тотальным контролем и подозрительностью</div>
    <div class="manifesto-value"><span>4.</span> Постоянное улучшение процессов над поиском виноватых</div>
    <div class="manifesto-value"><span>5.</span> Смысл и осознанность над слепым следованием трендам</div>
    <div class="manifesto-value"><span>6.</span> Прозрачность и конституция над устными указаниями и кулуарными решениями</div>
    <div class="manifesto-value"><span>7.</span> Ментальное здоровье над когнитивным перегрузом</div>
    <div class="manifesto-value"><span>8.</span> Конфликт мнений над уютным консенсусом</div>
    <div class="manifesto-value"><span>9.</span> Антихрупкость над хрупкой эффективностью</div>
    <div class="manifesto-value"><span>10.</span> Открытая политика над неформальной властью</div>
  </div>
  <h2>15 принципов</h2>
  <ol class="manifesto-principles">
    <li>Наша высшая цель — построить самовоспроизводящуюся систему, которая стабильно даёт результат, даже когда нас нет на месте.</li>
    <li>Мы выходим в <em>гембу</em> не для того, чтобы найти виноватых, а чтобы понять и улучшить процесс.</li>
    <li>Мы — гаранты конституции. Наша роль — защищать правила игры для всех, включая себя.</li>
    <!-- ... 15 total ... -->
  </ol>
</section>`;

const archiveContent = `
<section class="content-page">
  <h1>Архив великих идей</h1>
  <p class="weapon-subtitle">Великие мыслители уже говорили это. Мы просто снимаем консалтинговую пыль.</p>
  <div class="thinker-grid">
    ${thinkers.map(t => `
      <div class="thinker-card">
        <div class="thinker-name">${t.name}</div>
        <div class="thinker-years">${t.years}</div>
        <div class="thinker-idea">${t.idea}</div>
        <div class="thinker-arrow">→ ${t.weapon}</div>
      </div>
    `).join('')}
  </div>
</section>`;

const arsenalContent = `
<section class="content-page">
  <h1>Арсенал</h1>
  <p class="weapon-subtitle">${weapons.filter(w => w.status === 'published').length} опубликовано, ${weapons.length} всего. Выбери оружие.</p>
  <div class="filters">
    <button class="filter-btn active" data-filter="all">ВСЕ</button>
    ${scenarios.map(s => `<button class="filter-btn" data-filter="${s.id}">${s.title}</button>`).join('')}
  </div>
  <div class="weapon-grid" id="arsenalGrid">
    ${weapons.map(w => `
      <a href="/weapons/${w.slug}/" class="weapon-card" data-zone="${w.zone || ''}">
        <div class="weapon-title">${w.title}</div>
        <div class="weapon-subtitle">${w.subtitle || ''}</div>
        ${w.zone ? zoneBadgeHtml(w.zone) : ''}
        <span class="weapon-status" style="margin-left:var(--space-2);">${statusLabels[w.status] || w.status}</span>
      </a>
    `).join('')}
  </div>
</section>
<script>
  document.addEventListener('DOMContentLoaded', function(){
    var btns = document.querySelectorAll('.filters .filter-btn');
    var cards = document.querySelectorAll('#arsenalGrid .weapon-card');
    btns.forEach(function(b){ b.addEventListener('click', function(){
      btns.forEach(function(x){x.classList.remove('active');});
      this.classList.add('active');
      var f = this.dataset.filter;
      cards.forEach(function(c){
        c.style.display = (f === 'all' || c.dataset.zone === f) ? '' : 'none';
      });
    });});
  });
</script>`;

const scenariosContent = `
<section class="content-page">
  <h1>Сценарии</h1>
  <p class="weapon-subtitle">Выбери свой участок фронта — получи набор оружия.</p>
  ${scenarios.map(s => {
    const zoneWeapons = s.weapons.map(id => weaponById(id)).filter(Boolean);
    return `
    <div class="zone-card zone-${s.id}">
      <div class="zone-icon">${s.icon}</div>
      <div class="zone-title">${s.title}</div>
      <p>${s.subtitle}</p>
      <div class="weapon-grid" style="margin-top:var(--space-4);">
        ${zoneWeapons.map(w => `
          <a href="/weapons/${w.slug}/" class="weapon-card">
            <div class="weapon-title">${w.title}</div>
            <div class="weapon-subtitle">${w.subtitle || ''}</div>
          </a>
        `).join('')}
      </div>
    </div>`;
  }).join('')}
</section>`;

const casesContent = `
<section class="content-page">
  <h1>Полевые дневники</h1>
  <p class="weapon-subtitle">Реальные истории с заводов.</p>
  <div class="case-grid">
    ${cases.map(c => `
      <div class="case-card">
        <div class="case-headline"><span>⚔️</span>${c.title}</div>
        <p class="weapon-subtitle">${c.desc}</p>
        <div class="case-readtime">⏱ ${c.readtime || '5 минут'}</div>
      </div>
    `).join('')}
  </div>
</section>`;

const hqContent = `
<section class="content-page" style="text-align:center;padding-top:var(--space-16);">
  <h1>Штаб</h1>
  <p class="weapon-subtitle">Закрытый клуб партизан. Здесь не обсуждают теорию. Здесь разбирают боевые ситуации.</p>
  <p style="color:var(--color-steel);margin:var(--space-4) 0;">⚡ Еженедельный разбор полётов · ⚡ Анонимные вопросы · ⚡ Реальные кейсы</p>
  <a href="https://t.me/antimanager" class="btn btn-crisis" style="margin-top:var(--space-6);">💬 ВСТУПИТЬ В TELEGRAM</a>
</section>`;

const aboutContent = `
<section class="content-page">
  <h1>О проекте</h1>
  <p class="weapon-subtitle">Антименеджер — это не метод. Это присяга.</p>
  <div class="weapon-block">
    <p>Мы не изобретаем велосипед. Мы просто снимаем консалтинговую упаковку с идей Деминга, Тейлора, Богданова, Оно, Медоуз, Хапрова, Клаузевица... И адаптируем их к твоему конвейеру.</p>
  </div>
  <p style="margin-top:var(--space-6);color:var(--color-steel);">Единственный способ изменить систему — начать думать и делать осознанно.</p>
</section>`;

// === MAIN ===
console.log('\n🚀 AntiManager Brutalist Build\n');

// Index (landing — empty for now, fills in Story 14-19)
write('index.html', renderPage('AntiManager', '...', '<p>Landing placeholder</p>'));

// Static pages
write('manifesto/index.html', renderPage('Манифест | AntiManager', '...', manifestoContent));
write('archive/index.html', renderPage('Архив | AntiManager', '...', archiveContent));
write('arsenal/index.html', renderPage('Арсенал | AntiManager', '...', arsenalContent));
write('scenarios/index.html', renderPage('Сценарии | AntiManager', '...', scenariosContent));
write('headquarters/index.html', renderPage('Штаб | AntiManager', '...', hqContent));
write('about/index.html', renderPage('О проекте | AntiManager', '...', aboutContent));
write('404/index.html', renderPage('404', '...', '<h1>404</h1>', {}));
write('privacy/index.html', renderPage('Политика | AntiManager', '...', '<h1>Политика конфиденциальности</h1>', {}));
// sitemap.xml, robots.txt

// Copy assets
copyDir('css', 'css');
copyDir('js', 'js');
copyDir('fonts', 'fonts');

console.log('\n✅ Build complete.\n');
```

**Playwright-тест:**
```js
// Story 11: All static pages exist, no console errors, red corner on every page
const pages = ['/', '/manifesto/', '/archive/', '/arsenal/', '/scenarios/', '/headquarters/', '/about/'];
for (const url of pages) {
  const page = await context.newPage();
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  await page.goto('http://localhost:3000' + url);
  await page.waitForTimeout(500);
  const hasRedCorner = await page.evaluate(() => !!document.querySelector('.red-corner'));
  if (!hasRedCorner) throw new Error('Red corner missing on ' + url);
  // 404 should show 404 text
  if (url === '/404/') {
    const h1 = await page.evaluate(() => document.querySelector('h1')?.textContent || '');
    if (!h1.includes('404')) throw new Error('404 page broken');
  }
  await page.close();
}
```

**CSS supplement for static page components (add to brutalist.css):**
```css
/* Thinker cards (archive page) */
.thinker-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); }
.thinker-card { border: 2px solid var(--color-steel); padding: var(--space-4); position: relative; overflow: hidden; }
.thinker-card::after { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--color-steel); transition: width 0.2s, background 0.2s; }
.thinker-card:hover::after { width: 100%; background: rgba(220,38,38,0.08); }
.thinker-name { font-family: var(--font-heading); font-weight: 700; font-size: var(--text-lg); }
.thinker-years { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-steel); margin-top: var(--space-1); }
.thinker-idea { font-size: var(--text-sm); margin-top: var(--space-3); }
.thinker-arrow { font-family: var(--font-mono); font-size: var(--text-sm); color: var(--color-accent); margin-top: var(--space-2); }
@media (max-width: 768px) { .thinker-grid { grid-template-columns: 1fr; } }

/* Manifesto values (landing + manifesto page) */
.manifesto-values { margin: var(--space-8) 0; }
.manifesto-value { font-size: var(--text-base); padding: var(--space-3) 0; border-bottom: 1px solid var(--color-steel); }
.manifesto-value span { color: var(--color-accent); font-family: var(--font-heading); font-weight: 700; margin-right: var(--space-3); }
.manifesto-principles { margin: var(--space-6) 0; padding-left: var(--space-5); }
.manifesto-principles li { padding: var(--space-2) 0; font-size: var(--text-sm); line-height: 1.7; color: var(--color-steel); }
.manifesto-principles li::marker { color: var(--color-accent); font-weight: 700; }

/* Arsenal filters */
.filters { display: flex; flex-wrap: wrap; gap: var(--space-2); margin: var(--space-6) 0; }
.filter-btn { padding: var(--space-2) var(--space-4); border: 2px solid var(--color-steel); background: transparent; color: var(--color-steel); font-family: var(--font-heading); font-weight: 700; font-size: var(--text-xs); text-transform: uppercase; cursor: pointer; transition: all 0.15s; }
.filter-btn:hover { border-color: var(--color-accent); color: var(--color-accent); }
.filter-btn.active { background: var(--color-accent); border-color: var(--color-accent); color: #fff; }
```

> ⚠️ **JS transition note:** Старый `site/js/common.js` содержит sidebar, modals, theme toggle — удалить. Аккордеоны и download buttons перенести в новый `site/js/brutalist.js` (создаётся в Story 19). Инлайн-скрипты в контент-файлах (`src/content/XX-slug.html`) не трогать — они самодостаточны. Фильтр арсенала — инлайн в `arsenalContent`.

---

## Story 12: Weapon pages generation

**Что:** Добавить в build.js генерацию страниц статей из `weapons.json` + `site/src/content/XX-slug.html` (существующие контент-файлы). **Без нумерации в UI.**

**Код в build.js (добавить после генерации статических страниц):**
```js
const weaponTemplate = `
<div class="content-page">
  <nav class="breadcrumbs">
    <a href="/">Главная</a> <span class="sep">→</span>
    <a href="/arsenal/">Арсенал</a> <span class="sep">→</span>
    <span>{{title}}</span>
  </nav>
  <section class="weapon-hero">
    {{zone_badge}}
    <h1>{{title}}</h1>
    <p class="weapon-subtitle">{{subtitle}}</p>
    {{status_badge}}
  </section>
  {{content_body}}
  {{thinker_block}}
  {{download_section}}
  {{related_weapons}}
</div>
`;

const zoneLabels = { crisis: 'КРИЗИС', team: 'КОМАНДА', changes: 'ИЗМЕНЕНИЯ', system: 'СИСТЕМА' };
const statusLabels = { published: 'Опубликовано', review: 'На ревью', draft: 'Черновик' };

for (const w of weapons) {
  const contentPath = `src/content/${w.id}-${w.slug}.html`;
  const hasContent = fs.existsSync(path.join(__dirname, contentPath));
  let contentBody = hasContent ? read(contentPath) : '<p>Статья в разработке</p>';

  // Zone badge (only if zone is assigned)
  const zoneBadge = w.zone
    ? `<span class="badge badge-zone badge-zone-${w.zone}">${zoneLabels[w.zone] || w.zone}</span>`
    : '';

  // Status badge
  const statusBadge = `<span class="badge badge-status badge-status-${w.status}">${statusLabels[w.status] || w.status}</span>`;

  // Thinker block (optional)
  const thinker = thinkers.find(t => t.id === w.thinker);
  const thinkerBlock = thinker
    ? `<div class="thinker-block"><strong>Изначальная идея:</strong> ${thinker.name} (${thinker.years}) → ${thinker.weapon}</div>`
    : '';

  // Download section
  const downloadSection = `
    <div class="download-section">
      <h3>Скачать материалы</h3>
      <p>Хотите получить дополнительные материалы к этой статье? Оставьте заявку — мы сообщим, когда формат будет готов.</p>
      <button class="btn download-btn" data-article="${w.slug}">Скачать</button>
      <p class="download-feedback" style="display:none;margin-top:var(--space-3);color:var(--color-steel);font-size:var(--text-sm);"></p>
    </div>`;

  // Related articles (same zone, different slug)
  const related = weapons.filter(r => r.zone === w.zone && r.slug !== w.slug && r.zone !== null);
  let relatedHtml = '';
  if (related.length) {
    relatedHtml = '<h2 class="section-title">В том же окопе</h2><div class="weapon-grid">' +
      related.slice(0, 4).map(r => `<a href="/weapons/${r.slug}/" class="weapon-card">
        <div class="weapon-title">${r.title}</div>
        <div class="weapon-subtitle">${r.subtitle || ''}</div>
      </a>`).join('') + '</div>';
  }

  let html = weaponTemplate;
  html = html.replace(/{{title}}/g, w.title);
  html = html.replace('{{subtitle}}', w.subtitle || '');
  html = html.replace('{{zone_badge}}', zoneBadge);
  html = html.replace('{{status_badge}}', statusBadge);
  html = html.replace('{{content_body}}', contentBody);
  html = html.replace('{{thinker_block}}', thinkerBlock);
  html = html.replace('{{download_section}}', downloadSection);
  html = html.replace('{{related_weapons}}', relatedHtml);

  write(`weapons/${w.slug}/index.html`, renderPage(
    w.title + ' | AntiManager',
    w.subtitle || '',
    html,
    { headExtra: '' }
  ));
  console.log('  ✓ ' + w.id + ' ' + w.slug);
}
```

**CSS (добавить в brutalist.css):**
```css
.content-page { max-width: 780px; margin: 0 auto; padding: var(--space-8); }
.weapon-hero { padding: var(--space-12) 0 var(--space-8); border-bottom: 1px solid var(--color-steel); margin-bottom: var(--space-8); }
.weapon-subtitle { font-size: var(--text-lg); color: var(--color-steel); margin-top: var(--space-3); }
.breadcrumbs { font-size: var(--text-sm); color: var(--color-steel); margin-bottom: var(--space-4); }
.breadcrumbs a { margin: 0 var(--space-1); }
.breadcrumbs .sep { margin: 0 var(--space-2); }

.badge-zone { display: inline-block; font-family: var(--font-heading); font-weight: 700;
  font-size: var(--text-xs); padding: 2px var(--space-3); text-transform: uppercase;
  letter-spacing: 0.05em; margin-bottom: var(--space-3); }
.badge-zone-crisis   { background: var(--color-accent); color: #fff; }
.badge-zone-team     { background: var(--color-steel); color: #fff; }
.badge-zone-changes  { border: 1px solid var(--color-accent); color: var(--color-accent); }
.badge-zone-system   { border: 1px dashed var(--color-accent); color: var(--color-accent); }

.badge-status { display: inline-block; margin-top: var(--space-3); margin-left: var(--space-2);
  font-family: var(--font-mono); font-size: var(--text-xs); padding: 2px var(--space-3); }
.badge-status-published { border: 1px solid #22c55e; color: #22c55e; }
.badge-status-review    { border: 1px solid var(--color-warning); color: var(--color-warning); }
.badge-status-draft     { border: 1px solid var(--color-steel); color: var(--color-steel); }

.thinker-block {
  margin: var(--space-8) 0; padding: var(--space-4) var(--space-6);
  border: 2px solid var(--color-steel); border-left: 6px solid var(--color-accent);
  font-size: var(--text-sm);
}
.thinker-block strong { font-family: var(--font-heading); }

.download-section {
  margin: var(--space-10) 0; padding: var(--space-6);
  border: 2px solid var(--color-accent); text-align: center;
}
.download-section h3 { font-family: var(--font-heading); font-weight: 900; text-transform: uppercase; }
.download-section p { color: var(--color-steel); margin: var(--space-3) 0; }
```

**Playwright-тест:**
```js
// Story 12: Weapon pages exist, no numbering in UI, zone badge + status badge visible
const weapons = require('./site/src/data/weapons.json');
const page = await context.newPage();
for (const w of weapons.slice(0, 5)) { // Check first 5 weapons (variety of zones)
  await page.goto('http://localhost:3000/weapons/' + w.slug + '/');
  const title = await page.evaluate(() => document.querySelector('h1')?.textContent || '');
  if (!title || !title.includes(w.title.substring(0, 5))) throw new Error('Title mismatch: expected ~' + w.title + ', got ' + title);
  // Breadcrumb does NOT contain a number (no "00." etc.)
  const breadcrumb = await page.evaluate(() => document.querySelector('.breadcrumbs')?.textContent || '');
  if (breadcrumb.match(/\d{2}\./)) throw new Error('Breadcrumb contains numbering — should not: ' + breadcrumb);
  // Zone badge present (if article has a zone)
  const hasZoneBadge = await page.evaluate(() => !!document.querySelector('.badge-zone'));
  if (w.zone && !hasZoneBadge) throw new Error('Zone badge missing for article: ' + w.slug);
  // Status badge present
  const hasStatusBadge = await page.evaluate(() => !!document.querySelector('.badge-status'));
  if (!hasStatusBadge) throw new Error('Status badge missing for article: ' + w.slug);
  // Red corner present
  const corner = await page.evaluate(() => !!document.querySelector('.red-corner'));
  if (!corner) throw new Error('Red corner missing on weapon page');
  // Download section visible
  const download = await page.evaluate(() => !!document.querySelector('.download-section'));
  if (!download) throw new Error('Download section missing');
  // No console errors
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  await page.waitForTimeout(300);
  if (errors.length) throw new Error('Console errors on ' + w.slug + ': ' + errors.join(', '));
}
await page.close();
```

---

## Story 13: Content blocks restyle — weapon-block, table, pull-quote, widget

**Что:** Добавить в brutalist.css переопределение старых классов контента (block-principle, table, widget) под новый стиль.

**CSS (добавить в brutalist.css):**
```css
/* Override old content blocks to brutalist style */
.block-principle, .weapon-block {
  background: var(--color-bg); border: 2px solid var(--color-steel);
  border-left: 6px solid var(--color-accent); padding: var(--space-4) var(--space-6);
  margin: var(--space-4) 0; font-size: var(--text-base);
}
.block-thesis {
  background: var(--color-bg); border: 2px solid var(--color-accent);
  border-left: 6px solid var(--color-accent); padding: var(--space-4) var(--space-6);
  margin: var(--space-4) 0;
}
.block-note {
  background: var(--color-bg); border: 1px dashed var(--color-steel);
  padding: var(--space-3) var(--space-4); margin: var(--space-3) 0;
  font-size: var(--text-sm); color: var(--color-steel);
}
.block-case {
  background: var(--color-bg); border: 1px dashed var(--color-steel);
  border-left: 3px solid var(--color-accent); padding: var(--space-3) var(--space-4);
  margin: var(--space-3) 0; font-size: var(--text-sm);
}

table { width: 100%; border-collapse: collapse; margin: var(--space-4) 0; font-size: var(--text-sm); }
th { font-family: var(--font-heading); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
  text-align: left; padding: var(--space-3); border-bottom: 2px solid var(--color-accent); }
td { padding: var(--space-3); border-bottom: 1px solid var(--color-steel); color: var(--color-steel); }
tr:hover td { background: rgba(220, 38, 38, 0.05); }

.widget {
  border: 2px solid var(--color-steel); padding: var(--space-6); margin: var(--space-8) 0;
}
.widget-title {
  font-family: var(--font-heading); font-weight: 900; font-size: var(--text-xl);
  text-transform: uppercase; margin-bottom: var(--space-4);
}
.btn-outline { border-color: var(--color-steel); color: var(--color-steel); }
.btn-outline:hover { border-color: var(--color-accent); color: #fff; background: var(--color-accent); }
.progress-bar { height: 8px; background: #1a1a1a; margin: var(--space-4) 0; }
.progress-fill { height: 100%; background: var(--color-accent); transition: width 0.4s; }

.form-group input, .form-group textarea, .form-group select {
  background: #1a1a1a; border: 1px solid var(--color-steel);
  color: var(--color-text); padding: var(--space-3); font-family: var(--font-body);
  font-size: var(--text-base); width: 100%;
}
.form-group input:focus, .form-group textarea:focus {
  outline: none; border-color: var(--color-accent);
}
```

**Playwright-тест:**
```js
// Story 13: Weapon page renders old content blocks correctly restyled
const page = await context.newPage();
// Use chapter 00 (Маятник) which has lots of content blocks
await page.goto('http://localhost:3000/weapons/mayatnik-upravleniya/');
// Check block-principle has red left border
const leftBorder = await page.evaluate(() => {
  const el = document.querySelector('.block-principle');
  if (!el) return null;
  return window.getComputedStyle(el).borderLeft;
});
if (!leftBorder || !leftBorder.includes('6px')) throw new Error('block-principle missing 6px left border');
// Check table renders with red headers
const thBorder = await page.evaluate(() => {
  const th = document.querySelector('th');
  if (!th) return null;
  return window.getComputedStyle(th).borderBottom;
});
if (!thBorder || !thBorder.includes('rgb(220')) throw new Error('Table header not red: ' + thBorder);
// Check widget button is restyled
const btnColor = await page.evaluate(() => {
  const el = document.querySelector('.btn-outline');
  if (!el) return null;
  return window.getComputedStyle(el).borderColor;
});
if (!btnColor) throw new Error('Widget button missing');
```

---

## Story 14: Main page — Hero section

**Что:** Добавить hero-секцию в landing-страницу (в build.js, функция buildIndex).

**HTML для hero в build.js:**
```html
<section class="hero">
  <div class="hero-challenge">
    <h1 class="hero-heading">ТЫ ПРИШЁЛ ЗА ТАБЛЕТКОЙ?</h1>
    <h2 class="hero-answer">ЕЁ НЕТ.</h2>
  </div>
  <div class="hero-mckinsey">
    <p>Хочешь красивый совет? Иди к McKinsey. Они нарисуют тебе 100 слайдов. Ты заплатишь 10 миллионов. Через год всё вернётся.</p>
    <p class="hero-stay">Хочешь понять, как на самом деле работают великие идеи управления? <strong>Оставайся.</strong></p>
  </div>
  <div class="hero-thinkers">
    <p>Мы просто снимаем слой консалтинговой пыли с идей Деминга, Тейлора, Богданова, Оно, Медоуз, Хапрова, Клаузевица...</p>
    <p class="hero-quote">«Сначала среда, потом требования». «Сложность управляется сложностью». «Любая система лжёт». Просто консультанты забыли это сказать.</p>
  </div>
  <div class="hero-cta">
    <a href="/scenarios/" class="btn btn-crisis">🔥 У МЕНЯ КРИЗИС</a>
    <a href="#system-map" class="btn btn-primary">🗺️ ХОЧУ ПОНЯТЬ СИСТЕМУ</a>
  </div>
</section>
```

**CSS (добавить в brutalist.css):**
```css
.hero { padding: var(--space-16) var(--space-8); text-align: center; max-width: 900px; margin: 0 auto; }
.hero-heading { font-family: var(--font-heading); font-weight: 900; font-size: var(--text-hero);
  text-transform: uppercase; letter-spacing: -0.02em; margin-bottom: var(--space-2);
  animation: strike-in 0.6s ease-out; }
.hero-answer { font-family: var(--font-heading); font-weight: 900;
  font-size: clamp(2rem, 6vw, 5rem); color: var(--color-accent);
  animation: strike-in 0.6s ease-out 0.2s both; }
.hero-mckinsey { margin: var(--space-8) 0; font-size: var(--text-lg); line-height: 1.8; }
.hero-stay { font-family: var(--font-heading); font-weight: 700; margin-top: var(--space-4); }
.hero-stay strong { color: var(--color-accent); }
.hero-thinkers { font-size: var(--text-base); color: var(--color-steel); margin: var(--space-6) 0; }
.hero-quote { font-style: italic; margin-top: var(--space-4); border-left: 3px solid var(--color-accent);
  padding-left: var(--space-4); color: var(--color-text); }
.hero-cta { display: flex; gap: var(--space-4); justify-content: center; margin-top: var(--space-12);
  flex-wrap: wrap; }

@keyframes strike-in {
  from { opacity: 0; transform: scale(1.08); }
  to { opacity: 1; transform: scale(1); }
}
```

**Playwright-тест:**
```js
// Story 14: Hero renders, animation plays, crisis button pulses
const page = await context.newPage();
await page.goto('http://localhost:3000');
const heroText = await page.evaluate(() => document.querySelector('.hero-heading')?.textContent || '');
if (!heroText.includes('ТАБЛЕТКОЙ')) throw new Error('Hero heading missing: ' + heroText);
// Answer text is red
const answerColor = await page.evaluate(() => {
  const el = document.querySelector('.hero-answer');
  return el ? window.getComputedStyle(el).color : null;
});
if (!answerColor || !answerColor.includes('rgb(220')) throw new Error('Answer not red: ' + answerColor);
// Two CTA buttons present
const ctaCount = await page.evaluate(() => document.querySelectorAll('.hero-cta .btn').length);
if (ctaCount !== 2) throw new Error('Expected 2 CTA buttons, got ' + ctaCount);
// Mobile: hero still readable
await page.setViewportSize({ width: 480, height: 800 });
const heroSize = await page.evaluate(() => {
  return parseInt(window.getComputedStyle(document.querySelector('.hero-heading')).fontSize);
});
if (heroSize < 24) throw new Error('Hero too small on mobile: ' + heroSize + 'px');
```

---

## Story 15: Main page — Archaeology section

**Что:** Секция «Мы — археологи управления» с цепочкой мыслителей и кнопкой «Весь архив».

**HTML для buildIndex:**
```html
<section class="section archaeology">
  <h2 class="section-title">МЫ — АРХЕОЛОГИ УПРАВЛЕНИЯ</h2>
  <p class="section-desc">Каждый инструмент Антименеджера — это раскопка. Мы находим изначальную идею великого мыслителя. Очищаем её от консалтинговой упаковки. И адаптируем к твоему конвейеру.</p>
  <div class="thinker-chain">
    <span>Шухарт → PDCA</span>
    <span>Деминг → Качество</span>
    <span>Оно → Уважение</span>
    <span>Богданов → Система</span>
    <span>Гастев → Культура</span>
  </div>
  <a href="/archive/" class="btn">🏛️ ВЕСЬ АРХИВ</a>
</section>
```

**CSS (добавить в brutalist.css):**
```css
.section { padding: var(--space-12) var(--space-8); max-width: 1100px; margin: 0 auto; }
.section-title { font-family: var(--font-heading); font-weight: 900; font-size: var(--text-2xl);
  text-transform: uppercase; letter-spacing: 0.05em;
  border-bottom: 3px solid var(--color-accent); display: inline-block;
  padding-bottom: var(--space-2); margin-bottom: var(--space-6); }
.section-desc { font-size: var(--text-lg); line-height: 1.7; max-width: 700px; margin-bottom: var(--space-6); }
.thinker-chain { display: flex; flex-wrap: wrap; gap: var(--space-3); margin: var(--space-6) 0; }
.thinker-chain span { font-family: var(--font-mono); font-size: var(--text-sm);
  border: 1px solid var(--color-steel); padding: var(--space-2) var(--space-4); }
```

**Playwright-тест:**
```js
// Story 15: Archaeology section renders, thinker chain visible, archive button links to /archive/
const page = await context.newPage();
await page.goto('http://localhost:3000');
const title = await page.evaluate(() => document.querySelector('.archaeology .section-title')?.textContent || '');
if (!title.includes('АРХЕОЛОГИ')) throw new Error('Archaeology section missing');
const chainCount = await page.evaluate(() => document.querySelectorAll('.thinker-chain span').length);
if (chainCount < 4) throw new Error('Thinker chain too short: ' + chainCount);
// Archive button links correctly
const archiveHref = await page.evaluate(() => {
  const btn = document.querySelector('.archaeology .btn');
  return btn ? btn.getAttribute('href') : null;
});
if (archiveHref !== '/archive/') throw new Error('Archive button href wrong: ' + archiveHref);
```

---

## Story 16: Main page — Weapons + Star map + Combat zones

**Что:** Секция «Это — оружие» с избранными статьями (без нумерации), звезда-карта (динамическая), зоны боевых действий.

**HTML для buildIndex:**
```html
<section class="section" id="weapons-section">
  <h2 class="section-title">ЭТО — ОРУЖИЕ. А НЕ ЕЩЁ ОДНА КНИГА</h2>
  <p class="section-desc">Антименеджер — это не метод. Это способ думать. Метод можно скопировать. Способ думать — нельзя.</p>
  <p class="section-desc">Разница простая: метод даёт тебе инструкцию. Способ думать даёт тебе критерий: «Как понять, что инструкция врёт».</p>
  <div class="weapon-grid">
    <!-- Populated dynamically: featuredWeaponsHtml -->
  </div>
  <a href="/arsenal/" class="btn btn-primary">🔫 ВЕСЬ АРСЕНАЛ</a>
</section>
```

**Код в buildIndex для генерации featured weapons (динамический, без нумерации):**
```js
const published = weapons.filter(w => w.status === 'published');
const featured = published.length > 0 ? published.slice(0, 4) : weapons.filter(w => w.status === 'review').slice(0, 4);
const featuredWeaponsHtml = featured.map(w => `
  <a href="/weapons/${w.slug}/" class="weapon-card">
    <div class="weapon-title">${w.title}</div>
    <div class="weapon-subtitle">${w.subtitle || ''}</div>
    ${w.zone ? `<span class="weapon-status">${zoneLabels[w.zone] || w.zone}</span>` : ''}
  </a>
`).join('');
```

```html
<section class="section" id="system-map">
  <h2 class="section-title">КАРТА СИСТЕМЫ</h2>
  <div class="map-container">${starSvg(scenarios, weapons)}</div>
</section>

<section class="section">
  <h2 class="section-title">ВЫБЕРИ СВОЙ УЧАСТОК ФРОНТА</h2>
  <div class="zone-grid">
    ${scenarios.map(s => {
      const zoneWeapons = s.weapons.map(id => weaponById(id)).filter(Boolean);
      return `
      <a href="/scenarios/" class="zone-card zone-${s.id}">
        <div class="zone-icon">${s.icon}</div>
        <div class="zone-title">${s.title}</div>
        <div class="zone-subtitle">${s.subtitle}</div>
        <span class="zone-count">${zoneWeapons.length}</span>
      </a>`;
    }).join('')}
  </div>
</section>
```

**Playwright-тест:**
```js
// Story 16: Weapons grid, star map, zone cards all visible. No numbering in featured cards.
const page = await context.newPage();
await page.goto('http://localhost:3000');
// Weapons grid has cards (dynamic count, not hardcoded)
const weaponCards = await page.evaluate(() => document.querySelectorAll('#weapons-section .weapon-card').length);
if (weaponCards < 1) throw new Error('Expected at least 1 featured weapon card, got ' + weaponCards);
// No weapon-number span in featured cards
const hasNumbers = await page.evaluate(() => !!document.querySelector('#weapons-section .weapon-number'));
if (hasNumbers) throw new Error('Numbering found in featured weapons — should be absent');
// Star map SVG renders
const svg = await page.evaluate(() => {
  const el = document.querySelector('#system-map svg');
  return el ? el.viewBox.baseVal.width : 0;
});
if (!svg) throw new Error('Star map SVG missing');
// 4 zone cards
const zones = await page.evaluate(() => document.querySelectorAll('.zone-card').length);
if (zones !== 4) throw new Error('Expected 4 zone cards, got ' + zones);
// Arsenal button exists (without hardcoded number)
const arsenalBtn = await page.evaluate(() => {
  const btn = document.querySelector('a[href="/arsenal/"]');
  return btn ? btn.textContent.includes('АРСЕНАЛ') : false;
});
if (!arsenalBtn) throw new Error('Arsenal link missing');
```

---

## Story 17: Main page — Remaining sections (Manifesto teaser, Diaries, HQ, Stats, Footer)

**Что:** Добавить в landing оставшиеся секции: тизер манифеста, полевые дневники, штаб, статистика.

**HTML для buildIndex:**
```html
<section class="section manifesto-teaser">
  <h2 class="section-title">МАНИФЕСТ ИМПЕРИИ РАЦИОНАЛЬНОГО</h2>
  <p class="section-desc">Это не просто слова. Это конституция Антименеджера.</p>
  <div class="manifesto-grid">
    <div class="manifesto-value"><span>1.</span> Люди и их потенциал над слепым исполнением инструкций</div>
    <div class="manifesto-value"><span>2.</span> Работающая и справедливая система над героизмом и авралами</div>
    <!-- ... up to 10 -->
  </div>
  <a href="/manifesto/" class="btn">📜 ЧИТАТЬ ПОЛНОСТЬЮ</a>
</section>

<section class="section">
  <h2 class="section-title">ПОЛЕВЫЕ ДНЕВНИКИ</h2>
  <p class="section-desc">Реальные истории с заводов.</p>
  <div class="case-grid">
    ${cases.slice(0, 3).map(c => `
      <a href="/cases/" class="case-card">
        <div class="case-headline"><span>⚔️</span>${c.title}</div>
        <div class="weapon-subtitle">${c.desc}</div>
        <div class="case-readtime">⏱ ${c.readtime || '5 минут'}</div>
      </a>
    `).join('')}
  </div>
  <a href="/cases/" class="btn">📖 ВСЕ ИСТОРИИ</a>
</section>

<section class="section hq-section">
  <h2 class="section-title">ВСТУПАЙ В ШТАБ</h2>
  <p class="section-desc">Это закрытый клуб партизан. Здесь не обсуждают теорию. Здесь разбирают боевые ситуации.</p>
  <p class="section-desc">⚡ Еженедельный разбор полётов · ⚡ Анонимные вопросы · ⚡ Реальные кейсы</p>
  <a href="https://t.me/..." class="btn btn-primary">💬 ВСТУПИТЬ В TELEGRAM</a>
</section>

<section class="section stats-section">
  <h2 class="section-title">СЕГОДНЯ В ОКОПЕ</h2>
  <div class="stats-grid">
    <div class="stats-item"><strong>2 847</strong><br>управленцев читают</div>
    <div class="stats-item"><strong>113</strong><br>внедрили «правило трёх вопросов»</div>
    <div class="stats-item"><strong>47</strong><br>вышли из кризиса за 90 дней</div>
  </div>
</section>
```

**CSS (добавить в brutalist.css):**
```css
.manifesto-value { font-size: var(--text-base); padding: var(--space-3) 0;
  border-bottom: 1px solid var(--color-steel); }
.manifesto-value span { color: var(--color-accent); font-family: var(--font-heading);
  font-weight: 700; margin-right: var(--space-2); }
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-6);
  margin-top: var(--space-6); }
.stats-item { text-align: center; padding: var(--space-6); border: 2px solid var(--color-steel); }
.stats-item strong { font-family: var(--font-heading); font-size: var(--text-3xl); color: var(--color-accent); display: block; margin-bottom: var(--space-2); }

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: 1fr; }
}
```

**Playwright-тест:**
```js
// Story 17: All remaining sections visible, links work, layout complete
const page = await context.newPage();
await page.goto('http://localhost:3000');
const sections = [
  '.manifesto-teaser', '.hq-section', '.stats-section'
];
for (const sel of sections) {
  const visible = await page.evaluate(s => !!document.querySelector(s), sel);
  if (!visible) throw new Error('Section missing: ' + sel);
}
// Manifesto link points to /manifesto/
const manifestoLink = await page.evaluate(() => {
  const el = document.querySelector('.manifesto-teaser a[href="/manifesto/"]');
  return !!el;
});
if (!manifestoLink) throw new Error('Manifesto link missing');
// 3 stats items
const statsCount = await page.evaluate(() => document.querySelectorAll('.stats-item').length);
if (statsCount !== 3) throw new Error('Expected 3 stats, got ' + statsCount);
// Mobile: stats stack
await page.setViewportSize({ width: 480, height: 800 });
const statsCols = await page.evaluate(() => {
  return window.getComputedStyle(document.querySelector('.stats-grid')).gridTemplateColumns;
});
if (statsCols !== '1fr' && !statsCols.startsWith('repeat(1')) throw new Error('Stats grid not 1-col on mobile');
```

---

## Story 18: Full responsive audit — every page, every breakpoint

**Что:** Playwright-тест, который проходит по всем страницам на 5 брейкпоинтах и проверяет отсутствие горизонтального скролла и обрезанного текста.

**Playwright-тест:**
```js
// Story 18: Full responsive audit
const breakpoints = [
  { name: '4K', width: 2560, height: 1440 },
  { name: 'Desktop', width: 1920, height: 1080 },
  { name: 'Laptop', width: 1024, height: 768 },
  { name: 'Tablet', width: 768, height: 1024 },
  { name: 'Mobile L', width: 480, height: 800 },
  { name: 'Mobile S', width: 375, height: 667 },
];
// URLs to test
const urls = [
  '/',
  '/manifesto/',
  '/archive/',
  '/arsenal/',
  '/scenarios/',
  '/weapons/mayatnik-upravleniya/',
  '/weapons/dva-tipa-upravleniya/',
  '/about/',
];

let failures = [];
for (const bp of breakpoints) {
  for (const url of urls) {
    const page = await context.newPage();
    await page.setViewportSize({ width: bp.width, height: bp.height });
    await page.goto('http://localhost:3000' + url, { waitUntil: 'networkidle' });
    // Check no horizontal overflow
    const overflow = await page.evaluate(() => {
      return {
        bodyOverflow: document.body.scrollWidth > window.innerWidth,
        scrollX: document.documentElement.scrollWidth > window.innerWidth,
      };
    });
    if (overflow.bodyOverflow || overflow.scrollX) {
      failures.push(url + ' @ ' + bp.name + ': horizontal overflow detected');
    }
    // Check red corner visible
    const corner = await page.evaluate(() => !!document.querySelector('.red-corner'));
    if (!corner) failures.push(url + ' @ ' + bp.name + ': red corner missing');
    // Check no console errors
    const errors = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
    await page.waitForTimeout(500);
    if (errors.length) failures.push(url + ' @ ' + bp.name + ': JS errors: ' + errors.join(', '));
    await page.close();
  }
}

if (failures.length) {
  console.error('Responsive audit failures:');
  failures.forEach(f => console.error('  ❌ ' + f));
  throw new Error(failures.length + ' responsive audit failure(s)');
}
console.log('✅ All ' + urls.length + ' pages pass all ' + breakpoints.length + ' breakpoints');
```

---

## Story 19: Animations — red flash, unwrap, reveal

**Что:** Добавить в brutalist.css оставшиеся анимации и добавить в common.js IntersectionObserver для reveal.

**CSS (добавить в brutalist.css):**
```css
/* Red flash on page transition */
@keyframes red-flash {
  0% { background-color: #0A0A0A; }
  50% { background-color: rgba(220, 38, 38, 0.06); }
  100% { background-color: #0A0A0A; }
}
body.flash-in { animation: red-flash 0.5s ease-out; }

/* Unwrap animation for thinker cards */
.thinker-card { position: relative; overflow: hidden; }
.thinker-card::after {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0;
  width: 6px; background: var(--color-steel);
  transition: width 0.3s, background 0.3s;
}
.thinker-card:hover::after { width: 100%; background: rgba(220, 38, 38, 0.1); }

/* Scroll reveal */
.reveal { opacity: 0; transform: translateY(24px); transition: opacity 0.6s, transform 0.6s; }
.revealed { opacity: 1; transform: translateY(0); }
.reveal-delay-1 { transition-delay: 0.1s; }
.reveal-delay-2 { transition-delay: 0.2s; }
.reveal-delay-3 { transition-delay: 0.3s; }
```

**JS (добавить в site/js/common.js или создать новый site/js/brutalist.js):**
```js
document.addEventListener('DOMContentLoaded', function() {
  // Red flash on page load
  document.body.classList.add('flash-in');
  setTimeout(() => document.body.classList.remove('flash-in'), 500);

  // Scroll reveal
  var els = document.querySelectorAll('.reveal');
  if (!els.length || !window.IntersectionObserver) {
    els.forEach(function(el) { el.classList.add('revealed'); });
    return;
  }
  var obs = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) { entry.target.classList.add('revealed'); obs.unobserve(entry.target); }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  els.forEach(function(el) { obs.observe(el); });
});
```

**Playwright-тест:**
```js
// Story 19: Animations work — red flash on load, reveal triggers on scroll
const page = await context.newPage();
await page.goto('http://localhost:3000');
// Red flash applied on load
let hasFlash = await page.evaluate(() => document.body.classList.contains('flash-in'));
if (!hasFlash) throw new Error('Red flash class missing on body');
// Wait for flash to remove
await page.waitForTimeout(600);
hasFlash = await page.evaluate(() => document.body.classList.contains('flash-in'));
if (hasFlash) throw new Error('Red flash class not removed after animation');
// Scroll reveal: check .reveal elements get .revealed after scrolling
const revealCount = await page.evaluate(() => document.querySelectorAll('.reveal').length);
if (revealCount > 0) {
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(1000);
  const revealedCount = await page.evaluate(() => document.querySelectorAll('.revealed').length);
  if (revealedCount === 0) throw new Error('No elements revealed after scroll');
}
```

---

## Story 20: Lighthouse audit + deploy

**Что:** Запустить Lighthouse для главной и страницы оружия. Убедиться: Performance ≥ 85, Accessibility ≥ 90, SEO ≥ 90. Затем деплой.

**Bash:**
```bash
# Install lighthouse if needed
npm install -g lighthouse
# Run on main page
lighthouse http://localhost:3000 --output=json --output-path=./lighthouse-main.json --chrome-flags="--headless"
# Run on weapon page
lighthouse http://localhost:3000/weapons/mayatnik-upravleniya/ --output=json --output-path=./lighthouse-weapon.json --chrome-flags="--headless"
```

**Playwright-тест (proxy для проверки метрик):**
```js
// Story 20: Quick metrics check (not full Lighthouse)
const page = await context.newPage();
await page.goto('http://localhost:3000');
// Check <title> not empty
const title = await page.evaluate(() => document.title);
if (!title) throw new Error('Title missing');
// Check meta description
const desc = await page.evaluate(() => {
  const el = document.querySelector('meta[name="description"]');
  return el ? el.content : '';
});
if (!desc) throw new Error('Meta description missing');
// Check images have alt (accessibility proxy)
const imgsWithoutAlt = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('img')).filter(i => !i.alt).length;
});
if (imgsWithoutAlt > 0) throw new Error(imgsWithoutAlt + ' images missing alt text');
// Check font-display: swap (performance proxy)
const fontDisplay = await page.evaluate(() => {
  const sheet = Array.from(document.styleSheets).find(s => s.href && s.href.includes('fonts'));
  if (!sheet) return 'no-fonts-sheet';
  try { return sheet.cssRules[0]?.style?.fontDisplay || 'no-rule'; }
  catch(e) { return 'cross-origin'; }
});
console.log('Font display: ' + fontDisplay);
```

**Deploy:**
```bash
cd site && .\deploy.ps1
```

---

## Execution Order (Stories 00→20)

| Story | Depends On | Build Required |
|-------|-----------|----------------|
| 00 | — | No (cleanup) |
| 01 | 00 | No (fonts only) |
| 02 | 01 | Yes (CSS + test HTML) |
| 03 | 02 | Yes (header component) |
| 04 | 02 | Yes (button styles) |
| 05 | 02 | Yes (corner + dividers) |
| 06 | 02 | Yes (weapon card styles) |
| 07 | 02 | Yes (zone + case cards) |
| 08 | 02 | Yes (star map) |
| 09 | — | No (data only) |
| 10 | 02+03 | Yes (base template + footer) |
| 11 | 09+10 | Yes (build.js + static pages) |
| 12 | 11 | Yes (weapon pages) |
| 13 | 12 | Yes (content restyle) |
| 14 | 11 | Yes (hero section) |
| 15 | 11 | Yes (archaeology section) |
| 16 | 08+11+12 | Yes (weapons + map + zones) |
| 17 | 11 | Yes (remaining sections) |
| 18 | 17 | No (audit only) |
| 19 | 14 | Yes (animations) |
| 20 | 18 | No (lighthouse + deploy) |

**Правило:** После каждой Story, требующей Build, запускать:
```bash
node site/build.js
npx serve site/dist -p 3000
# (если сервер уже запущен — просто перезагрузить страницу в Playwright)
```

## Validation Gate (после Story 20)

```bash
# 1. Build passes
node site/build.js | findstr "✅"

# 2. All 31 pages exist in dist/
$pages = @(Get-ChildItem site/dist -Recurse -Filter index.html).Count
if ($pages -lt 31) { throw "Expected >=31 pages, got $pages" }

# 3. No broken links (optional: linkchecker)
# 4. Deploy
.\deploy.ps1
```
