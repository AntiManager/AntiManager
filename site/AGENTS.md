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

When creating new lite chapter content:
1. Read the source `.md` from vault
2. Extract: principle, model/table, thesis excerpt
3. Create interactive widget (diagnostic/calculator)
4. Write HTML partial to `site/src/content/XX-slug.html`
5. Run `node site/build.js` to rebuild
6. Run `.\deploy.ps1` from `site/` directory to deploy

## Commands

```bash
cd site
node build.js           # Build site into dist/
npx serve dist          # Local preview
npm test                # Playwright tests
.\deploy.ps1            # Deploy to VPS (reads .env)
```

## SSH / Deploy

See `.env` for connection details. Default deploy configuration:
```
ssh -p {{REMOTE_PORT}} {{REMOTE_USER}}@{{REMOTE_HOST}}
nginx container: antimanager-web, root: {{REMOTE_DIR}}/current/
```

## Conventions
- Vanilla HTML/CSS/JS — no frameworks
- Lite-first content: principle + model + thesis + widget + download button
- All 22 chapters indexed
- Widgets: one question per screen, back button, step counter, progress bar
