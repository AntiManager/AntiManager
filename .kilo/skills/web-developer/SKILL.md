---
name: web-developer
description: Разработка сайта antimanager.ru — vanilla HTML/CSS/JS, дизайн-система, производительность
---

# Скилл: web-developer

## Технологии
- Vanilla HTML/CSS/JS (без фреймворков)
- CSS Custom Properties (дизайн-токены)
- CSS Nesting (нативный)
- CSS Container Queries (адаптив карточек)
- Mermaid.js / Chart.js через CDN

## Дизайн-система (common.css)

`css
:root {
  --color-bg: #F5F7FA;
  --color-bg-card: #FFFFFF;
  --color-text: #1A2C3E;
  --color-text-secondary: #4A5B6E;
  --color-accent: #E85D04;
  --color-accent-hover: #c44d02;
  --color-border: #E2E8F0;
  --font-sans: 'Inter', sans-serif;
  --font-heading: 'Manrope', sans-serif;
  --radius-card: 20px;
  --shadow-card: 0 8px 20px rgba(0,0,0,0.05);
}
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #0F1A24;
    --color-bg-card: #1E2A3A;
    --color-text: #E2E8F0;
    --color-accent: #FF8C32;
  }
}
`

Все страницы используют эти переменные. Новые цвета — только через переменные.

## Шаблон страницы книги (book-06.html)

Каждая страница книги = book-template.html:

`
Hero (header + заголовок + тезис)
  → секция концепций (grid карточек → клик → модалка)
  → интерактивный инструмент (тест/калькулятор)
  → блок «Для кого»
  → скачивание PDF (заглушка)
  → footer
`

## Интерактивные инструменты

- Один вопрос на экран. Progress bar (aria-valuenow).
- Back-кнопка (разрешить переосмыслить).
- Результат: не оценка, а профиль/рекомендация.
- JS-виджеты через requestAnimationFrame (не блокировать поток).

## Адаптивность

- Mobile-first через container queries, @media только для layout-обёрток
- Семантическая разметка, aria-атрибуты, focus-visible

## Производительность

- preload шрифтов Inter + Manrope
- Явные width/height для Mermaid-диаграмм (CLS < 0.1)
- Lighthouse: Performance > 90, Accessibility > 90, SEO > 90

## Структура файлов

- books/book-XX.html — страницы глав
- css/common.css — всё (одним файлом, минифицировать не обязательно)
- js/common.js — общее, js/interactive/ — виджеты
- images/, pdf/, downloads/
