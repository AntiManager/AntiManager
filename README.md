# AntiManager

**Система управления производством** — интерактивная книга-сайт для руководителей производства.

🌐 [antimanager.pro](https://antimanager.pro) | 📖 [Манифест (RU)](manifesto-ru.md) | 📖 [Manifesto (EN)](manifesto-en.md)

> Мы — инженеры человеческих управленческих систем, архитекторы порядка и гаранты справедливости. Наша задача — не контролировать людей, а проектировать социальные машины, которые раскрывают потенциал каждого.
>
> *Из [Manifestum Imperii Rationalis](manifesto-ru.md)*

## О проекте

Главы, инструменты и кейсы — единая связанная система управления производством в пяти контурах:

| Контур | Главы | Фокус |
|--------|-------|-------|
| **Стратегия** | 00, 05, 11, 15 | Маятник управления, каскадирование целей, культурный код, живой завод |
| **Процессы** | 02, 03, 06, 07, 13 | Сложные системы, системная динамика, процессы, OEE, 12 рычагов |
| **Информация** | 08, 19 | Нервная система компании, цифровой двойник |
| **Люди** | 09, 10, 12, 14, 20, 21 | Бей-беги-замри, ситуационное развитие, анти-тайм-менеджмент, живая система, выученная беспомощность, Run/Change |
| **Адаптация** | 04, 16, 17, 18, 22 | PDCA, хаос, лестница ошибок, антикризис, траектория |

Книгу дополняет библиотека лонгридов [`/articles/`](https://antimanager.pro/articles/) — стратегия, экономика, управление, цифровизация.

## Технологии

- Vanilla HTML/CSS/JS — без фреймворков
- Статическая генерация через Node.js (`site/build.js`)
- Self-hosted шрифты: Golos Text, PT Serif, JetBrains Mono (woff2, Cyrillic/Latin split)
- Бруталистская дизайн-система: чёрно-красно-белая палитра, шум
- Тесты сборки на Node (`node --test`) + Playwright e2e (несколько вьюпортов × тест-сьюты)
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
    templates/       # base.html, og-image.svg/png
    data/            # weapons, articles, article-topics/series, materials, chapters, tools, thinkers, cases, scenarios
    content/         # лендинги «оружия» + contact.html
    content/full/    # полные тексты статей (/full/)
    content/articles/# лонгриды библиотеки «Статьи» (/articles/)
    content/genome/  # раздел «Геном завода»
    lib/             # escape.js
  css/               # brutalist.css, fonts.css
  js/                # brutalist.js, contact.js
  fonts/             # Golos Text, PT Serif, JetBrains Mono (woff2)
  materials/         # PDF статей и авторские дополнительные материалы
  scripts/           # render-og.js, render-pdf.js, verify-deploy.ps1
  tests/             # Playwright e2e-тесты
  unit/              # unit-тесты сборки (node --test)
  feedback/          # микросервис формы обратной связи (Python)
  deploy/            # nginx.conf
  deploy.ps1         # деплой на VPS
  dist/              # Build output (gitignored)
```

## Разработка

```bash
cd site
npm install
node build.js      # Сборка в dist/
npx serve dist     # Локальный просмотр
npm test           # unit + Playwright
npm run test:unit  # только unit
npm run test:e2e   # только Playwright
.\deploy.ps1       # Деплой на VPS
```
