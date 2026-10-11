# AntiManager — Active Context
> Updated: 2026-10-11

## Current Task
**Two-tier theme pages** (landing → full text → materials) — implemented, committed
(`0e4e511`) and **deployed** (live-verified): `/weapons/<slug>/` stays interactive and
shows a `.read-more-card` (`{{read_more}}` → `/weapons/<slug>/full/`) instead of the
dead «Тезисный отрывок»; the full page carries the complete article (static H2/H3 TOC,
reading progress, 4-level breadcrumb) plus an honest `.materials-section` (article PDF +
declared extras, print fallback). Fake site-wide «Материалы к статье / Хочу PDF» removed.
**Rollout:** 00, 02–20 built and deployed. Article 19's previously blocked deploy is
**resolved** (SSH 2222 reachable again; the whole-`dist/` deploy shipped 19 + 20,
live-verified). **Next editorial: article 21 «Два типа управления».**
Per-article history → `.memory/archive/progress-history-2026.md`.

Publish-readiness: 00/01/02–20 all READY (articles 10, 15, 17, 18, 20 at 11/12 — the single
miss is the `case` heading false gap; their cases are inline/bold body labels).
Parked: SEO Phase 2 (publish 21 `review` weapons; replace landing stats 2 847 / 113 / 47).

**Editor procedure is codified** — follow the `content-publisher` skill and the
`/full-article <slug>` command; do not re-derive the steps. Key rules that still matter:

- Tests: unit **8/8**; Playwright **99/99** (33 × 3). Run all: `cd site; npm test`.
- **Env pitfall:** Docker Desktop holds host port 3000, so `npm test`'s Playwright
  `webServer` may reuse a dead port and abort all tests. If so, run the suite on an
  alternate port via a temp config (`webServer.port` + `use.baseURL`), and keep test
  requests relative to `baseURL` (AX07 fixed for this in `1e0c508`).
- Scripts: `npm run render:pdf` (`site/scripts/render-pdf.js`, Playwright print);
  `materials.json` `href` validated; `MATERIALS_FILE` env seam for tests.
- Lede = first `<p>` of the full partial — keep it a short standfirst (split a long
  preface paragraph); a part subtitle must be a non-`<p>` element (`.full-part-lede`).
  No mermaid runtime — convert ```mermaid fences to lists/flow text.
- **Two-pass PDF rule:** `build → render:pdf → build → render:pdf → build` (the first
  render runs before the article's own PDF exists). Every render rewrites the PDF
  `/CreationDate` (~12-byte diff) — `git checkout -- site/materials` restores untouched
  PDFs; commit only genuinely new/changed ones.

## Harness state
- Skills 8, commands 10 (+`/full-article`), agents 2. MCP: obsidian, github (project
  `.kilo/kilo.json`), context7 (global `kilo.jsonc`); `web-search` declared but dead.
- Article 01 site: `build.js` manifesto rendered from structured
  `manifestoValues/manifestoPrinciples/manifestoClosing` (drives `/manifesto/` and the
  landing teaser — no drift).
- `article-readiness` skill + `/article-readiness` + `.kilo/scripts/article_readiness.py`
  (report in gitignored `.kilo/reports/`); reusable `.kilo/scripts/md_to_partial.py`.
- Landing lite tables and `weapons.json` subtitles are canon-checked against the vault.
- `/check-site` runs the full suite (`npm test`); `vault-indexer` stale `.gigacode/`
  exclusion removed.
- Memory compacted 2026-10-11: history → `.memory/archive/` (`progress-history-2026.md`,
  `active_context-2026-09.md`). `.kilo/process-engine/` is git-excluded
  (`.git/info/exclude`) — force-add only to commit it deliberately.

## Process-library refactor (plan 1791721561689) — parallel track
- **Phase 0 (specs) + T1.1 done.** Unified SME template in the personal vault
  `Библиотека процессов\`: `specs/T0.1…T0.8` + `_template-stub.md`; engine (parser +
  validator + CLI) at `.kilo/process-engine/` (11/11 tests). APQC = groups primary +
  crosswalk; engine kept in AntiManager (git-excluded). Log:
  `.kilo/plans/1791721561689-…-execution-log.md`.
- `Proc_lib.md` split → vault `library\`: `INDEX.md` + 12 group files
  (`STRAT ORG ENG ANLZ PLAN MFG MNT QUAL HRP ENV IMPR EMG`). Regression gate PASS:
  759 nodes / 0 edges; 12 groups / 60 proc / 130 subproc / 557 ops. Do NOT touch
  `Proc_library/library/`. Deferred: `technologies/*.md` vendoring; group cross-ref
  anchors → T1.4.
- **Next:** T1.2 — normalize hierarchy per group (`LIBRARY→GROUP→PROCESS→SUBPROCESS`),
  unified coding; goal per PROCESS/SUBPROCESS.
- **Resume:** engine `.kilo/process-engine/engine.py`; validate
  `python .kilo/process-engine/engine.py "<…>\Библиотека процессов"` (vocab v0.1/44);
  re-split `split_library.py`; tests `python -m pytest -q -p no:cacheprovider`.
- Parallel Agent Manager worktree `silicon-goal` is stale by one commit and carries
  duplicate article-18 edits — reset it to `main` before committing process work.

## Hot rules / deferred
- Metrika/Webvisor untouched; `webvisor:true` vs `/privacy/` wording — deferred by user (compliance risk).
- `yandex-verification` meta needs the user's code.
- GitVerse token in `.git/config` `origin.pushurl` (plaintext) — rotate + move to credential helper/SSH (HIGH).
- `chapters.json`/`tools.json` — unreferenced dead data (remove or wire), decide separately.
- `build.js` `VERSION` static vs dynamic `BUILD_DATE` — couple on next release.
- Residual: `content_body` is raw HTML (malicious PR to `src/content/*.html`); rely on PR review/branch protection.
