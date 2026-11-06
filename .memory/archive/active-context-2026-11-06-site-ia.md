# Active context archive — site IA refactor (2026-11-06)

Removed from `.memory/active_context.md` during the 2026-11-06 harness-optimization
closeout. The site-IA plan is closed; this is history, not a resume pointer.

## Closeout repairs

- `site/AGENTS.md` (`/playbook/`, retired HQ CTA, «Имитация развития»).
- `.kilo/AGENTS.md` (canonical routes, no active plan).
- `.kilo/harness.md` (gate baselines).
- `.memory/system_patterns.md` (route map).
- `task-conversion` gained the rename-sweep rule; global `HARNESS.md` updated.

## Already read (do not re-read unless the file changed)

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
