# AntiManager — Tech Context
> Updated: 2026-10-21

## Build
```bash
cd site
npm run build               # build.js — static HTML/partials → dist/
npm test                    # unit (node --test) + Playwright
npm run render:pdf          # PDF for /full/ and /articles/ (after build; never concurrent with build)
npm run render:og           # og-image.png from og-image.svg
npm run optimize:thinkers   # .webp siblings for thinker photos
python -m unittest discover -s site/feedback/tests   # feedback microservice
```

## Config
- `.env` (gitignored): Yandex Metrika ID, deploy secrets
- `site/package.json`: `antimanager-site`
- `.kilo/kilo.json.example`: Kilo project config template

## Git
- Branch: `main`
- Remote: origin (GitHub fetch + GitHub+GitVerse push), gitverse (explicit push)
- Kilo agents (2): book-editor, vault-auditor
- Kilo skills (8): book-writing, content-publisher, article-readiness, diagram-architect, management-research, site-designer, vault-indexer, web-developer
- Kilo commands (10): fix-encoding, link-ideas, new-article, new-chapter, new-tool, vault-audit, vault-index, check-site, article-readiness, full-article

## Deploy
- `site/deploy.ps1` (site) and `site/feedback/deploy.ps1` (feedback microservice)
- TLS terminates at Caddy; nginx sees http (relative redirects, `absolute_redirect off`)
- Nginx (`site/deploy/nginx.conf`): shared security headers at server level, locations set only
  `expires` (assets 7d, HTML 5m); `www→apex` 301, trailing-slash 301, custom 404, HSTS.
- `POST /api/feedback` is proxied same-origin to the `antimanager-feedback` container; the bot
  token lives only in the server-side `feedback.env` (never in client JS or the repo).
- SSH port 2222 is flaky: the optional Caddy-reload step may time out after the container restart —
  verify live (GET 200) before re-running.
