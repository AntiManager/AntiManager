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
gone. **Rollout:** articles 00, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16 built and
deployed. Articles 15 «Живой завод» (`4633211`) and 16 «Управлять хаосом на производстве»
**published this session** (16: vault Layer 2 — heading hierarchy normalised, Case-1 arithmetic fixed
12%→6% ⇒ ~1 млн/мес, Obsidian escapes unescaped, tools 1→7, chapters 4→7; `src/content/full/16-haos.html`
via new reusable `.kilo/scripts/md_to_partial.py`; landing `{{read_more}}`; `materials/haos.pdf` 432 813 B;
unit 8/8, e2e 99/99; committed `8451587`, pushed GitHub+GitVerse, deployed, live-verified 11/11). Plan + log:
`.kilo/plans/1790011926918-full-article-pages-{plan,execution-log}.md`.

Publish-readiness track: 00/01/02/03/04/05/06/07/08/09/10/11/12/13/14/15/16 all READY (article 16
12/12; articles 10 and 15 at 11/12 — the single miss is the `case` heading false gap; their cases are
inline/bold body labels). Articles 00, 02–16 have deployed `/full/` pages.
Next editorial: article **17 «Лестница ошибок»** — Layer 2 pass + site sync.
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
- `npm run render:pdf` regenerates *every* `<slug>.pdf`, so all tracked PDFs show as modified
  after each render — usually timestamp-only (`/CreationDate`, 14 B), not content. The PDFs also
  carry pre-existing loopback `http://127.0.0.1:<port>` link annotations (already in HEAD).

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
  `[[wiki]]`). Used to author `src/content/full/16-haos.html`; replaces the per-article
  one-off converter. NOTE: it escapes `<`/`>`/`&`.
- `.kilo/AGENTS.md` map: skills 8, commands 9.
- `/check-site` now runs the full suite (`npm test`); `vault-indexer` stale `.gigacode/`
  exclusion removed.
- Memory compacted: old `active_context` history → `.memory/archive/active_context-2026-09.md`.

## Next step
- Article 16 «Управлять хаосом на производстве» **published** (`8451587`, pushed GitHub+GitVerse,
  deployed, live-verified 11/11: landing `.read-more-card` → `/full/`, no `block-thesis`/`download-section`;
  `/full/` with `.article-toc`, `.materials-section`, PDF link, `"position": 4`, no tokens;
  `materials/haos.pdf` 200 `application/pdf` 432 813 B). Note: `deploy.ps1`'s final optional Caddy-reload
  ssh step timed out again (config unchanged, no-op) — the container restart itself succeeded.
- Next: article **17 «Лестница ошибок»** — Layer 2 editorial pass + site sync.
- Roll `/full/` out article-by-article as vault readiness allows (00 pilot, 02–16 done; 01
  has no weapon entry — its full text is `/manifesto/`): convert `src/content/full/XX-slug.html`,
  replace the landing excerpt with `{{read_more}}`, `npm run build` → `npm run render:pdf` →
  rebuild → deploy.
- Publish per-article extras (checklists/templates): `site/materials/<slug>/<file>` +
  entry in `site/src/data/materials.json`.
- SEO Phase 2 decision gates remain parked (publish 21 `review` weapons; replace
  fabricated landing stats 2 847 / 113 / 47).

## Hot rules / deferred
- Metrika/Webvisor untouched; `webvisor:true` vs `/privacy/` wording — deferred by user (compliance risk).
- `yandex-verification` meta needs the user's code.
- GitVerse token in `.git/config` `origin.pushurl` (plaintext) — rotate + move to credential helper/SSH (HIGH).
- `chapters.json`/`tools.json` — unreferenced dead data (remove or wire), decide separately.
- `build.js` `VERSION` static vs dynamic `BUILD_DATE` — couple on next release.
- Residual: `content_body` is raw HTML (malicious PR to `src/content/*.html`); rely on PR review/branch protection.
