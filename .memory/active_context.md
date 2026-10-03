# AntiManager — Active Context
> Updated: 2026-10-03

## Current Task
**Two-tier theme pages** (landing → full text → materials) — implemented, committed
(`0e4e511`) and **deployed** (live-verified). The topic landing
`/weapons/<slug>/` stays interactive and now shows a `.read-more-card`
(`{{read_more}}` → `/weapons/<slug>/full/`) instead of the dead «Тезисный отрывок»;
the new full page carries the complete article (static H2/H3 TOC, reading progress,
4-level breadcrumb) plus an honest `.materials-section` (article PDF + declared
extras, print fallback). The fake site-wide «Материалы к статье / Хочу PDF» block is
gone. **Rollout:** articles 00, 02, 03, 04, 05, 06, 07, 08, 09 done. Article 09 «Бей,
беги, замри» completed this session (Layer 2 → landing `{{read_more}}` → `/full/` +
`materials/bey-begi-zamri.pdf` 442 KB; commit `c7f2355`, deployed, live-verified).
Plan + log: `.kilo/plans/1790011926918-full-article-pages-{plan,execution-log}.md`.

Publish-readiness track: 00/01/02/03/04/05/06/07/08/09 → 12/12. Articles 00, 02, 03, 04, 05,
06, 07, 08, 09 have deployed `/full/` pages.
Next editorial: article **10 «Ситуационное развитие»** — Layer 2 pass + site sync.
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

## Harness state (this session)
- Article 01 site: `build.js` manifesto now rendered from structured
  `manifestoValues/manifestoPrinciples/manifestoClosing` (drives both `/manifesto/`
  and the landing teaser — no drift); `brutalist.css` +`.manifesto-preamble`/
  `.manifesto-value-body`; `ux-critical.spec.js` +`AX13`. Suite 99/99.
- New: skill `article-readiness`, command `/article-readiness`,
  script `.kilo/scripts/article_readiness.py` (report in gitignored `.kilo/reports/`);
  wired into `book-writing` + `book-editor`.
- `.kilo/AGENTS.md` map: skills 8, commands 9.
- `/check-site` now runs the full suite (`npm test`); `vault-indexer` stale `.gigacode/`
  exclusion removed.
- Memory compacted: old `active_context` history → `.memory/archive/active_context-2026-09.md`.

## Next step
- Roll `/full/` out article-by-article as vault readiness allows (00 pilot, 02–09 done):
  convert `src/content/full/XX-slug.html`, replace the landing excerpt with
  `{{read_more}}`, `npm run build` → `npm run render:pdf` → rebuild → deploy. (Article 01
  has no weapon entry — its full text is `/manifesto/`.)
- Then article **10 «Ситуационное развитие»** — Layer 2 editorial pass + site sync.
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
