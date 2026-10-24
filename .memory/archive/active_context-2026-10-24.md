# AntiManager — Active Context
> Updated: 2026-10-22 · SEO-пакет задеплоен и закоммичен (?v=20261022a, 78 URL, IndexNow 202); Линейные системы — база 60 компаний.

## State
- **SEO (2026-10-22):** сторонний отчёт опровергнут (sitemap/robots/хостинг/индексация Google — факты неверны; причина — нет регистрации в Вебмастере/GSC). Внедрён техпакет: verification meta через env, IndexNow с ключом и деплой-хуком, нормализация title/description. Добавлена тема `practice` и 5 прикладных статей (5S, OEE, хронометраж, Lean, KPI); ссылка «Практика» в подвале. Правки ревью внесены. Unit 22/22, Playwright 228/228. **Задеплоено 2026-10-22** (`?v=20261022a`, sitemap 78 URL, IndexNow HTTP 202, verify-deploy 6/6); verification-коды пусты — meta не выводится до регистрации в Вебмастере/GSC.
- **Client meeting kit (2026-10-21):** `Приложение-формы-артефактов` and `Экспресс-аудит-ПС` now have landscape `.docx`; new `Вопросы-собственнику.md/.docx` — 63 questions in 7 blocks, 17 marked ★, meeting plan and summary template. `КАБЭКС.md` updated. Vault files are outside git; docx via pandoc + python-docx.
- **Vault layout (2026-10-21):** universal docs in `Методология ПС/` (`Карточки-систем.md`, `Проектная-модель.md`, `Индекс-методологии.md`); client docs in `Заказчики/КАБЭКС/` (`Проект_диагностики.md`, `Карта-систем-собственнику.md/.docx`, `Приложение-формы-артефактов.md`, `Экспресс-аудит-ПС.md`, `КАБЭКС.md`). `Аудит ПС/` and `Библиотека процессов/` stay top-level. Vault root now holds only unrelated personal notes.
- **Client editions (2026-10-21):** `Приложение-формы-артефактов` stripped of preambles, provenance and internal paths (−24%); `Экспресс-аудит-ПС` is a standalone client copy of the express checklist (scale + 40 criteria + summary, no base ids or cross-links). Index `КАБЭКС.md` records provenance and the drift rule (universal note stays the source).
- **Methodology set (vault, outside git):** 14 system cards (all 12 fields, S14 no longer carries a 13th field) + full checklist 132 criteria / 7 blocks (`version: "1.1"`) + express 40 (unchanged, blocks 1–6 only) + diagnostics doc with 14 systems. Cards use base ids `1.1–6.18` / `7.1–7.12`; FPY, COQ, KPI-passport, master data are marked «вне полного чек-листа».
- **Project model (vault `Методология ПС/`):** `Проектная-модель.md` — separate detailed document (6 execution types, A–G effect classes, lifecycle/ТПР, handover/benefits, portfolio rules, 13×6 system interface). Cards only reference it; appendices A–D removed from `Карточки-систем.md`.
- **Terminology (2026-10-21):** canonical term is **ТПР / точка принятия решения** (not «ворота»); replaced across the whole vault incl. artifact codes, КТК artifacts and `PLAN-04`. Do not reintroduce «ворота» for project decision points.
- **Client appendix (vault `Заказчики/КАБЭКС/`):** `Приложение-формы-артефактов.md` now carries filled examples from library artifacts for `Ф-КТК`, `Ф-ПР`, `Ф-СРС`, `Ф-KPI`, `Ф-БП` (21 groups incl. `PRJ`), `Ф-СХ`; no empty tables.
- **Process library (vault `Библиотека процессов/`):** 21 groups / 83 processes / 259 subprocesses / 1041 operations. New `PRJ` group (4 processes, owner ГД); `T0.1` §T1.7 records the additive extension. `PRJ` has no `## Потоки (Flow Links)` table yet — next flow tranche.
- **Checkers:** `check_ps_audit.py` (132/7, pinned fingerprint of `1.1–6.18`) → 0/0; `check_system_cards.py` (14 cards, 12 fields each, ids, codes, orphans, no project appendices, S14 model reference) → 0; `check_artifacts.py` on the **library root** (`<vault>\Библиотека процессов`) → OK, 26 pre-existing warnings; `token_scan` on `library\artifacts` → 0.
- **Systems map (2026-10-21):** `/genome/systems/` published from the vault cards via `gen_systems_page.py` (14 × 12 fields, summary, blank template); owner doc `Заказчики/КАБЭКС/Карта-систем-собственнику.md/.docx`; template `materials/ps-systems-map/`. **Deployed 2026-10-21** (live 200 verified); committed in `a0d06a3`.
- **PS express audit (`/genome/audit/`):** untouched by this plan (express hash, generator hash, XLSX hash verified unchanged).
- **Articles:** 40, 41, 50–55 and practice 60–64 published; unit **22/22**, Playwright **228/228**, PDF 31; live `?v=20261022a` (SEO package deployed 2026-10-22).
- **Git:** Release A–C + docs cleanup + systems map (`a0d06a3`) pushed 2026-10-21. Vault-split change set committed 2026-10-21 (repo side only; vault files are outside git). SEO + practice change set committed and pushed 2026-10-22.
- **Линейные системы (2026-10-22):** новый заказчик в vault `Заказчики/Линейные-системы/` (ООО + ИП Санников; бренд ROSCA, `rosca.linear-tech.ru`). Создан рабочий комплект: компания, экономика, рынок/сегменты, производство, продажи/воронка, диагностика, план погружения, данные 1С, источники, база клиентов. Первый транш базы: **60 компаний** (A–E, акцент вне Урала, Fabricators.ru), CSV + MD. Следующая сессия: наполнение базы до 100–150 (ИНН/контакты/статус) и маркетинговое позиционирование ROSCA. Resume: `Заказчики/Линейные-системы/ЛС-Следующая-сессия.md`. **Продуктовая база (22.10):** `ЛС-Продукты.md`, `ЛС-Продукты-Дистрибуция.md` (17 товарных групп), `ЛС-Продукты-Производство.md` (ROSCA), `ЛС-Позиционирование-и-маркетинг.md`, `ЛС-Маркетинг-анализ.md`; следующий шаг — снять противоречия производства (технология, опыт, длина, две цены), проверить форму/Директ, сделать бенчмарк 10 SKU + 10 звонков.

