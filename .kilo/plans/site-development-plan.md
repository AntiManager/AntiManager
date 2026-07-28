# План сайта antimanager.pro

> Актуально на 28.07.2026. Бруталистский ребрендинг + UI/UX-фиксы завершены и задеплоены.

---

## 1. Концепция

**Цель:** Показать руководителям производств системность управления через 4 зоны боевых действий (Crisis, Team, Changes, System).

**Дизайн:** Брутализм — чёрно-бело-красная палитра, шумовая текстура, конструктивистские приёмы.

**Навигация:** Динамическая SVG-карта зон (star map) на главной. 22 статьи-«оружия» без нумерации.

## 2. Статус (28.07.2026)

### Проделано (июль 2026)

- [x] **Бруталистский ребрендинг** — `brutalist.css` (400 строк), `build.js` переписан под новую архитектуру
- [x] **Данные**: `weapons.json` (23 статьи), `scenarios.json` (4 зоны), `thinkers.json` (9 мыслителей + фото)
- [x] **Страницы**: landing, manifesto, archive, arsenal (с фильтрами), scenarios, cases, headquarters, about, 404, privacy
- [x] **22 страницы оружия** — каждая с шаблоном (зона, контент, мыслитель с фото, related, download-CTA)
- [x] **Интерактивные виджеты**: диагностика Run/Change (гл. 21), Pre-Mortem (гл. 16)
- [x] **SEO**: Schema.org (Article, BreadcrumbList, WebSite), OG (article:section, article:published_time), canonical, sitemap, robots.txt
- [x] **UI/UX-фиксы (28.07)**: skip-link + focus-visible + reduced-motion (A11y), touch targets 44px, crisis CTA shortcut, responsive breakpoints (640px/1024px), hover guards, download CTA text, фото мыслителей, hamburger menu, scroll-to-top, word-break
- [x] **Playwright**: 66 e2e-тестов (mobile/tablet/desktop), все проходят

### Следующий приоритет

- [ ] Контент глав: 02 (Сложность), 04 (PDCA), 06 (Процессы), 11 (Культура)
- [ ] Интерактивные инструменты для написанных глав
- [ ] Полнотекстовые страницы кейсов
- [ ] Скачиваемые материалы (PDF чек-листов)
- [ ] Lighthouse ≥ 90

## 3. Технологический стек

| Технология | Роль |
|---|---|
| Vanilla HTML/CSS/JS | Без фреймворков |
| node build.js | Сборка страниц из компонентов |
| CSS Custom Properties | Дизайн-токены (ch: 0A0A0A, red: DC2626, steel: 6B7280) |
| Golos Text + PT Serif + JetBrains Mono | Типографика (woff2, Cyrillic/Latin split) |
| SVG (data-driven) | Динамическая карта зон (star map) |
| nginx:alpine (Docker) | Раздача статики |
| Caddy (Docker) | HTTPS termination, reverse proxy |
| Playwright | e2e-тесты 3 вьюпорта |

## 4. Архитектура

```
AntiManager/
├── Фото_мыслителей/          ← фото мыслителей (копируются в dist/)
├── manifesto-ru.md / -en.md  ← манифесты
├── site/
│   ├── src/
│   │   ├── components/       ← header.html, footer.html
│   │   ├── templates/        ← base.html, og-image.svg
│   │   ├── data/             ← weapons.json, scenarios.json, thinkers.json, cases.json
│   │   └── content/          ← HTML-контент 22 статей
│   ├── build.js              ← сборка → dist/
│   ├── css/brutalist.css     ← дизайн-система (400 строк)
│   ├── css/fonts.css         ← @font-face (10 woff2)
│   ├── js/brutalist.js       ← flash, reveal, download, menu, scroll-top
│   ├── fonts/                ← woff2 (Golos Text, PT Serif, JetBrains Mono)
│   ├── tests/                ← ux-critical.spec.js (66 тестов)
│   ├── deploy/               ← deploy.ps1, nginx.conf
│   └── dist/                 ← собранный сайт (gitignored)
```

Чистые URL: `/weapons/slug/` → `dist/weapons/slug/index.html`

## 5. Деплой

```powershell
cd site
node build.js
.\deploy.ps1      # Сборка + SCP + chmod + Docker restart
```

Или `.\deploy.ps1 -SkipBuild` если dist уже собран.

После деплоя CSS/JS кешируются на 7 дней с `must-revalidate`. Cache-busting: `?v=YYYYMMDD` в URL стилей/скриптов.

## 6. Следующие итерации

1. **Контент глав** — переработать .md → HTML: 02, 04, 06, 11, 13
2. **Интерактивные инструменты** — для каждой готовой главы свой виджет
3. **Кейсы** — полнотекстовые страницы полевых дневников
4. **PDF-материалы** — чек-листы и шаблоны для загрузки
5. **Производительность** — Critical CSS inline, Lighthouse ≥ 90
6. **Star map interactive** — кликабельные лучи → статьи зоны
