---
name: content-publisher
description: Moving Obsidian articles into the site's HTML pages — extracting content, tools, cases
---

# Skill: content-publisher

Content is two-tier per theme: the **topic landing** `/weapons/<slug>/` (interactive
model) and the **full text** `/weapons/<slug>/full/` (complete article + materials).

## Process — landing (lite)

1. Source — a `.md` from the vault (path in `.env`, variable `ARTICLES_DIR`)
2. Extract: principle, model/table
3. Design an interactive widget (diagnostics/calculator/test) based on the article material
4. Write an HTML partial to `site/src/content/XX-slug.html` (name = slug from `site/src/data/weapons.json`)
5. Put `{{read_more}}` where the path to the full text belongs (build renders a read-more
   card only if `src/content/full/XX-slug.html` exists; otherwise the token renders empty)
6. Build: `cd site; node build.js`
7. Deploy: `.\deploy.ps1`

## Process — full text

1. Convert the vault `.md` into `site/src/content/full/XX-slug.html` (H2/H3 headings drive
   the TOC automatically; `{{read_more}}` is not used here)
2. Remove the landing's `Тезисный отрывок` section and put `{{read_more}}` in its place
3. Build, then `npm run render:pdf` → `site/materials/<slug>.pdf`
4. Rebuild so the materials block links the PDF, then deploy

## Mapping article content → HTML blocks

| Article content | Partial block |
|---|---|
| Title + subtitle | `weapon-hero` (landing) / `full-hero` (full; zone — from `weapons.json`) |
| Principle / key idea | `.block-principle` |
| Path to the full text | `{{read_more}}` → `.read-more-card` (landing) |
| Tables, classifications | `<table>` (wrap wide tables in `.table-wrap`) |
| Cases from practice | `.block-case` |
| Step-by-step protocol / test | `.widget` + `.progress-bar` (landing only) |
| Materials (PDF + extras) | `.materials-section`, generated on the full page from `materials.json` + `materials/<slug>.pdf` |

## Materials

- Article PDF: auto-detected from `site/materials/<slug>.pdf` (generate with `npm run render:pdf`).
- Extra artifacts (checklists, templates): `site/materials/<slug>/<file>` plus an entry in
  `site/src/data/materials.json` — `href` must be `/materials/<slug>/<file>`.
- Never promise future files; the block shows only what exists.

## MCP integration

- Obsidian MCP — when you need to programmatically extract article structure (many files)
- GitHub MCP — when committing and pushing finished pages
