# AntiManager Site

Public website: https://antimanager.pro
GitHub: https://github.com/AntiManager/AntiManager

## Project Structure

```
AntiManager/
  manifesto-ru.md    # Манифест (русский)
  manifesto-en.md    # Manifesto (English)
  README.md
  site/              # Website source code
    build.js         # Static site builder
    src/             # Templates, data, chapter content
    src/content/     # Topic-landing partials (XX-slug.html)
    src/content/full/# Full-text article partials (XX-slug.html) — presence enables /full/
    materials/       # Downloadable assets: <slug>.pdf (generated) + <slug>/ (authored extras)
    scripts/         # render-og.js, render-pdf.js
    css/             # Stylesheets
    js/              # JavaScript
    fonts/           # Self-hosted woff2
    tests/           # Playwright UX tests
    deploy/          # nginx config
    deploy.ps1       # Deploy to VPS
    package.json
    playwright.config.js
    dist/            # Build output (gitignored)
```

## Vault Path

Source articles (`.md` files) for book chapters live in the Obsidian vault.
Configure the path in `.env` (`ARTICLES_DIR`). Default location:
```
{{ARTICLES_DIR}}
```

Chapters are numbered `XX_Title.md` and map to chapters in `site/src/data/chapters.json`.

Two-tier content per theme: the topic landing at `/weapons/<slug>/` carries the
interactive model/diagnostic; the full text at `/weapons/<slug>/full/` carries the
complete article plus a materials block (article PDF + extras). The landing shows a
read-more card only when a full-text partial exists, and the full page is generated
only then too.

When creating new lite (landing) chapter content:
1. Read the source `.md` from vault
2. Extract: principle, model/table; put `{{read_more}}` where the path to the full text belongs
3. Create interactive widget (diagnostic/calculator)
4. Write HTML partial to `site/src/content/XX-slug.html`
5. Run `node site/build.js` to rebuild

When publishing the full text:
1. Convert the vault `.md` into `site/src/content/full/XX-slug.html` (headings H2/H3 drive the TOC)
2. Replace the landing's `Тезисный отрывок` section with the `{{read_more}}` placeholder
3. Run `node site/build.js`, then `npm run render:pdf` to regenerate `materials/<slug>.pdf`
4. Rebuild so the materials block picks up the PDF, then run `.\deploy.ps1`

## Commands

```bash
cd site
node build.js           # Build site into dist/
npx serve dist          # Local preview
npm test                # unit + Playwright tests
npm run test:unit       # unit tests only
npm run test:e2e        # Playwright only
npm run render:og       # regenerate src/templates/og-image.png from og-image.svg
npm run render:pdf      # render materials/<slug>.pdf from each /full/ page (run after build)
.\deploy.ps1            # Deploy to VPS (reads .env)
```

Unit tests run with `--test-concurrency=1`: any unit test that shells out to `build.js`
writes the shared `dist/`, so parallel test files would race. Keep that flag.
`build.js` accepts a `BUILD_DATE` env override (used by tests for deterministic dates).

## SSH / Deploy

See `.env` for connection details. Default deploy configuration:
```
ssh -p {{REMOTE_PORT}} {{REMOTE_USER}}@{{REMOTE_HOST}}
nginx container: antimanager-web, root: {{REMOTE_DIR}}/current/
```

## Conventions
- Vanilla HTML/CSS/JS — no frameworks
- Two-tier content: topic landing (principle + model + widget) → `/full/` (full text + materials)
- Materials are honest: only real files are linked (`materials/<slug>.pdf`, declared extras); never "coming soon"
- `materials.json` `href` must match `/materials/<slug>/<file>` (build rejects anything else)
- Print stylesheet (`@media print` in `brutalist.css`) strips site chrome for the PDF; regenerate PDFs with `npm run render:pdf`
- All 22 chapters indexed
- Widgets: one question per screen, back button, step counter, progress bar
- SEO: `og:image` must be the raster `/og-image.png` (social networks do not render SVG);
  run `npm run render:og` after editing `src/templates/og-image.svg`
- Sitemap `lastmod` and JSON-LD dates derive from the build date, not hardcoded constants
