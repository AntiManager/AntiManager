# AntiManager — Active Context archive (2026-10)
> Full history; not auto-loaded.

## Archive append 2026-10-12 (harness cleanup)

## Pipelines consolidated (2026-10-12)
Tooling unified under `pipelines/` (`common/`, `obsidian-to-site/`, `proc-library/`); the process-library engine is now versioned in-repo (specs mirrored at `pipelines/proc-library/specs/`, generated artifacts ignored) and the vault path is env-driven (`PROC_LIB_VAULT`). The `silicon-goal` worktree is retired (useful bits — `kilo.json` boot-trio, two skill fixes — ported to `main`). Details in `progress.md`.

## Review + cleanup + DEPLOY done (2026-10-11)
`/review uncommitted` (reviewer subagent) found and applied: (1) **major** — the new full-page
`description` came from raw article prose → escaped once at construction (build.js) so it can't
break the `<meta>` attribute (the pre-existing `{{description}}` substitution stays raw; all other
inputs are load-sanitized); (2) `gzip_types` — `text/html` removed (nginx compresses it implicitly;
explicit listing warns "duplicate MIME type", verified via `nginx -t`); (3) `date` field validated
`^\d{4}-\d{2}-\d{2}$` at load (HTML attr / sitemap XML / JSON-LD) else dropped; (4) `.filter-btn:hover`
color → `--color-accent-text` (was still `--color-accent`, ~4.1:1); (5) Yandex unit assertion pinned to
the exact `yandex_XXXXXXXXXXXXXXXX.html` placeholder and the test build sets `YANDEX_VERIFICATION:''`;
(6) breadcrumb builder simplified. Suite re-run: **unit 8/8, e2e 102/102**.
**Deploy (live-verified):** two `deploy.ps1` bugs found and fixed — `scp dist\*` skipped the hidden
`.well-known/` (security.txt was 404) → now `scp dist\.`; nginx `absolute_redirect off` so the
trailing-slash 301 is relative (TLS is at Caddy; nginx only saw http). Commits `410d706`, `abdfb60`,
`440cfd3` pushed to GitHub+GitVerse and deployed. Live: home/arsenal/weapon/full 200, custom 404,
`www→apex` 301, trailing-slash 301 (https), HSTS + Content-Language, security.txt 200.

## Next session (resume) — editorial / SEO
- Next editorial: the DRAFT series **30–35** (JDR-аудит/экспресс/middle/plant-manager, сборник
  тестов, концепция развития НЦ/НС) — each needs frontmatter + related sections + case/conclusion
  before `/full/`.
- SEO Phase 2 remaining (accepted/deferred): CSP still lacks `default-src`/`script-src` (inline
  Metrika/widgets); Metrika `webvisor` vs `/privacy/` wording (user-deferred).
Resume pointers: nginx conf validated on a local `nginx:alpine` container; `.webp` siblings live in the
untracked `Фото_мыслителей/` (gitignored) and are regenerated via `npm run optimize:thinkers`; per-article
`date` fields are in `weapons.json`.

## Latest: SEO & accessibility hardening (2026-10-11)
Full live-site audit + fixes, all verified. **Uncommitted** (working tree), on top of the
parked `SEO Phase 2` edits (all weapons `published`, fabricated landing stats removed).

- **nginx** (`site/deploy/nginx.conf`, verified on a local `nginx:alpine` container):
  custom 404 (`error_page 404 /404/index.html`), `www→apex` 301, trailing-slash 301,
  HSTS + `Content-Language: ru`, de-duplicated `Cache-Control` (server-level `add_header`
  + per-location `expires` only). Deploy must still run `nginx -t`.
- **build.js**: unique `/full/` meta description (first paragraph via `summaryText`);
  landing description grammar fixed; JSON-LD enriched (`@id` graph, `Organization.logo`,
  `mainEntityOfPage`, `image`); `og:image:alt`/`twitter:image:alt`; `datePublished` from the
  per-article `weapons.json` `date` (added, sourced from git), `dateModified` = build date;
  sitemap `lastmod` per article; `YANDEX_VERIFICATION` env replaces the `XXXX` placeholder;
  `.well-known/security.txt`; thinker photos as `<picture>` (webp + fallback, guarded).
