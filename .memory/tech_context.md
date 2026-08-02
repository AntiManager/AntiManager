# AntiManager — Tech Context
> Updated: 2026-08-02

## Build
```bash
cd site
npm run build   # runs build.js — generates static HTML from Markdown+JSON
```

## Config
- `.env` (gitignored): Yandex Metrika ID, deploy secrets
- `site/package.json`: `antimanager-site`
- `kilo.json.example`: Kilo project config template

## Git
- Branch: `main`
- Remote: origin (GitHub fetch + GitHub+GitVerse push), gitverse (explicit push)
- Kilo agents: book-editor, vault-auditor
- Kilo skills: book-writing, content-publisher, diagram-architect, management-research, site-designer, vault-indexer, web-developer

## Deploy
- `site/deploy.ps1`
- Nginx: immutable→must-revalidate cache
