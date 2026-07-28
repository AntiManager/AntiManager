# AntiManager

**Система управления производством** — интерактивная книга-сайт для руководителей производства.

🌐 [antimanager.pro](https://antimanager.pro) | 📖 [Манифест (RU)](manifesto-ru.md) | 📖 [Manifesto (EN)](manifesto-en.md)

> Мы — инженеры человеческих управленческих систем, архитекторы порядка и гаранты справедливости. Наша задача — не контролировать людей, а проектировать социальные машины, которые раскрывают потенциал каждого.
>
> *Из [Manifestum Imperii Rationalis](manifesto-ru.md)*

## О проекте

22 главы, 22 инструмента, 10 кейсов — единая связанная система управления производством в пяти контурах:

| Контур | Главы | Фокус |
|--------|-------|-------|
| **Стратегия** | 00, 05, 11, 15 | Маятник управления, каскадирование целей, культурный код, живой завод |
| **Процессы** | 02, 03, 06, 07, 13 | Сложные системы, системная динамика, процессы, OEE, 12 рычагов |
| **Информация** | 08, 19 | Нервная система компании, цифровой двойник |
| **Люди** | 09, 10, 12, 14, 20, 21 | Бей-беги-замри, ситуационное развитие, анти-тайм-менеджмент, живая система, выученная беспомощность, Run/Change |
| **Адаптация** | 04, 16, 17, 18, 22 | PDCA, хаос, лестница ошибок, антикризис, траектория |

## Технологии

- Vanilla HTML/CSS/JS — без фреймворков
- Статическая генерация через Node.js (`site/build.js`)
- Self-hosted шрифты: Golos Text, PT Serif, JetBrains Mono (woff2, Cyrillic/Latin split)
- Бруталистская дизайн-система: чёрно-красно-белая палитра, шум
- Playwright e2e-тесты (3 вьюпорта × 22 тест-сьюта = 66 тестов)
- Docker: nginx:alpine + Caddy на VPS

## Структура

```
Фото_мыслителей/     # Фотографии мыслителей (копируются в dist/images/thinkers/)
manifesto-ru.md      # Манифест (русский)
manifesto-en.md      # Manifesto (English)
site/                # Код и деплой сайта
  build.js           # Статический билдер
  src/
    components/      # header, footer (HTML-компоненты)
    templates/       # base.html, og-image.svg
    data/            # weapons.json, scenarios.json, thinkers.json, cases.json
    content/         # HTML-контент 22 глав
  css/               # brutalist.css, fonts.css
  js/                # brutalist.js (flash, scroll-reveal, menu, scroll-top)
  fonts/             # Golos Text, PT Serif, JetBrains Mono (woff2 × 10)
  tests/             # Playwright (ux-critical.spec.js — 66 тестов)
  deploy/            # deploy.ps1, nginx.conf
  dist/              # Build output (gitignored)
```

## Разработка

```bash
cd site
npm install
node build.js      # Сборка в dist/
npx serve dist     # Локальный просмотр
npm test           # Playwright тесты
.\deploy.ps1       # Деплой на VPS
```
