Карта хранилища в Roadmap/Дорожная карта доработок.md.
План сайта в .kilo/plans/site-development-plan.md.
План репозитория в .kilo/plans/antimanager-repo-restructure.md.

Скиллы:
- web-developer — дизайн-система, шаблон страницы, производительность
- content-publisher — перенос Obsidian-статей в HTML
- book-writing — редактура статей
- vault-commander — аудит хранилища (устаревший, см. vault-indexer)
- vault-indexer — полная инвентаризация vault (структура, связи, здоровье)
- site-designer — дизайн и UX сайта antimanager.pro
- diagram-architect — Mermaid-диаграммы
- management-research — исследование концепций

MCP (включены постоянно):
- obsidian — пакетная обработка заметок, чтение/запись vault
- web-search — поиск референсов
- github — коммиты/пуши, деплой

---

## Настройка на новом ПК

1. Установить Node.js, Python, Obsidian + remotely-save
2. Клонировать репо: `git clone https://github.com/AntiManager/AntiManager`
3. Скопировать `.kilo/kilo.json.example` → `.kilo/kilo.json`, подставить пути
4. Синхронизировать vault (remotely-save стянет только контент)
5. Готово — vault чистый, конфиг в репо

---

## Протокол безопасности (приоритет: абсолютный)

1. **Бекап перед изменением.** Любая операция записи в файлы начинается с бекапа в $env:TEMP\kilo\backups\дата\`n2. **PowerShell — только для ASCII и простых операций.** Кириллицу обрабатывать через Python (ftfy).
3. **Верификация.** После каждого изменения — проверка результата. Если алгоритм не дал ожидаемого результата — откат.
4. **Не пачками.** Один файл → проверить → закоммитить. Без массовых apply.
