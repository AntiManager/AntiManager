---
description: Migrate one article's full text to its /full/ page (TOC, materials, PDF) and deploy
---
Migrate the full text of one article. `$1` = article number or slug (e.g. `19`).

Follow the `content-publisher` skill (full-text process). Atomic recipe:

1. **Vault Layer 2 first.** Run `python pipelines/obsidian-to-site/article_readiness.py`, read the
   report, and apply the `article-readiness` skill checklist until the article is
   READY. Guard encoding before and after every vault edit.
2. **Convert.** `python pipelines/obsidian-to-site/md_to_partial.py "<vault .md>" site/src/content/full/XX-slug.html`
   (slug from `site/src/data/weapons.json`). The site has no mermaid runtime —
   convert ```mermaid fences to lists/tables in the partial.
3. **Landing.** Replace the `Тезисный отрывок` block with `{{read_more}}`. Keep the
   first `<p>` of the full partial a short, strong standfirst — it becomes the lede.
4. **Regression.** Extend the rollout test in `site/unit/build-full.test.js` to the new slug.
5. **Build + PDF (two-pass rule).**
   `cd site; node build.js; npm run render:pdf; node build.js; npm run render:pdf; node build.js`
   The first render runs before `site/materials/<slug>.pdf` exists; the second embeds
   the real download link in the PDF itself.
6. **Tests.** `cd site; npm test` (expected: unit 8/8, e2e 99/99; if port 3000 is held
   by Docker, run on an alternate port via a temp config).
7. **Stage PDFs cleanly.** Renders rewrite `/CreationDate` on every tracked PDF —
   `git checkout -- site/materials` restores untouched ones; commit only genuinely
   new/changed PDFs.
8. **Deploy + live-verify.** `site/deploy.ps1`, then confirm landing `.read-more-card`
   → `/full/`, `/full/` 200 (static TOC + PDF link), `/materials/<slug>.pdf` 200.
