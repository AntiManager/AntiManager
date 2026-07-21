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

1. Установить Node.js (npx)
2. Установить Obsidian + remotely-save
3. Синхронизировать vault (remotely-save стянет всё, включая .kilo/)
4. Скопировать глобальный конфиг (подставь свой путь до vault):
   `powershell
   New-Item -ItemType Directory -Path \"$env:USERPROFILE\.config\kilo\" -Force
   Copy-Item \"$env:USERPROFILE\Documents\{{VAULT_DIR}}\.kilo\globalsync.jsonc\" \"$env:USERPROFILE\.config\kilo\kilo.jsonc\"
   `
5. Готово.
