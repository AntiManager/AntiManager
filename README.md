# AntiManager

**Система управления производством** — интерактивная книга-сайт для руководителей производства.

🌐 https://antimanager.pro

## О проекте

22 главы, 22 инструмента, 10 кейсов — единая связанная система управления производством. Пять контуров: Стратегия, Процессы, Информация, Люди, Адаптация. Каждая глава содержит принцип модели, таблицу/схему, тезисный отрывок и интерактивный диагностический виджет.

## Технологии

- **Vanilla HTML/CSS/JS** — без фреймворков
- **Node.js** build pipeline — статическая генерация из шаблонов и JSON-данных
- **Playwright** — UX-тесты (3 вьюпорта, 16 тестов × 3 = 48)
- **Self-hosted шрифты** — Inter + Manrope (woff2, cyrillic/latin)
- **Классовая тёмная тема** — без JS-переключения CSS-переменных

## Структура

```
build.js          # Статический билдер
src/
  content/        # HTML-части глав (lite-контент)
  data/           # chapters.json, tools.json, cases.json
  templates/      # base.html, chapter.html
  components/     # header.html, sidebar.html, footer.html
css/              # Стили (дизайн-токены, тёмная тема, адаптив)
js/               # Интерактив (карта, виджеты, модалки, сайдбар)
fonts/            # Inter + Manrope woff2
tests/            # Playwright UX-тесты
deploy/           # nginx.conf, скрипты деплоя
```

## Разработка

```bash
npm install        # Установка зависимостей (только dev — Playwright)
node build.js      # Сборка сайта в dist/
npx serve dist     # Локальный просмотр
npm test           # Запуск Playwright-тестов
```

## Деплой

```bash
.\deploy.ps1       # Деплой на VPS (scp + ssh)
```

## Лицензия

Проприетарная. Все права защищены. См. [Manifestum Imperii Rationalis](https://antimanager.pro/about/) — манифест рационального управления.

---

Также в репозитории: черновики статей и хронология эволюции управления (см. файлы `.md` в корне).
