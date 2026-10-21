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
    src/content/     # Topic-landing partials (XX-slug.html) + contact.html
    src/content/full/# Full-text article partials (XX-slug.html) — presence enables /full/
    src/content/genome/ # «Геном завода» section partials (landing.html, role.html)
    src/content/articles/ # «Статьи» long-read partials (XX-slug.html)
    src/lib/         # escape.js (shared build helpers)
    materials/       # Downloadable assets: <slug>.pdf (generated) + <slug>/ (authored extras)
    scripts/         # render-og.js, render-pdf.js
    css/             # Stylesheets
    js/              # JavaScript
    fonts/           # Self-hosted woff2
    tests/           # Playwright UX tests
    unit/            # build unit tests (node --test)
    feedback/        # feedback-form microservice (Python stdlib)
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

A consulting-service section, not an arsenal weapon. Indexable static pages rendered by
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
Section styles live in the `/* === GENOME SECTION === */` block of `css/brutalist.css`.

## «Экспресс-аудит» (`/genome/audit/`)

A static tool page nested under Геном: the 40-criterion express checklist with 0–5 anchors (one
native `<details>` per criterion) plus a fillable XLSX
(`materials/ps-express-audit/express-audit-ps.xlsx`). Source of truth:
`Аудит ПС/Экспресс-чек-лист-аудита-ПС.md` in the vault; the full 120-criterion checklist is never
published.
- `src/content/genome/audit.html` is authored, but its seven `<!--AUDIT:*:START/END-->` regions are
  generated offline by `.kilo/scripts/gen_ps_audit_page.py` (same pattern as the role documents).
  Run it after vault edits and commit the regenerated partial together with the workbook.
  `build.js` throws when a marker region is empty, so an un-generated partial cannot ship empty
  sections. There is no npm script: the generator needs the local vault.
- `gen_ps_audit_page.py --check` compares marker inner regions and workbook cell/formula values
  (never the zip bytes, which churn) and exits 1 on drift.
- `<details>` works without JS; `js/audit.js` adds toggle-all, opening the criterion named in the
  URL hash, and expanding everything before printing (restored after). Print CSS re-enables
  `.section-title`, which the global print block hides, and keeps `.audit-block-title` visible.
- The download href carries `?v=<vault version>`: bump the vault frontmatter `version` and the
  authored href together.
- The request-context slug is `audit`: registered in both `js/contact.js` and
  `feedback/server.py` (unknown packs are silently dropped by the service, so update both and
  redeploy the feedback container with the site).
- Section styles live in the `/* === GENOME AUDIT (/genome/audit/) === */` block of
  `css/brutalist.css`.

## «Карта систем» (`/genome/systems/`)

A nested Геном page that publishes the 14 system cards as a uniform 12-field template, plus a
blank card template for a client's own systems. Source of truth: `Методология ПС/Карточки-систем.md`
in the vault; the client edition `Заказчики/КАБЭКС/Карта-систем-собственнику.md` is generated,
never hand-edited.
- `src/content/genome/systems.html` is authored; its three `<!--SYSTEMS:META/SUMMARY/CARDS:*-->`
  regions are generated offline by `.kilo/scripts/gen_systems_page.py`. Run it after vault edits
  and commit the regenerated partial together with the downloads. `build.js` throws on an empty
  marker region. There is no npm script: the generator needs the local vault.
- The same generator writes the compact owner document (`Заказчики/КАБЭКС/Карта-систем-собственнику.md`
  + `.docx` in the vault) and the blank template (`materials/ps-systems-map/system-card-template.md/.docx`)
  via pandoc; `--check` compares the marker regions, the owner Markdown and the template and exits
  1 on drift.
- The page reuses `.doc-cards` / `.doc-card` / `.doc-full` and the summary `.table-wrap`; page
  styles live in the `/* === SYSTEMS MAP (/genome/systems/) === */` block of `css/brutalist.css`.
- Discovery: a `.systems-entry` section on `/genome/` (deliberately not a seventh `.doc-card`, so
  the landing still renders exactly six role documents), a sitemap entry, and
  `unit/build-systems.test.js`. `/genome/systems/` is in the `ux-critical` no-hscroll path list.

## «Статьи» library (`/articles/`)

Topic-grouped long-reads. Route shape: `/articles/` (hub) → `/articles/<topic>/` (topic hub) →
`/articles/<topic>/<slug>/` (full article: TOC, FAQ, materials, series block, Telegram CTA).
Data lives in three files under `src/data/`:
- `article-topics.json` — locked topic taxonomy (`strategy`, `economics`, `management`, `digital`),
  each with a title, description and `order`;
