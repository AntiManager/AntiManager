# AntiManager — Tech Context
> Updated: 2026-10-11

## Build
```bash
cd site
npm run build   # runs build.js — generates static HTML from Markdown+JSON
npm run optimize:thinkers  # generate .webp siblings for thinker photos (Playwright canvas)
```

## Config
- `.env` (gitignored): Yandex Metrika ID, deploy secrets
- `site/package.json`: `antimanager-site`
- `kilo.json.example`: Kilo project config template

## Git
- Branch: `main`
- Remote: origin (GitHub fetch + GitHub+GitVerse push), gitverse (explicit push)
- Kilo agents (2): book-editor, vault-auditor
- Kilo skills (8): book-writing, content-publisher, article-readiness, diagram-architect, management-research, site-designer, vault-indexer, web-developer
- Kilo commands (10): fix-encoding, link-ideas, new-article, new-chapter, new-tool, vault-audit, vault-index, check-site, article-readiness, full-article

## Deploy
- `site/deploy.ps1`
- Nginx (`site/deploy/nginx.conf`): shared security headers at server level, locations set only
  `expires` (assets 7d, HTML 5m); `www→apex` 301, trailing-slash 301, custom 404, HSTS.
