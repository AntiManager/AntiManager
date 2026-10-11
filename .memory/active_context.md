# AntiManager — Active Context
> Updated: 2026-10-11

## Current Task
**Two-tier theme pages** (landing → full text → materials) — implemented, committed
(`0e4e511`) and **deployed** (live-verified). The topic landing
`/weapons/<slug>/` stays interactive and now shows a `.read-more-card`
(`{{read_more}}` → `/weapons/<slug>/full/`) instead of the dead «Тезисный отрывок»;
the new full page carries the complete article (static H2/H3 TOC, reading progress,
4-level breadcrumb) plus an honest `.materials-section` (article PDF + declared
extras, print fallback). The fake site-wide «Материалы к статье / Хочу PDF» block is
gone. **Rollout:** articles 00, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17 built and
deployed. Articles 15 «Живой завод» (`4633211`), 16 «Управлять хаосом на производстве» and
17 «Лестница ошибок» **published** (16: vault Layer 2 — heading hierarchy normalised, Case-1 arithmetic fixed
12%→6% ⇒ ~1 млн/мес, Obsidian escapes unescaped, tools 1→7, chapters 4→7; `src/content/full/16-haos.html`
via new reusable `.kilo/scripts/md_to_partial.py`; landing `{{read_more}}`; `materials/haos.pdf` 432 813 B;
unit 8/8, e2e 99/99; committed `8451587`, pushed GitHub+GitVerse, deployed, live-verified 11/11. 17: vault Layer 2 —
title `#`, thesis-first opening, unsourced 500 млн → «сотни миллионов», misattribution «Р. Грин/М. Гоулстон» →
Маршалл Голдсмит «Прыгни выше головы!», tabs→3-space, tools 2→4, chapters 4→7, split pull-quote joined;
readiness 11/12 (single `case` false gap, same as 10/15), wiki 6→11; landing lite table 3→4 levels, weapons.json
subtitle fixed; `md_to_partial.py` generalised (no-Оглавление fallback + indented list continuations);
`materials/lestnitsa-oshibok.pdf` 285 319 B; committed `9894435`, pushed GitHub+GitVerse, deployed, live-verified).
Plan + log: `.kilo/plans/1790011926918-full-article-pages-{plan,execution-log}.md`.

Publish-readiness track: 00/01/02/03/04/05/06/07/08/09/10/11/12/13/14/15/16/17/18 all READY (article 16
12/12; articles 10, 15, 17 and 18 at 11/12 — the single miss is the `case` heading false gap; their cases are
inline/bold body labels). Articles 00, 02–18 have deployed `/full/` pages.
Next editorial: article **19 «Цифровой двойник»** — Layer 2 pass + site sync.
Parked: SEO Phase 2 (publish 21 `review` weapons; replace landing stats 2 847 / 113 / 47).

- Tests: unit **8/8**; Playwright **99/99** (33 × 3). Run all: `cd site; npm test`.
- **Env pitfall:** Docker Desktop holds host port 3000, so `npm test`'s Playwright
  `webServer` may reuse a dead port and abort all tests. If so, run the suite on an
  alternate port via a temp config (`webServer.port` + `use.baseURL`), and keep test
  requests relative to `baseURL` (AX07 fixed for this in `1e0c508`).
- New scripts: `npm run render:pdf` (`site/scripts/render-pdf.js`, Playwright print);
  `materials.json` `href` validated; `MATERIALS_FILE` env seam for tests.
