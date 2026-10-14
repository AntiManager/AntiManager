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
    src/content/genome/ # «Геном завода» section partials (landing.html, role.html)
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

## «Геном завода» section (`/genome/`, `/genome/role/`)

A consulting-service section, not an arsenal weapon. Two indexable static pages rendered by
`build.js` from authored partials in `src/content/genome/`:
- `landing.html` — model, comparison, the free PLAN-group sample (3 processes / 11 subprocesses
  / 49 operations) and six document cards (05/06 link to the role page anchors).
- `role.html` — full role documents: the КУ package (levels 1–5 descriptors, question bank,
  cases, 360°) and the recruiter profile. The KU/profile block is generated offline from the
  Obsidian vault by `.kilo/scripts/genome_doc_build.py` (idempotent, fills the `<!--KU:*-->` /
  `<!--PROFILE:*-->`   markers). Re-run it after vault edits, then commit the regenerated partial —
  `node build.js` itself stays vault-independent.
- The generator emits an `<a>` only for servable targets (`http(s)`, `mailto:`, `#`, `/`);
  vault-relative and `.md` references are rendered as plain text, so a dead `.md` link can
  never leak onto the published page.

CTAs: commercial buttons open the feedback form (`/contact/?pack=…`); «Задать вопрос в Штаб» → `/headquarters/`.

## Contact / feedback form (`/contact/`)

The `/contact/` page hosts the feedback form. It is a static partial (`src/content/contact.html`,
wired in `build.js` with `js/contact.js`), so the site stays static. Submitting posts JSON to the
**same-origin** `POST /api/feedback`, proxy-passed by nginx to the `antimanager-feedback` container
(the `site/feedback/` microservice: Python stdlib, no deps) which forwards the message to the owner's
Telegram chat via the bot. The offer CTAs on `/genome/` and `cta-band` link to `/contact/` (with a
`?pack=` context slug); the footer carries «Связаться».

Rules:
- The **bot token never leaves the server**: it lives only in `$REMOTE_DIR/feedback.env`
  (`chmod 600`, passed with `--env-file`). Never put it in client JS, `dist/`, or the repo; the
  same-origin proxy exists precisely so the browser never needs the token or CORS.
- Because the endpoint is same-origin, the existing CSP (`form-action 'self'`, no `connect-src`)
  already permits it — do not move the endpoint to another origin without adding `connect-src`.
- The service is covered by `python -m unittest discover -s site/feedback/tests` (not by
  `npm test`, which only runs the site build + Playwright); the Playwright `contact.spec.js`
  intercepts `/api/feedback`, so no real network call is made in tests (the static `serve` cannot
  answer POST).
- Deploy the service (`site/feedback/deploy.ps1`) before/independently of the site; nginx resolves
  the container by name on the shared `vps_shared` network.
Section styles live in the `/* === GENOME SECTION === */` block of `css/brutalist.css`.

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
npm run optimize:thinkers  # generate .webp siblings for thinker photos (run after adding a photo)
.\deploy.ps1            # Deploy to VPS (reads .env)
.\scripts\verify-deploy.ps1  # post-deploy live check: /genome/, /genome/role/, sitemap → exit non-zero on failure
```
Regenerate the genome role documents after vault edits (needs the local Obsidian vault):
`python ..\.kilo\scripts\genome_doc_build.py`

Unit tests run with `--test-concurrency=1`: any unit test that shells out to `build.js`
writes the shared `dist/`, so parallel test files would race. Keep that flag.
`build.js` accepts a `BUILD_DATE` env override (used by tests for deterministic dates).

`render:pdf` serves `dist/` and prints each `/full/` page in print media — never run it
concurrently with `build.js`/tests (they rewrite the shared `dist/`), or the PDF captures
stale markup (a phantom ~3× size jump / embedded images is the tell). Wide inline SVGs
(e.g. the article-07 loss map, `viewBox 1500×1120`) are illegible at A4 print width and
print as a dark block: hide them under `@media print` (`.loss-map { display: none }`) and
keep a table/text equivalent right below.

## SSH / Deploy

See `.env` for connection details. Default deploy configuration:
```
ssh -p {{REMOTE_PORT}} {{REMOTE_USER}}@{{REMOTE_HOST}}
nginx container: antimanager-web, root: {{REMOTE_DIR}}/current/
```

nginx `add_header` is **not inherited** once a `location` declares its own, so shared
security headers live at server level and locations set only `expires` (assets 7d, HTML 5m).
Always `nginx -t` before/after deploy; validate a conf change on a throwaway `nginx:alpine`
container first, since a syntax error takes the site down.

TLS terminates at **Caddy** (nginx only sees http), so nginx emits relative redirects
(`absolute_redirect off`) — otherwise a 301 Location points to `http://` and adds a hop.
`deploy.ps1` copies `dist\.` (not `dist\*`): scp's glob skips dotfiles, and `.well-known/`
would never ship otherwise. SSH port 2222 is flaky — if the run aborts on the optional
Caddy-reload step after "Restarting Docker container", verify live (GET 200) before re-running.

## Conventions
- Vanilla HTML/CSS/JS — no frameworks
- Two-tier content: topic landing (principle + model + widget) → `/full/` (full text + materials)
- Materials are honest: only real files are linked (`materials/<slug>.pdf`, declared extras); never "coming soon"
- `materials.json` `href` must match `/materials/<slug>/<file>` (build rejects anything else)
- Print stylesheet (`@media print` in `brutalist.css`) strips site chrome for the PDF; regenerate PDFs with `npm run render:pdf`
- All 23 weapons indexed (00, 02–23; article 01 is `/manifesto/`)
- Widgets: one question per screen, back button, step counter, progress bar
- SEO: `og:image` must be the raster `/og-image.png` (social networks do not render SVG);
  run `npm run render:og` after editing `src/templates/og-image.svg`
- Article `datePublished` and sitemap `lastmod` use the per-article `date` in `weapons.json`;
  `dateModified` and static-page `lastmod` use the build date
- Thinker photos ship as `<picture>` (generated `.webp` + original fallback); build guards on
  the `.webp` existing, so a missing generation degrades gracefully to the raster
- Long inline code/identifier chips (`.anchor-code`, `.cv`) must **wrap** (`overflow-wrap: anywhere`),
  never `white-space: nowrap` — a nowrap chip caused page-level horizontal scroll on `/genome/`
  (375/768px). The shared no-hscroll Playwright test (`ux-critical` AX04) guards this.
