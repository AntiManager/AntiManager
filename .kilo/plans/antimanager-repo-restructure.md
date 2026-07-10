# План реструктуризации репозитория AntiManager

> Репозиторий: https://github.com/AntiManager/AntiManager + GitVerse
> Назначение: публичное лицо проекта УПС

---

## 1. Концепция

AntiManager — не свалка файлов и не архив других репозиториев.
AntiManager — хаб, который содержит:

1. **Исходники сайта** antimanager.ru (site/)
2. **Готовые статьи** в markdown (articles/)
3. **Справочные материалы** в 1 экземпляре (research/)
4. **README** со ссылками на всё остальное

Всё остальное (Python-утилиты, платформа ЭСЗ, бэкенды) — в своих репозиториях.
AntiManager только ссылается на них.

---

## 2. Текущее состояние (проблемы)

| Файл | Проблема |
|---|---|
| 6 статей .md | старые версии, в vault актуальные |
| 5 APQC-файлов | дубликаты |
| git_comand.md | личное — не должно быть публично |
| README.md | сломанные ссылки, нет описания |

---

## 3. Целевая структура

`
AntiManager/
├── README.md           ← хаб: описание, ссылки на сайт, GitHub-репозитории, Telegram
├── site/               ← исходники antimanager.ru (главный контент репо)
│   ├── index.html
│   ├── catalog.html
│   ├── books/
│   ├── css/ + js/
│   └── ...
├── articles/           ← готовые статьи (только финальные версии)
│   ├── 00_Маятник_управления.md
│   ├── 01_Manifestum.md
│   └── ...
├── research/           ← справочники (по 1 экз.)
│   └── APQC_PCF_7.4_ru.xlsx
└── docs/               ← документация проекта
    └── ARCHITECTURE.md
`

---

## 4. Статус готовности статей

| Статья | Статус | Готово к выкладке |
|--------|--------|-------------------|
| 21 | published | ✅ да |
| 22 | review | ❌ (после публикации) |
| 20 | review | ❌ |

**Правило:** в articles/ попадают только статьи со статусом published.

## 5. Что AntiManager НЕ содержит (только ссылки)

| Проект | Репозиторий | Как указать в README |
|---|---|---|
| Цифровая платформа (ЭСЗ) | github.com/.../factory-system | Ссылка в README |
| Генератор Mermaid | github.com/.../BusinessProcessMermaidGenerator | Ссылка в README |
| APQC-фронтенд | github.com/.../apqc-pcf-frontend | Ссылка в README |
| BPM-решатель | github.com/.../BPM_solve | Ссылка в README |
| Перевод Excel | github.com/.../Excell_Translator | Ссылка в README |
| Остальные утилиты | свои репозитории | Ссылка в README |

---

## 5. План миграции (8 шагов, ~15 минут)

| № | Действие | Команда |
|---|---|---|
| 1 | Удалить git_comand.md | git rm git_comand.md |
| 2 | Удалить старые статьи | git rm *.md (кроме README) |
| 3 | Удалить дубликаты APQC, оставить 1 | git rm K0147* APQC* затем mkdir research; mv ... research/ |
| 4 | Создать папки | mkdir site articles docs |
| 5 | Скопировать сайт из vault | cp -r ../"VAULT_DIR/Книга/00_Сайт/"* site/ |
| 6 | Написать README | (см. шаблон ниже) |
| 7 | Закоммитить | git add . && git commit -m "restructure: site + references" |
| 8 | Запушить | git push origin main |

---

## 6. Шаблон README

`markdown
# AntiManager

Система управления производственными предприятиями:
методологии, диагностики, интерактивные инструменты.

🌐 **Сайт:** [antimanager.ru](https://antimanager.ru)

---

## Состав проекта

| Компонент | Описание | Ссылка |
|---|---|---|
| Сайт | Интерактивные презентации, тесты, книги | site/ |
| Статьи | Готовые главы книги | rticles/ |
| Цифровая платформа | Supabase + n8n — операционный контур | [factory-system](ссылка) |
| Генератор Mermaid | Диаграммы бизнес-процессов | [mermaid-generator](ссылка) |
| ... | ... | ... |

## Автор

Евгений Богданов — COO, 20 лет в промышленности.
Telegram: [@...](ссылка)

## Лицензия

MIT
`

---

## 7. Критерий готовности

- git_comand.md отсутствует
- В корне репо: README.md, папки site/ articles/ research/ docs/
- site/ содержит рабочий antimanager.ru
- README содержит ссылки на все связанные репозитории и Telegram
- В репо нет дубликатов и мусора

