# obsidian-to-site

Turn articles and materials authored in Obsidian into site pages.

- `article_readiness.py` — 12-point publish-readiness screen for a vault
  article; report to `.kilo/reports/` (gitignored).
- `md_to_partial.py` — convert one vault `.md` into a site `/full/` partial
  (H2/H3 drive the TOC).
- `add-fm-00.py` — one-off frontmatter helper (article 00), retained for history.

Shared vault utilities: `../common/guard_encoding.py`, `../common/to_crlf.py`.

Procedure: `.kilo/command/full-article.md` + the `content-publisher` skill.
