# AntiManager — Active Context
> Updated: 2026-09-21

## Current Task
**Two-tier theme pages** (landing → full text → materials) — implemented, **not yet
committed/deployed**. The topic landing `/weapons/<slug>/` stays interactive and now
shows a `.read-more-card` (`{{read_more}}` → `/weapons/<slug>/full/`) instead of the
dead «Тезисный отрывок»; the new full page carries the complete article (static
H2/H3 TOC, reading progress, 4-level breadcrumb) plus an honest `.materials-section`
(article PDF + declared extras, print fallback). The fake site-wide «Материалы к
статье / Хочу PDF» block is gone. **Pilot: article 00** (`content/full/00-*.html`,
464-line vault conversion; PDF 414 KB). Plan + log:
`.kilo/plans/1790011926918-full-article-pages-{plan,execution-log}.md`.

Publish-readiness track (parked pending deploy): 00/01/02/03 → 12/12; 00/01 deployed.
Next editorial: article **04 «Управление как эксперимент»** — Layer 2 pass.
Parked: SEO Phase 2 (publish 21 `review` weapons; replace landing stats 2 847 / 113 / 47).

- Tests: unit **7/7**; Playwright **99/99** (33 × 3). Run all: `cd site; npm test`.
- New scripts: `npm run render:pdf` (`site/scripts/render-pdf.js`, Playwright print);
  `materials.json` `href` validated; `MATERIALS_FILE` env seam for tests.

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
- **Deploy the two-tier article 00**: commit + `.\deploy.ps1`, then verify live
  `/weapons/mayatnik-upravleniya/` (read-more card) and `/full/` (TOC, PDF download).
- Roll `/full/` out article-by-article as vault readiness allows (article 01 has no
  weapon entry — its full text is `/manifesto/`).
- Continue article-by-article readiness: article **04 «Управление как эксперимент»**
  — Layer 2 editorial pass (facts, related tools/chapters, style), then site sync.
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