## Next
1. **Регистрация в поисковиках (следующая сессия):** зарегистрировать сайт в Яндекс.Вебмастере и Google Search Console, получить коды, вписать `YANDEX_VERIFICATION` / `GOOGLE_VERIFICATION` в `.env`, передеплоить (meta + HTML-файл), подтвердить, отправить sitemap; baseline через 2–4 недели. После любого деплоя IndexNow запускать вручную, если `caddy reload` оборвал скрипт (`cd site; npm run indexnow`). Next semantic tranche: Taylor, SMED, TPM, FPY; expand short weapon descriptions.
2. **Линейные системы:** следующая сессия — обогатить базу (Checko/Dadata/2GIS, 1С, hh/тендеры) до 100–150 компаний, собрать топ-30 и 10 звонков; затем позиционирование ROSCA (ICP A/B/E, оффер, доказательства, возражения, лендинг, контент-план, KPI). Старт: `ЛС-Следующая-сессия.md`; база: `ЛС-База-клиентов-РФ.md/.csv`. **Продукты (22.10):** knowledge base собрана, следующий шаг — бенчмарк 10 SKU, 10 звонков, 3 оффера A/B/E и маркетинговый план.
3. Optional: regenerate the client `Экспресс-аудит-ПС.md` after any change to the universal v3.0 checklist (it is a snapshot; 40/40 rows currently identical modulo base ids).
4. Process-library: author `PRJ` flow links (`author_*_flows.py` pattern), then Phase 2 T2.6 tranche 2 — `MFG-02/03`, then `MFG-04/05`.
5. PS-audit: human blind-scoring of 5 criteria; publish only via a separate plan.
6. Editorial: DRAFT series 30–35 before `/full/`.

## Open cosmetic
- «Штаб»/club framing; hero CTA → `#offer`; README contours 22 vs weapons 23.
- Card content defects not covered by the plan: master data is now scoped (S01 planning vs S13 registry), school of masters and crane/fire artifacts carry explicit «совместно с» marks; remaining: S03 5S target (≥4.0 monthly) and S05 6–15 min read as level 4, not 3; S11 target state still describes a gap; S02 lists 4 QUAL processes without artifacts; S06 omits `HRP-01-05/-07`.

## Hot rules
- Skills 8 / commands 10 / agents 2; `/check-site` = `npm test`.
- Obsidian MCP writes on Cyrillic paths are broken — use `Write`/`Edit` + Python (`.kilo/AGENTS.md` §7).
- `check_artifacts.py` takes the **library root**, not the vault root.
- Data SSOT: `articles.json` + topics + series; only `published` renders; tests derive from data.
- Every article `.md` needs title block + `---`; no Mermaid — tables/lists.
- `render:pdf` two-pass; deploy may time out on Caddy reload — verify live.
- History → `.memory/archive/`.
