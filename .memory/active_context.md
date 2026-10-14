# AntiManager — Active Context
> Updated: 2026-10-14 · Feedback form `/contact/` → Telegram microservice built & tested locally (NOT deployed)

## Session done — Customer feedback form → Telegram (2026-10-14, local only)
- New `/contact/` page (static partial `src/content/contact.html` + `js/contact.js`, `brutalist.css` §CONTACT) with a form posting **same-origin** `POST /api/feedback`. Offer CTAs on `/genome/` and `cta-band` now open `/contact/?pack=express|process|library|pilot`; footer gained «Связаться». `/privacy/` rewritten (FZ-152: feedback data, consent, withdrawal).
- Backend: `site/feedback/` microservice (Python **stdlib only**, `server.py` + `Dockerfile` + `deploy.ps1` + `tests/`). nginx `location = /api/feedback` proxies to the `antimanager-feedback` container on `vps_shared`. Token stays server-side only (`$REMOTE_DIR/feedback.env`, `chmod 600`).
- **Evidence:** build OK; unit **11/11**; Playwright **135/135**; python `unittest` **20/20**. Token/bot-id absent from the repo (`rg AAF1kAa|8704688877` → 0).
- **Review (`/review uncommitted`, 2026-10-14) + fixes:** added `__pycache__/`·`*.pyc` to `.gitignore` (pyc would otherwise be committed); nginx now overwrites `X-Forwarded-For` with `$remote_addr` (was `$proxy_add_x_forwarded_for`, which kept a client-spoofable value → rate-limit bypass if the port is ever exposed); `server.py` rate-limiter now sweeps idle keys; `deploy.ps1` verifies the container is actually running after `docker run -d` (a crash-loop from an empty env returned exit 0); 5 new service tests (oversized body, invalid JSON, non-object payload, unknown path, invalid requests don't consume the limit); README/.env.example point at `$REMOTE_DIR/feedback.env`. Deferred (documented): nginx static-upstream fragility — restarting nginx while the container is down fails `nginx -t`; left as-is per the documented deploy ordering.
- **Deploy is PENDING (blocker):** needs (a) a **rotated** bot token (the old one was pasted in chat), (b) the real `TELEGRAM_CHAT_ID` from `getUpdates` (owner must `/start` the bot; `8704688877` is the **bot id**, NOT the chat id), (c) creating `$REMOTE_DIR/feedback.env`, then `site/feedback/deploy.ps1` + `site/deploy.ps1`.
- **Open (confirm):** other `t.me/antimanager` links left as-is — `build.js` landing CTA (201), JSON-LD `sameAs` (214), `/headquarters/` + landing crisis CTA (558/658), `security.txt` (889). Point them at `antimanagerpro`/`antimanagerpro_bot` or keep the channel?

## Session done — Article 07 eight monsters + inline loss map (2026-10-14)
- Ch.3 переписан на **восемь** монстров (+«Нереализованный потенциал сотрудников», Лайкер) + раздел «Взаимосвязь монстров» + причинная таблица; inline SVG-карта на `/weapons/dengi-v-dvizhenii/full/` (`role=img` + `<title>`/`<desc>`, скрыта в print — таблица ниже = текстовый эквивалент). Ch.06 приведён к канону «восемь» (нет «девятого вида», «информационные пробки» — усилитель); Ch.05 уже был каноничным.
- Правки vault `07_…md`/`06_…md` через `guard_encoding.py` (backup → OK); docx соавтора проверен — без tracked changes/comments. `VERSION → 20261014a`. Unit **10/10**, Playwright **120/120** (AX04 no-hscroll); PDF `dengi-v-dvizhenii.pdf` (345 KB, 0 картинок) + `processy.pdf` перегенерированы. Commit `9cfd8e7` → deploy → live-verified.
- **Open COSMETIC:** карта читается мелко на десктопе (вне print); при желании — `<h4>`/полноширинная обёртка. Сам SVG статичный (черновик называл его «интерактивной схемой»).
- **Урок (в `site/AGENTS.md`):** не запускать `render:pdf` параллельно с `build`/тестами (оба пишут `dist/`) — иначе в PDF попадает устаревшая разметка; широкий inline SVG в print скрывать, отдавая таблицу.

## Session done — «Геном завода» live + SEO-хардening
- `/genome/` (landing + PLAN sample + 6 doc cards) и `/genome/role/` (КУ + recruiter profile) — индекс, sitemap 0.7/0.6, nav «Геном». Deploy `0d87762`, затем SEO `241092e` → `verify-deploy.ps1` **3/3 OK** (live 200).
- Role KU/profile — offline `.kilo/scripts/genome_doc_build.py` (idempotent, 43 tables); build stays vault-independent.
- SEO: `robots index, follow, max-image-preview:large, max-snippet:-1`; JSON-LD `Organization` в static `@graph` (висячий `publisher` устранён); role breadcrumb 3 уровня; `og:image:alt` без дубля бренда; `<h1>` без склейки; битая `.md`-ссылка → plain text (генератор нейтрализует `.md`/rel-ссылки); `<title>` лендинга усилен. Unit **9/9**, Playwright **120/120**.
- Cleanup: `docs/prototype/` удалён (backup `%TEMP%\kilo\backups`); memory compacted; harness clean (global 7/7/9, project 8/2/10, 0 orphans).

## RESUME (2026-10-14)
- **Feedback form:** reviewed + fixed + committed (two logical units: service; site) + pushed (2026-10-14). **Deploy stays blocked** on the secrets below.
- **Feedback form deploy (blocker):** rotate token, get real `chat_id`, create `$REMOTE_DIR/feedback.env`, run `site/feedback/deploy.ps1` then `site/deploy.ps1`, live-verify a real submission + 429/honeypot.
- **Editorial:** DRAFT series **30–35** (JDR-аудит/экспресс/middle/plant-manager, сборник тестов, концепция НЦ/НС) — frontmatter + related + case/conclusion, затем `/full/` (`content-publisher` + `/full-article <slug>`).
- **Open COSMETIC** (продуктовое): hero-CTA «Заказать проработку» → `#offer`, не прямой Telegram.
- Tests: unit **11/11**; Playwright **135/135** (45×3) — `cd site; npm test`; service `python -m unittest discover -s site/feedback/tests` (**15/15**). Docker держит порт 3000 → при abort `webServer` — временный config на другом порту.
- Two-pass PDF: `build → render:pdf → build → render:pdf → build`; render переписывает `/CreationDate` → `git checkout -- site/materials`.

## Harness / hot rules
- Skills 8, commands 10, agents 2. MCP: obsidian+github (project), context7 (global). `/check-site` = `npm test`.
- Plans policy (`.kilo/AGENTS.md`): `.kilo/plans/` gitignored; 3 tracked plans — history, не трогать.
- **SSH 2222 flaky:** `deploy.ps1` может упасть на mid-run ssh timeout, хотя upload прошёл — проверить живой сайт (GET 200) перед повтором.
- `yandex-verification` meta нужен код пользователя.
- Tech debt (Metrika `webvisor` vs `/privacy/`, GitVerse token rotation, dead `chapters.json`/`tools.json`, `VERSION`/`BUILD_DATE`, raw `content_body`) → `.memory/progress.md` §Technical Debt.
- Full history → `.memory/archive/`; completed-session detail → `.memory/progress.md`.
