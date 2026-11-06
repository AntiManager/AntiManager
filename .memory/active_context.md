# AntiManager — Active Context
> Updated: 2026-11-06 · No active plan. `1793969494727` (site IA refactor) is closed and archived;
> new plans go to `.kilo/plans/`.

## State

- **Plan complete (S11, 2026-11-06).** Releases A/B/C are built, tested and deployed
  (Release B/C went live 2026-11-06). Final gate on a fresh build: unit 43/43, `npm test` 378 passed /
  6 skipped (3 projects), `check:links` 85 pages 0/0/0/0, `check:redirects` no drift, Pagefind
  82 indexed / 15,946 words. `VERSION` = `20261106d`.
- **Working tree uncommitted** — 124 entries (90 modified, 34 untracked); no commit was requested.
  Release A went live from this same tree on 2026-11-06.
- **Closeout repairs:** `site/AGENTS.md` (`/playbook/`, retired HQ CTA, «Имитация развития»),
  `.kilo/AGENTS.md` (canonical routes, no active plan), `.kilo/harness.md` (gate baselines),
  `.memory/system_patterns.md` (route map). `task-conversion` gained the rename-sweep rule;
  global `HARNESS.md` updated.

## Next

- **User-owned:** 12.1 hero value proposition, 12.3 named author/experience facts, Metrika goal
  names (12.6), `/start/` editorial approval.
- No open technical P0/P1. Start new work as a fresh local plan in `.kilo/plans/`.

### Resume commands

```powershell
cd site; npm test
cd site; .\scripts\verify-deploy.ps1
cd site; npm run check:links; npm run check:redirects
```

### Already read (do not re-read)

- `site/build.js` (routes/sitemap/home/catalog/playbook/start/method/about/search/renderPage),
  `src/routes.js`, `src/lib/{catalog,legacy-routes,escape}.js`,
  `scripts/{gen-redirects.js,check-links.mjs}`, `src/templates/base.html`,
  `src/components/{header,footer}.html`.
- `site/deploy.ps1`, `scripts/verify-deploy.ps1`, `deploy/{nginx.conf,redirects.conf}`,
  `package.json`, `playwright.config.js`, `pagefind.yml`.
- `css/brutalist.css` (header/search/home/footer/filters/cards/genome/method/about,
  `.chapter-nav`, `.related-*`, `.thinker-links`, `.lead-magnet`, `.offer-facts`);
  `js/{brutalist,search,analytics}.js`; `tests/{search,home,nav-mobile,book-facets,genome,about,
  ux-critical,a11y,analytics}.spec.js`; `unit/build-{search,home,routes,start-book,about,genome,
  escape,seo,related}.test.js`.
- `site/src/content/genome/landing.html` offer + lead magnet; 18 chapter widget partials.

## Hot rules

- Paths: workspace `C:\Work\Python`; vault `C:\Work\Personal Vault`; `.env` at repo root.
- Toolchain: Python 3.14 + `ftfy python-docx openpyxl pytest`; Pandoc 3.13; Node 26 + Pagefind 1.6;
  Playwright chromium; tests use port 3100 (`PLAYWRIGHT_PORT`), never 3000.
- `/playbook/` is canonical; `/book/` is a single-hop 301. Series «Имитация развития».
  `/about/headquarters/` and `/headquarters/` 301 to `/contact/` (club retired).
- `npm test` = unit + `check:redirects` + build (site + Pagefind) + `check:links` + Playwright.
  `node build.js` alone wipes `dist/` and skips the search index; unit tests share `dist/`
  (`--test-concurrency=1`); `check:links` scans `dist/`.
- Search: `/search/` stays noindex, out of the sitemap, without `data-pagefind-body`; a future CSP
  with `script-src` needs `'self'` and `wasm-unsafe-eval`; Pagefind matches token prefixes.
- Widgets: one static back button outside `#<id>Question` (AX15).
- Deploy: `npm test` first; `nginx -t` on a throwaway `nginx:alpine`; SSH 2222 is flaky (the copy
  may already be live); Caddy reload may refuse `localhost:2019` (non-fatal); `verify-deploy.ps1`
  must probe 3xx with `HttpClient`, not `Invoke-WebRequest -MaximumRedirection 0` on PS 7.6.
- Generators default to the vault (`--vault`; `check_system_cards.py` positional); `--check`
  compares marker regions — re-run the generator, never hand-edit markers.
- Obsidian MCP writes on Cyrillic paths are broken — use `Write`/`Edit` + Python; guard encoding.
- `check_artifacts.py` takes the library root, not the vault root.
- Data SSOT: `articles.json` + topics + series; only `published` renders. Every article `.md`:
  title block + `---`; no Mermaid.
- `render:pdf` two-pass; PDFs churn on every run — restore untouched tracked PDFs before commit.
- Home is exactly six sections; `#system-map` is a container, not a section.
- Long H1 words are capped, not split (`.content-page h1`, `.hero-gen h1`, `.documents-hub h1`,
  `.privacy-page h1`); `/method/` `#offer` sits before `#problem`.
- Skills 8 / commands 10 / agents 0; `/check-site` = `npm test`. History → `.memory/archive/`.