- Full-page authoring note: the landing read-more lede is auto-extracted from the
  first `<p>` in the full partial — make it a short, strong standfirst (split the
  preface's first paragraph when it is long or disclaimer-like), and keep a part
  subtitle a non-`<p>` element (`.full-part-lede`). The site has no mermaid runtime:
  convert source mermaid fences to ordered-list/flow text in full partials.
- `npm run render:pdf` renders from the already-built `dist/`. **Two-pass rule (learned on 17):**
  `build` → `render:pdf` → `build` → **`render:pdf` again** → `build`. The first render happens while the
  article's own `materials/<slug>.pdf` does not yet exist, so its materials block is the print fallback;
  only a second render (PDF present) embeds the real download link. Any single-pass render leaves exactly
  the newly-added PDF with fallback text. **Content is deterministic, but every render rewrites the PDF
  `/CreationDate`/`/ModDate` metadata**, so all tracked PDFs show as modified (same byte length, ~12-byte
  diff). Restore the untouched ones (`git checkout -- site/materials`) and commit only genuinely new/changed
  PDFs — avoids a 17-file binary churn on each article.

## Harness state (this session)
- Article 01 site: `build.js` manifesto now rendered from structured
  `manifestoValues/manifestoPrinciples/manifestoClosing` (drives both `/manifesto/`
  and the landing teaser — no drift); `brutalist.css` +`.manifesto-preamble`/
  `.manifesto-value-body`; `ux-critical.spec.js` +`AX13`. Suite 99/99.
- New: skill `article-readiness`, command `/article-readiness`,
  script `.kilo/scripts/article_readiness.py` (report in gitignored `.kilo/reports/`);
  wired into `book-writing` + `book-editor`.
- New reusable script `.kilo/scripts/md_to_partial.py` (vault Markdown → site full-text
  partial: drops frontmatter/title block/Оглавление/related sections, maps `##`→h2
  (opens `<section>`) / `###`→h3, tables→`.table-wrap`, blockquotes, ul/ol, bold/italic,
  `[[wiki]]`). Used to author `src/content/full/16-haos.html` and `17-lestnitsa-oshibok.html`;
  replaces the per-article one-off converter. NOTE: it escapes `<`/`>`/`&`. Generalised on 17:
  handles articles without a manual «Оглавление» (drop title block to the first `---`) and merges
  indented continuation lines into the preceding list item (multi-line numbered items).
- Landing lite tables and `weapons.json` subtitles are canon-checked against the vault article
  (17's subtitle «Как отличить системную ошибку от случайной» was stale → rewritten).
- `.kilo/AGENTS.md` map: skills 8, commands 9.
- `/check-site` now runs the full suite (`npm test`); `vault-indexer` stale `.gigacode/`
  exclusion removed.
- Memory compacted: old `active_context` history → `.memory/archive/active_context-2026-09.md`.

## Next step
- Article 18 «Антикризис» **full cycle done** (vault Layer 2 + site sync). Vault: demoted
  title-block subtitle to a bold non-heading; unescaped the poster-quote `1\.`/`2\.`/`3\.`;
  4 U+2011 → hyphen; 7 parenthetical ` – ` → `—`; hedged unsourced precision (Bayer «десятки
  миллионов евро» → «многомиллионный ущерб»; «сократились на 98%» → «в разы»; «выявляется на
  100%» → «почти всегда»; «упала в 3 раза» → «резко упала»; «лучше 80% управленцев» → «лучше
  большинства»); fixed grammar «не давало» → «не давал»; replaced the draft «файл 15» reference
  with `[[15_Живой_завод|15. Живой завод]]`; dropped the «Ваш коллега и проводник» signature;
  tools 2→4 (+PDCA, +5 Whys), chapters 4→5 (+15); `updated` → 2026-10-11. Readiness 11/12
  (single `case` false gap, same as 10/15/17), jumps 0, wiki 6→10, guard OK (2.6%).
- Site: landing «Тезисный отрывок» → `{{read_more}}`, stale «80% провалов» → «большинство
  провалов» (canon-aligned); authored `src/content/full/18-antikrizis.html` via `md_to_partial.py`
  (8 h2 / 7 h3, 3 tables, 2 blockquotes; the lede is the intro's first `<p>`); rollout regression
  extended to 18. `materials/antikrizis.pdf` 357 562 B. Unit 8/8, e2e 99/99 (port 3000 free).
- Next: article **19 «Цифровой двойник»** — Layer 2 editorial pass + site sync.
- Roll `/full/` out article-by-article as vault readiness allows (00 pilot, 02–18 done; 01
  has no weapon entry — its full text is `/manifesto/`): convert `src/content/full/XX-slug.html`,
  replace the landing excerpt with `{{read_more}}`, `npm run build` → `npm run render:pdf` →
  rebuild → **`render:pdf` again** → rebuild → deploy.
- Publish per-article extras (checklists/templates): `site/materials/<slug>/<file>` +
  entry in `site/src/data/materials.json`.
- SEO Phase 2 decision gates remain parked (publish 21 `review` weapons; replace
  fabricated landing stats 2 847 / 113 / 47).

## Process-library refactor (plan 1791721561689)
- **Phase 0 (specs) done** (2026-10-11). Unified SME process-library template
  scaffolded in the personal vault `Библиотека процессов\`: `specs/T0.1…T0.8`
  + `_template-stub.md`; engine (parser + validator + CLI, Python) at
  `.kilo/process-engine/` (10/10 tests). APQC = groups primary + crosswalk
  (plan §2.5 upheld); procurement/sales thin loop; engine kept in AntiManager.
  Log: `.kilo/plans/1791721561689-…-execution-log.md`.
- **T1.1 done** (2026-10-11). `Proc_lib.md` split into vault
  `Библиотека процессов\library\`: `INDEX.md` + 12 group files
  (`STRAT ORG ENG ANLZ PLAN MFG MNT QUAL HRP ENV IMPR EMG`). New reusable
  `.kilo/process-engine/split_library.py`. **Regression gate PASS** — parser
  before/after identical: 759 nodes / 0 edges; 12 groups / 60 proc / 130 subproc /
  557 ops. Guard 13/13 OK; engine tests **11/11** (+`test_split_library_preserves_graph`).
  Engine hardened: `main()` reconfigures stdout/stderr to UTF-8 (cp1251 console
  crashed on `×`/`→` and aborted `--json`). Do NOT touch `Proc_library/library/`.
  Deferred: verbose `technologies/*.md` vendoring (would add MFG subprocesses →
  needs its own baseline); group cross-ref anchors (`[[#Группа PLAN …]]`) → T1.4.
- **Next:** T1.2 — normalize hierarchy per group (`LIBRARY→GROUP→PROCESS→SUBPROCESS`),
  unified coding, §9.1; add a goal per PROCESS/SUBPROCESS.
- **Resume commands:** engine = `.kilo/process-engine/engine.py`; validate the vault
  library: `python .kilo/process-engine/engine.py "…\Библиотека процессов"` (vocab
  v0.1/44). Re-split if needed:
  `python .kilo/process-engine/split_library.py "<…>\Proc_library\library\processes\Proc_lib.md" "…\Библиотека процессов\library"`.
  Tests: `python -m pytest -q -p no:cacheprovider` (in `.kilo/process-engine`).
- **Open (low):** spec docs T0.1–T0.8 are English (service-doc policy); user
  may request Russian.

## Hot rules / deferred
- Metrika/Webvisor untouched; `webvisor:true` vs `/privacy/` wording — deferred by user (compliance risk).
- `yandex-verification` meta needs the user's code.
- GitVerse token in `.git/config` `origin.pushurl` (plaintext) — rotate + move to credential helper/SSH (HIGH).
- `chapters.json`/`tools.json` — unreferenced dead data (remove or wire), decide separately.
- `build.js` `VERSION` static vs dynamic `BUILD_DATE` — couple on next release.
- Residual: `content_body` is raw HTML (malicious PR to `src/content/*.html`); rely on PR review/branch protection.