- **CSS**: accessible text tokens `--color-muted #8B95A8` (~6.5:1) and
  `--color-accent-text #EF4444` (~5.3:1); `--color-steel` kept for borders/filled surfaces;
  zone-subtitle opacity removed. Footer nav added (fixes orphan `/about`, `/headquarters`, `/privacy`).
- **Images**: `scripts/optimize-thinkers.js` (Playwright canvas → `.webp`), `npm run optimize:thinkers`; saved ~1.2 MB.
- **Content**: article 05 full partial `h4`→`h3` (cleared the heading jump).
- **Tests**: unit 8/8, e2e **102/102** (new AX14 contrast test; build-seo gains items 9–14).
- **Not fixed (accepted):** CSP still lacks `default-src`/`script-src` (inline Metrika/widgets);
  Metrika `webvisor` vs `/privacy/` wording (deferred by user).

## Current Task
**Two-tier theme pages** (landing → full text → materials) — implemented, committed
(`0e4e511`) and **deployed** (live-verified): `/weapons/<slug>/` stays interactive and
shows a `.read-more-card` (`{{read_more}}` → `/weapons/<slug>/full/`) instead of the
dead «Тезисный отрывок»; the full page carries the complete article (static H2/H3 TOC,
reading progress, 4-level breadcrumb) plus an honest `.materials-section` (article PDF +
declared extras, print fallback). Fake site-wide «Материалы к статье / Хочу PDF» removed.
**Rollout:** 00, 02–23 built, tested (unit 8/8, e2e 99/99) and deployed.
**Article 21 «Два типа управления»** done (committed `75bc1c7`, live-verified); **article
22 «Ударить по траектории»** done: vault restructured to the norm (title block `---`;
all `###` sections re-levelled to `##`, clearing the 1 heading jump; 2 double-encoded
wiki-link display texts repaired — L83 «инжиниринг на уровне причин», L189 «контракт с
самим собой» + broken target `Два_типа_управления` → `21_Два_типа_управления»;
unsourced «90% людей» hedged; `book/draft` dropped; tools +PDCA, chapters +06/+21).
Readiness 12/12, jumps 0, wiki 20; landing `{{read_more}}`;
`full/22-udarit-po-traektorii.html` = 14 h2. The converter now drops the legacy bold
«Связанные главы:» trailer (recurring chrome — was leaking in 20/21 too).
**Article 23 «Коммуникационный конструктор»** done (committed `516d8b8`, live-verified):
vault Layer 2 — frontmatter + title block (Концепция/Механизм) + 2 inline crosslinks
([[14_Управление_живой_системой]], [[Pre-Mortem]]) + «Связанные инструменты/главы»;
readiness 8/12 → 12/12 (jumps 0, wiki 11). New weapon `23 kommunikacionnyy-konstruktor`
(zone `changes`) + landing (principle + 5-model table + 3-question model-picker widget) +
`/full/` (14 h2) + PDF. `build-seo.test.js` landing plural 22→23 «главы» (count-pinned).
**Next editorial:** the DRAFT series **30–35** (JDR-аудит/экспресс/middle/plant-manager,
сборник тестов, концепция развития НЦ/НС) — a different set; each needs frontmatter +
related sections + case/conclusion before /full/.
Per-article history → `.memory/archive/progress-history-2026.md`.

Publish-readiness: 00/01/02–23 all READY (articles 10, 15, 17, 18, 20, 21 at 11/12 — the
single miss is the `case` heading false gap; their cases are inline/bold body labels).
Remaining vault articles 30–35 are DRAFT (different series; see “Next editorial”).
SEO Phase 2 — done (`410d706`): all 23 weapons `published`, fabricated landing stats removed
(guarded by `build-seo.test.js`). Only CSP `script-src` and the Metrika `webvisor`/`/privacy/` wording stay deferred.

**Editor procedure is codified** — follow the `content-publisher` skill and the
`/full-article <slug>` command; do not re-derive the steps. Key rules that still matter:

- Tests: unit **8/8**; Playwright **99/99** (33 × 3). Run all: `cd site; npm test`.
- **Env pitfall:** Docker Desktop holds host port 3000, so `npm test`'s Playwright
  `webServer` may reuse a dead port and abort all tests. If so, run the suite on an
  alternate port via a temp config (`webServer.port` + `use.baseURL`), and keep test
  requests relative to `baseURL` (AX07 fixed for this in `1e0c508`).
- Scripts: `npm run render:pdf` (`site/scripts/render-pdf.js`, Playwright print);
  `materials.json` `href` validated; `MATERIALS_FILE` env seam for tests.
- Lede = first `<p>` of the full partial — keep it a short standfirst (split a long
  preface paragraph); a part subtitle must be a non-`<p>` element (`.full-part-lede`).
  No mermaid runtime — convert ```mermaid fences to lists/flow text.
- **Two-pass PDF rule:** `build → render:pdf → build → render:pdf → build` (the first
  render runs before the article's own PDF exists). Every render rewrites the PDF
  `/CreationDate` (~12-byte diff) — `git checkout -- site/materials` restores untouched
  PDFs; commit only genuinely new/changed ones.

## Harness state
- Skills 8, commands 10 (+`/full-article`), agents 2. MCP: obsidian, github (project
  `.kilo/kilo.json`), context7 (global `kilo.jsonc`); `web-search` declared but dead.
- Article 01 site: `build.js` manifesto rendered from structured
  `manifestoValues/manifestoPrinciples/manifestoClosing` (drives `/manifesto/` and the
  landing teaser — no drift).
- `article-readiness` skill + `/article-readiness` + `pipelines/obsidian-to-site/article_readiness.py`
  (report in gitignored `.kilo/reports/`); reusable `pipelines/obsidian-to-site/md_to_partial.py`.
- Landing lite tables and `weapons.json` subtitles are canon-checked against the vault.
- `/check-site` runs the full suite (`npm test`); `vault-indexer` stale `.gigacode/`
  exclusion removed.
- Memory compacted 2026-10-11: history → `.memory/archive/` (`progress-history-2026.md`,
  `active_context-2026-09.md`). `pipelines/proc-library/` is git-excluded
  (`.git/info/exclude`) — force-add only to commit it deliberately.

## Process-library refactor (plan 1791721561689) — parallel track
- **Phase 1 COMPLETE — "subprocess-level v1" FROZEN (T1.5).** Unified SME template
  in the personal vault `Библиотека процессов\`: `specs/T0.1…T0.8` + `_template-stub.md`;
  engine (parser + validator + CLI + tools) at `pipelines/proc-library/`. Log:
  `.kilo/plans/1791721561689-…-execution-log.md`; plan §11/§12.
- T1.1 split `Proc_lib.md` → vault `library\` (T1.6 later added `INF` + the 7 `SL_*`);
  T1.2 hierarchy + goals; T1.3 APQC crosswalk 79/79; T1.4 seams; T1.6 `INF`+`LOG`.
  **Baseline: 20 groups / 79 processes / 238 subprocesses / 995 operations**, 1332
  nodes / 0 edges. Do NOT touch `Proc_library/library/`.
- **T1.5 freeze gate:** 0 errors at LIBRARY/GROUP/PROCESS/SUBPROCESS (goals present,
  APQC 79/79, §4.7/§4.9/§4.10 0, 0 dup codes); all 4823 errors + 3848 warnings are
  OPERATION-level (→ T2.2); **client-identity token scan 0** (new `token_scan.py`;
  fixed QUAL-06-02 «500 тыс. руб.»). Record: `pipelines/proc-library/freeze_v1_subprocess.json`
  (signature `sha256 a506b2f5…`). Suite **15/15**. `SLA` + `ENG-04` stay OUT of the
  template (holding-grade; user decision — supersedes T0.1 D1 for these two).
- **Next:** Phase 2 (operations + flow graph), pilot **Planning** (`PLAN` + `SL_PLAN`).
- **Resume:** engine `pipelines/proc-library/engine.py`; validate
  `python pipelines/proc-library/engine.py "<…>\Библиотека процессов"` (vocab v0.1/44);
  token scan `python pipelines/proc-library/token_scan.py "<…>\Библиотека процессов\library"`;
  tests `python -m pytest -q -p no:cacheprovider`.
- Note: `pipelines/proc-library/` is git-excluded; the `silicon-goal` worktree carries a
  mirror copy — keep them in sync.

## Hot rules / deferred
- Metrika/Webvisor untouched; `webvisor:true` vs `/privacy/` wording — deferred by user (compliance risk).
- `yandex-verification` meta needs the user's code.
- GitVerse token in `.git/config` `origin.pushurl` (plaintext) — rotate + move to credential helper/SSH (HIGH).
- `chapters.json`/`tools.json` — unreferenced dead data (remove or wire), decide separately.
- `build.js` `VERSION` static vs dynamic `BUILD_DATE` — couple on next release.
- Residual: `content_body` is raw HTML (malicious PR to `src/content/*.html`); rely on PR review/branch protection.
- **SSH 2222 flaky (VPS):** `Test-NetConnection` to `5.129.221.85:2222` intermittently
  succeeds while `ssh`/`scp` time out; ping + 443 stay green. `deploy.ps1` may abort on a
  mid-run ssh timeout although the dist upload/container restart already landed —
  **verify live (GET 200) before re-running**; the trailing Caddy reload is optional.

## Archive append 2026-10-16 (harness optimization: boot-trio compaction)


## Session done — /contact/ form QA + fixes (2026-10-16, committed & deployed)
- **Deployed** (commit `2c13407`, pushed to both remotes): `VERSION → 20261016b`; feedback service redeployed and the site redeployed. **Live:** `GET /contact/` 200 with `?v=20261016b` + `aria-describedby`; `GET /` 200; `GET /css/brutalist.css?v=20261016b` 200 with `.btn:disabled`; `POST /api/feedback` form-encoded (honeypot) → 200 `text/html` (new no-JS path live, silent drop). **SSH :2222 flaked twice** — the service `deploy.ps1` aborted after `docker build` (image rebuilt, container not recreated) and the site `deploy.ps1` aborted at the nginx-restart step; recovered by recreating the feedback container manually after a ~15 s retry (site needed no restart — `dist` is volume-mounted, content served immediately).
- **QA** in real Chromium (320–1280 px): adaptability clean (no hscroll, tap targets ≥44px, 16px inputs → no iOS zoom), functional flows green (keyboard-only, Enter-submit, double-submit guard, native validation, `?pack=`). Full report served to user.
- **Fixed all 7 findings:** (1) `:focus`+`outline:none` on `.field input/textarea` beat the global `:focus-visible` → removed `outline:none`, keyboard ring restored; (2) `.btn:disabled{opacity:.5;cursor:not-allowed}`; (3) 429 now shows a specific «Слишком много заявок» message (`contact.js` carries `err.status`); (4) `html{background:var(--color-bg)}` (was body-only → white overscroll/capture artifact); (5) consent checkbox 20→24px (WCAG 2.5.8); (6) `aria-describedby="cf-contact-hint"` on the contact field; (7) no-JS path now works — `feedback/server.py` accepts `application/x-www-form-urlencoded` and returns a small HTML notice for `Accept: text/html`, JSON otherwise; noscript text updated.
- **Evidence:** site `npm test` → unit OK + Playwright **162/162** (153 + 3 new CF01 tests ×3 viewports); service `python -m unittest discover -s site/feedback/tests` → **23/23** (+3). Re-verified live in browser: focus ring present, checkbox 24×24, `html` bg, disabled opacity 0.5.
- **Lesson folded into `site/AGENTS.md`** (Contact): a component `:focus { outline:none }` silently overrides the global `:focus-visible` ring (higher specificity) — audit components after adding global focus styles; keep the background on `html`.

## Session done — review + fixes + cleanup + commit (2026-10-16)
- **Review** of the uncommitted strategy follow-up + the `fcace02` feature. Findings & fixes:
  - Reverted a metadata-only churn on `site/materials/antihrupkaya-strategiya.pdf` (a 38-byte `CreationDate`/`ModDate` diff from the re-render; rendered content unchanged).
  - Fixed a real defect: the «Читайте также» interlinks block leaked into the auto-generated article TOC. `withToc` now skips headings marked `data-toc="skip"`; the generator + both partials carry the attribute; a new unit assertion guards it (no PDF regen needed — attributes do not render).
- **Plan cleanup** (`.kilo/plans/`, gitignored): archived the finished `1792172902407-*` (strategy), `1791982730592` (article 07), `1791984795554` (feedback form) into `archive/`. Kept `1791721561689-*` (process-library, Phase 2 in progress) and the 3 tracked plans.
- **Harness + docs:** verified counts — global **7/7/9**, project **8/10/2**, **0 orphans** (the `/check-harness` baseline holds; `/dev`,`/e2e` are documented Zakup project-level, `/run-app` is a removal note). Documented the `/strategy/` section + `gen_strategy_partials.py` in `site/AGENTS.md` (mirrors the `/genome/` and `/contact/` sections) and fixed a misplaced CSS-block reference there.
- **Evidence:** `cd site; npm test` → unit **14/14**, Playwright **153/153**. Committed & pushed to both remotes.

## NEXT SESSION — editorial DRAFT series 30–35
JDR-аудит/экспресс/middle/plant-manager, сборник тестов, концепция НЦ/НС — frontmatter + related + case/conclusion, затем `/full/` (`content-publisher` + `/full-article <slug>`). Open COSMETIC (продуктовое): «Штаб»/клубный каркас на `/headquarters/` + landing hq-section всё ещё описывает сообщество, хотя точка входа — бот; hero-CTA «Заказать проработку» ведёт на `#offer`, не в Telegram.

## Session done — Strategy long-reads `/strategy/` (2026-10-16, DEPLOYED & live-verified)
- **Phase 1 (vault editorial) DONE.** Consolidated drafts 1+2 → flagship `Книга/01_Статьи/40_Антихрупкая_стратегия.md`; article 3 → satellite `41_Амортизационная_ловушка.md`. Head restructured for the converter (`# Title` → `**standfirst**` → `---` → `## Введение`); both **12/12 READY** (`article_readiness.py`). `Антихрупкая_стратегия_2.md` moved to `06 - Черновики глав/` (superseded); originals trashed. Backlinks added to `18_Антикризис`/`07_Деньги_в_движении`; `Roadmap/Дорожная карта доработок.md` updated (series 40/41). Satellite arithmetic fixed (80%→45% = ×1,78; amort 5%→8–10%+), duplicate investment-discipline checklist replaced by a link to the flagship. Terms localized (labor hoarding, absorptive capacity, war-gaming, playbook, units-of-production). **Note:** no book `README.md` exists (nothing to update).
- **Phase 2 (factcheck) DONE.** `.kilo/reports/strategy-factcheck.md` (22 claims; search engines were degraded → 15 «not found» ≠ refuted). Applied honest corrections: cable market 2,9% → «~4–6% CAGR 2026–2031» (Mordor/Grand View); removed the factually wrong TSMC/Infineon 2024–25 example; HSE misattribution reframed to the ABC/XYZ method (Стерлигова); dropped unverifiable micro-data (Финуниверситет 8,3–14,4%, ММК/ТМК numbers, Lingyuan/HK/SAIL, NBER 90/5%, Mississippi $ figures, JES/Burgundy/Bundesbank/PwC/WSM quotes); kept & sourced the verified items (Toyota-2008, Newell/Sharpie, Nippon Steel method change −70 bn ¥, IAS 2.13, OEE). Added `## Источники` (real links) to both `.md`.
- **Phase 3/4 (site) DONE.** `site/src/data/strategy.json` (separate from `weapons.json` — SEO test pins weapons counts); partials via `.kilo/scripts/gen_strategy_partials.py` (converter + md-link→anchor + «Читайте также» interlinks to `/weapons/18-antikrizis/`, `/weapons/07-dengi-v-dvizhenii/`, `/genome/`, sibling); `build.js`: `strategy` loader, `strategyTemplate`, `strategyIndexContent`, `makeStructuredData('strategy')` (Article+BreadcrumbList 3-level+FAQPage), sitemap 0.8, `VERSION → 20261016a`; nav «Стратегия» (header+footer); `brutalist.css` §STRATEGY; `scripts/render-pdf.js` now renders `/strategy/<slug>/` too. Tests: `unit/build-strategy.test.js` + `tests/strategy.spec.js` + AX04 no-hscroll paths.
- **Phase 5 DONE.** Two-pass PDF (`build → render:pdf → build → render:pdf → build`; `git checkout -- site/materials` reverted churn, only the 2 new PDFs kept: `antihrupkaya-strategiya.pdf` 351 KB, `amortizacionnaya-lovushka.pdf` 286 KB). **Evidence:** unit **14/14**, Playwright **153/153**; deployed (`deploy.ps1`; the optional Caddy-reload step hit the known SSH-2222 timeout — a no-op); **live:** `/strategy/`, both articles, and PDF all **200**, FAQPage + breadcrumb present, `?v=20261016a`.
- **Follow-up (2026-10-16, deployed):** re-ran the factcheck with a real browser (Playwright + DuckDuckGo — the plain-HTTP engines that failed the first pass are captcha-blocked). Upgraded several first-pass «not found» to **CONFIRMED** (cable ~2.9%/2026 — CRU; Toyota-2008; Newell/Sharpie; Nippon Steel −¥70 bn method change + pipe-subsidiary merger; IAS 2.13; Burgundy; PwC; WallStreetMojo; Kalinowski *Economics and Sociology* 2017). Rewrote `.kilo/reports/strategy-factcheck.md` as the honest record. Fixed the live satellite: dropped an orphan NBER citation + an unverified «50 млрд» clause, added the now-used Burgundy/PwC/WallStreetMojo sources (vault → partials → build → two-pass PDF → deploy). **Evidence:** unit 14/14, Playwright 153/153; live `?cb` shows the corrected `## Источники`.
- **Commit status:** the feature landed as `fcace02`; the follow-up source fix (`41-amortizacionnaya-lovushka.html` + its regenerated PDF) was committed & pushed in the 2026-10-16 review session (see the top block).
- **Open/optional:** 18-antikrizis landing backlink to the flagship; homepage teaser (plan marks optional). Factcheck report is local (`.kilo/reports/`, gitignored) and not committed. Residual nuance: the flagship's «4–6% CAGR 2026–2031» (Mordor/Grand View) was not independently re-confirmed (CRU supports 2.9% for a single year).

## Session done — Customer feedback form → Telegram (2026-10-14, DEPLOYED & live-verified)
- New `/contact/` page (static partial `src/content/contact.html` + `js/contact.js`, `brutalist.css` §CONTACT) with a form posting **same-origin** `POST /api/feedback`. Offer CTAs on `/genome/` and `cta-band` now open `/contact/?pack=express|process|library|pilot`; footer gained «Связаться». `/privacy/` rewritten (FZ-152: feedback data, consent, withdrawal).
- Backend: `site/feedback/` microservice (Python **stdlib only**, `server.py` + `Dockerfile` + `deploy.ps1` + `tests/`). nginx `location = /api/feedback` proxies to the `antimanager-feedback` container on `vps_shared`. Token stays server-side only (`$REMOTE_DIR/feedback.env`, `chmod 600`).
- **Evidence:** build OK; unit **11/11**; Playwright **135/135**; python `unittest` **20/20**. Token/bot-id absent from the repo (`rg AAF1kAa|8704688877` → 0).
- **Review (`/review uncommitted`, 2026-10-14) + fixes:** added `__pycache__/`·`*.pyc` to `.gitignore` (pyc would otherwise be committed); nginx now overwrites `X-Forwarded-For` with `$remote_addr` (was `$proxy_add_x_forwarded_for`, which kept a client-spoofable value → rate-limit bypass if the port is ever exposed); `server.py` rate-limiter now sweeps idle keys; `deploy.ps1` verifies the container is actually running after `docker run -d` (a crash-loop from an empty env returned exit 0); 5 new service tests (oversized body, invalid JSON, non-object payload, unknown path, invalid requests don't consume the limit); README/.env.example point at `$REMOTE_DIR/feedback.env`. Deferred (documented): nginx static-upstream fragility — restarting nginx while the container is down fails `nginx -t`; left as-is per the documented deploy ordering.
- **Deployed & live-verified (2026-10-14):** after the provider VM restart (Москва, 16:50–17:50 МСК) the service and site were deployed. `TELEGRAM_CHAT_ID=8428486696`; token = **reused (NOT rotated)** `8704688877:<secret>` — valid (`getMe` → `@antimanagerpro_bot`); the value the owner pasted lacked the `<bot_id>:` prefix, so it was completed from the known id. `$REMOTE_DIR/feedback.env` created (`chmod 600`, keys set) and uploaded via `scp` (token never in the command line). **Live evidence:** `GET /` 200, `GET /contact/` 200 (form `action="/api/feedback"`); valid POST → **200** (delivered to Telegram); honeypot → 200 silent-drop; no-consent → 400; after 5 allowed → **429**. One initial POST returned **502** (`urlopen error [Errno 101] Network unreachable`) right after container start — the container resolves `api.telegram.org` to AAAA too but the network is IPv4-only; IPv4 (149.154.166.110:443) is reachable from inside the container and all later sends succeeded, so it was a startup DNS blip, not a config error. Both `antimanager-feedback` and `antimanager-web` running on `vps_shared`; healthz reachable from the web container.
- **Links → bot (resolved):** the 5 remaining `t.me/antimanager` links (landing CTA, JSON-LD `sameAs`, crisis/primary CTAs, `security.txt` Contact) now point at `https://t.me/antimanagerpro_bot` (commit `93c3eae`). **Labels reformulated for the bot** (commit `1db8749`, deployed & live-verified): «ВСТУПИТЬ В TELEGRAM» → «НАПИСАТЬ В TELEGRAM» (landing hq-section + `/headquarters/`), «Новые материалы — в Штабе» → «Спросить в Telegram» (materials block). The "Штаб"/club framing on `/headquarters/` and the landing hq-section heading («ВСТУПАЙ В ШТАБ») still describes a community, though the entry point is now the bot — open COSMETIC if the framing should change. Token kept as-is (owner's decision, not rotated).

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

## RESUME (2026-10-14) — PARKED until 2026-10-15 («паркуемся до завтра»)
- **Feedback form:** reviewed + fixed + committed + pushed + **deployed & live-verified** (2026-10-14). No open blockers. Token was reused (not rotated) — rotate later if desired.
- **Next (first action tomorrow):** editorial DRAFT series **30–35** (JDR-аудит/экспресс/middle/plant-manager, сборник тестов, концепция НЦ/НС) — frontmatter + related + case/conclusion, затем `/full/` (`content-publisher` + `/full-article <slug>`).
- **Open COSMETIC** (продуктовое): hero-CTA «Заказать проработку» → `#offer`, не прямой Telegram; «Штаб»/клубный каркас на `/headquarters/` + hq-section лендинга («ВСТУПАЙ В ШТАБ», «закрытый клуб») всё ещё описывает сообщество, хотя точка входа — бот (переформулировать под бота, если нужно).
- Tests: unit **11/11**; Playwright **135/135** (45×3) — `cd site; npm test`; service `python -m unittest discover -s site/feedback/tests` (**20/20**). Docker держит порт 3000 → при abort `webServer` — временный config на другом порту.
- Two-pass PDF: `build → render:pdf → build → render:pdf → build`; render переписывает `/CreationDate` → `git checkout -- site/materials`.
