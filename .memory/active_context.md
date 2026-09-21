# AntiManager — Active Context
> Updated: 2026-09-21

## Current Task
**Two-tier theme pages** (landing → full text → materials) — implemented, committed
(`0e4e511`) and **deployed** (live-verified 2026-09-21). The topic landing
`/weapons/<slug>/` stays interactive and now shows a `.read-more-card`
(`{{read_more}}` → `/weapons/<slug>/full/`) instead of the dead «Тезисный отрывок»;
the new full page carries the complete article (static H2/H3 TOC, reading progress,
4-level breadcrumb) plus an honest `.materials-section` (article PDF + declared
extras, print fallback). The fake site-wide «Материалы к статье / Хочу PDF» block is
gone. **Rollout:** article 00 (pilot) deployed; article 02 «Управление сложными
системами» completed this session (vault Layer 2 → landing `{{read_more}}` → `/full/`
+ `materials/slozhnye-sistemy.pdf`). Plan + log:
`.kilo/plans/1790011926918-full-article-pages-{plan,execution-log}.md`.

Publish-readiness track: 00/01/02/03 → 12/12; 00/01 deployed; articles 00 + 02 have
`/full/`. Caveat: article 03's recorded pass was cosmetic-only (same overstatement as
02) — give it the full cycle before treating it done.
Next editorial: article **04 «Управление как эксперимент»** — Layer 2 pass.
Parked: SEO Phase 2 (publish 21 `review` weapons; replace landing stats 2 847 / 113 / 47).

- Tests: unit **8/8**; Playwright **99/99** (33 × 3). Run all: `cd site; npm test`.
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
- Roll `/full/` out article-by-article as vault readiness allows (00 pilot, 02 done):
  convert `src/content/full/XX-slug.html`, replace the landing excerpt with
  `{{read_more}}`, `npm run build` → `npm run render:pdf` → rebuild → deploy. (Article 01
  has no weapon entry — its full text is `/manifesto/`.)
- **Article 03 «Системная динамика» — full cycle next** (recorded pass was cosmetic;
  same correction as 02: Layer 2 → site sync → `/full/`).
- Then article **04 «Управление как эксперимент»** — Layer 2 editorial pass.
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