- `articles.json` — one entry per article (`id`, `topic`, `order`, optional `series`, text fields,
  `date`, `tags`, `status`, four `faq` items);
- `article-series.json` — cross-topic series (`capability` = «Управление способностью»).

Only `status: published` entries render. Topic hubs are emitted only for topics with at least one
published article, so an empty taxonomy entry never ships a blank page. Article IDs are internal
file/data keys; the UI never shows numbering. Legacy `/strategy/...` URLs 301 to
`/articles/strategy/...` (nginx, server level).

Article partials are generated offline from the vault by
`.kilo/scripts/gen_article_partials.py` (Markdown links → real `<a>`; appends the «Читайте также»
interlinks block with `data-toc="skip"`). Every source `.md` must keep a `---` after the title
block: the converter drops everything through the first separator, so a missing one produces an
empty partial. Re-run the generator after vault edits, then commit the regenerated partial —
`node build.js` itself stays vault-independent. Site interlinks live only in
the generator, never in the vault `.md`: the converter drops Markdown links, and the vault keeps its
native `[[wiki]]` backlinks. Section styles: `/* === ARTICLES LIBRARY (/articles/) === */` in
`css/brutalist.css`; `.strategy-*` classes remain as one-release aliases for cached pages.

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
- The form is progressive: with JavaScript it POSTs JSON; without it the browser
  submits `application/x-www-form-urlencoded` natively, which `server.py` also parses
  (a checked consent checkbox arrives as `consent=on`) and answers with a small HTML
  notice when the request `Accept`s HTML. Do not break either path.
- Component focus styles must not kill the global ring: a `.field input:focus { outline: none }`
  rule outranks the global `:focus-visible { outline: 3px }` by specificity and silently removes
  the keyboard indicator. Rely on the global rule; change only `border-color` locally.
- Keep the page background on `html` (`html { background: var(--color-bg) }`), not only `body`:
  a body-only background leaves the canvas unpainted, which flashes white on mobile overscroll
  and renders white/transparent in full-page captures.
Section styles live in the `/* === CONTACT === */` block of `css/brutalist.css`.

## Commands

```bash
cd site
node build.js           # Build site into dist/
npx serve dist          # Local preview
npm test                # unit + Playwright tests
npm run test:unit       # unit tests only
npm run test:e2e        # Playwright only
npm run render:og       # regenerate src/templates/og-image.png from og-image.svg
npm run render:pdf      # render materials/<slug>.pdf from each full-text page (run after build)
npm run optimize:thinkers  # generate .webp siblings for thinker photos (run after adding a photo)
.\deploy.ps1            # Deploy to VPS (reads .env)
.\scripts\verify-deploy.ps1  # post-deploy live check: /genome/, /genome/role/, sitemap → exit non-zero on failure
```
Regenerate the genome role documents after vault edits (needs the local Obsidian vault):
`python ..\.kilo\scripts\genome_doc_build.py`
Regenerate the article long-read partials after vault edits (same vault):
`python ..\.kilo\scripts\gen_article_partials.py`

Unit tests run with `--test-concurrency=1`: any unit test that shells out to `build.js`
writes the shared `dist/`, so parallel test files would race. Keep that flag.
`build.js` accepts a `BUILD_DATE` env override (used by tests for deterministic dates).

`render:pdf` serves `dist/` and prints each `/full/` page in print media — never run it
concurrently with `build.js`/tests (they rewrite the shared `dist/`), or the PDF captures
stale markup (a phantom ~3× size jump / embedded images is the tell). It fails fast when a
target's `dist/` page is missing (instead of printing the 404 page) and retries a just-written
PDF 3× because Windows antivirus/indexers intermittently lock it. Wide inline SVGs
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
- `datePublished` and sitemap `lastmod` use each entry's `date` (`weapons.json` for weapon pages,
  `articles.json` for `/articles/` long-reads); `dateModified` and static-page `lastmod` use the build date
- Thinker photos ship as `<picture>` (generated `.webp` + original fallback); build guards on
  the `.webp` existing, so a missing generation degrades gracefully to the raster
- Long inline code/identifier chips (`.anchor-code`, `.cv`) must **wrap** (`overflow-wrap: anywhere`),
  never `white-space: nowrap` — a nowrap chip caused page-level horizontal scroll on `/genome/`
  (375/768px). The shared no-hscroll Playwright test (`ux-critical` AX04) guards this.
