# AntiManager — Active Context
> Updated: 2026-10-11

## Review + cleanup done — committed/pushed this session (2026-10-11)
`/review uncommitted` (reviewer subagent) found and applied: (1) **major** — the new full-page
`description` came from raw article prose → escaped once at construction (build.js) so it can't
break the `<meta>` attribute (the pre-existing `{{description}}` substitution stays raw; all other
inputs are load-sanitized); (2) `gzip_types` restored `text/html` (unrelated removal); (3) `date`
field now validated `^\d{4}-\d{2}-\d{2}$` at load (HTML attr / sitemap XML / JSON-LD) else dropped;
(4) `.filter-btn:hover` color → `--color-accent-text` (was still `--color-accent`, ~4.1:1); (5)
Yandex unit assertion pinned to the exact `yandex_XXXXXXXXXXXXXXXX.html` placeholder and the test
build sets `YANDEX_VERIFICATION:''` (env-independent); (6) breadcrumb builder simplified. Harness:
`site/AGENTS.md` gained the nginx `add_header`-inheritance lesson + 23-weapons count;
`.memory/tech_context.md` Deploy line synced. Suite re-run: **unit 8/8, e2e 102/102**. Committed + pushed.

## Next session (resume) — editorial / SEO
- Next editorial: the DRAFT series **30–35** (JDR-аудит/экспресс/middle/plant-manager, сборник
  тестов, концепция развития НЦ/НС) — each needs frontmatter + related sections + case/conclusion
  before `/full/`.
- SEO Phase 2 remaining (accepted/deferred): CSP still lacks `default-src`/`script-src` (inline
  Metrika/widgets); Metrika `webvisor` vs `/privacy/` wording (user-deferred).
Resume pointers: nginx conf validated on a local `nginx:alpine` container; `.webp` siblings live in the
untracked `Фото_мыслителей/` (gitignored) and are regenerated via `npm run optimize:thinkers`; per-article
`date` fields are in `weapons.json`.

## Latest: SEO & accessibility hardening (2026-10-11)
Full live-site audit + fixes, all verified. **Uncommitted** (working tree), on top of the
parked `SEO Phase 2` edits (all weapons `published`, fabricated landing stats removed).

- **nginx** (`site/deploy/nginx.conf`, verified on a local `nginx:alpine` container):
  custom 404 (`error_page 404 /404/index.html`), `www→apex` 301, trailing-slash 301,
  HSTS + `Content-Language: ru`, de-duplicated `Cache-Control` (server-level `add_header`
  + per-location `expires` only). Deploy must still run `nginx -t`.
- **build.js**: unique `/full/` meta description (first paragraph via `summaryText`);
  landing description grammar fixed; JSON-LD enriched (`@id` graph, `Organization.logo`,
  `mainEntityOfPage`, `image`); `og:image:alt`/`twitter:image:alt`; `datePublished` from the
  per-article `weapons.json` `date` (added, sourced from git), `dateModified` = build date;
  sitemap `lastmod` per article; `YANDEX_VERIFICATION` env replaces the `XXXX` placeholder;
  `.well-known/security.txt`; thinker photos as `<picture>` (webp + fallback, guarded).
- **CSS**: accessible text tokens `--color-muted #8B95A8` (~6.5:1) and
  `--color-accent-text #EF4444` (~5.3:1); `--color-steel` kept for borders/filled surfaces;
  zone-subtitle opacity removed. Footer nav added (fixes orphan `/about`, `/headquarters`, `/privacy`).
- **Images**: `scripts/optimize-thinkers.js` (Playwright canvas → `.webp`), `npm run optimize:thinkers`; saved ~1.2 MB.
- **Content**: article 05 full partial `h4`→`h3` (cleared the heading jump).
- **Tests**: unit 8/8, e2e **102/102** (new AX14 contrast test; build-seo gains items 9–14).
- **Not fixed (accepted):** CSP still lacks `default-src`/`script-src` (inline Metrika/widgets);
  Metrika `webvisor` vs `/privacy/` wording (deferred by user).

## Current Task
**Two-tier theme pages** (landing → full text → materials) — implemented, committed
(`0e4e511`) and **deployed** (live-verified): `/weapons/<slug>/` stays interactive and
shows a `.read-more-card` (`{{read_more}}` → `/weapons/<slug>/full/`) instead of the
dead «Тезисный отрывок»; the full page carries the complete article (static H2/H3 TOC,
reading progress, 4-level breadcrumb) plus an honest `.materials-section` (article PDF +
declared extras, print fallback). Fake site-wide «Материалы к статье / Хочу PDF» removed.
**Rollout:** 00, 02–23 built, tested (unit 8/8, e2e 99/99) and deployed.
**Article 21 «Два типа управления»** done (committed `75bc1c7`, live-verified); **article
22 «Ударить по траектории»** done: vault restructured to the norm (title block `---`;
all `###` sections re-levelled to `##`, clearing the 1 heading jump; 2 double-encoded
wiki-link display texts repaired — L83 «инжиниринг на уровне причин», L189 «контракт с
самим собой» + broken target `Два_типа_управления` → `21_Два_типа_управления»;
unsourced «90% людей» hedged; `book/draft` dropped; tools +PDCA, chapters +06/+21).
Readiness 12/12, jumps 0, wiki 20; landing `{{read_more}}`;
`full/22-udarit-po-traektorii.html` = 14 h2. The converter now drops the legacy bold
«Связанные главы:» trailer (recurring chrome — was leaking in 20/21 too).
**Article 23 «Коммуникационный конструктор»** done (committed `516d8b8`, live-verified):
vault Layer 2 — frontmatter + title block (Концепция/Механизм) + 2 inline crosslinks
([[14_Управление_живой_системой]], [[Pre-Mortem]]) + «Связанные инструменты/главы»;
readiness 8/12 → 12/12 (jumps 0, wiki 11). New weapon `23 kommunikacionnyy-konstruktor`
(zone `changes`) + landing (principle + 5-model table + 3-question model-picker widget) +
`/full/` (14 h2) + PDF. `build-seo.test.js` landing plural 22→23 «главы» (count-pinned).
**Next editorial:** the DRAFT series **30–35** (JDR-аудит/экспресс/middle/plant-manager,
сборник тестов, концепция развития НЦ/НС) — a different set; each needs frontmatter +
related sections + case/conclusion before /full/.
Per-article history → `.memory/archive/progress-history-2026.md`.

Publish-readiness: 00/01/02–23 all READY (articles 10, 15, 17, 18, 20, 21 at 11/12 — the
single miss is the `case` heading false gap; their cases are inline/bold body labels).
Remaining vault articles 30–35 are DRAFT (different series; see “Next editorial”).
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
- **Phase 1 COMPLETE — "subprocess-level v1" FROZEN (T1.5).** Unified SME template
  in the personal vault `Библиотека процессов\`: `specs/T0.1…T0.8` + `_template-stub.md`;
  engine (parser + validator + CLI + tools) at `.kilo/process-engine/`. Log:
  `.kilo/plans/1791721561689-…-execution-log.md`; plan §11/§12.
- T1.1 split `Proc_lib.md` → vault `library\` (T1.6 later added `INF` + the 7 `SL_*`);
  T1.2 hierarchy + goals; T1.3 APQC crosswalk 79/79; T1.4 seams; T1.6 `INF`+`LOG`.
  **Baseline: 20 groups / 79 processes / 238 subprocesses / 995 operations**, 1332
  nodes / 0 edges. Do NOT touch `Proc_library/library/`.
- **T1.5 freeze gate:** 0 errors at LIBRARY/GROUP/PROCESS/SUBPROCESS (goals present,
  APQC 79/79, §4.7/§4.9/§4.10 0, 0 dup codes); all 4823 errors + 3848 warnings are
  OPERATION-level (→ T2.2); **client-identity token scan 0** (new `token_scan.py`;
  fixed QUAL-06-02 «500 тыс. руб.»). Record: `.kilo/process-engine/freeze_v1_subprocess.json`
  (signature `sha256 a506b2f5…`). Suite **15/15**. `SLA` + `ENG-04` stay OUT of the
  template (holding-grade; user decision — supersedes T0.1 D1 for these two).
- **Next:** Phase 2 (operations + flow graph), pilot **Planning** (`PLAN` + `SL_PLAN`).
- **Resume:** engine `.kilo/process-engine/engine.py`; validate
  `python .kilo/process-engine/engine.py "<…>\Библиотека процессов"` (vocab v0.1/44);
  token scan `python .kilo/process-engine/token_scan.py "<…>\Библиотека процессов\library"`;
  tests `python -m pytest -q -p no:cacheprovider`.
- Note: `.kilo/process-engine/` is git-excluded; the `silicon-goal` worktree carries a
  mirror copy — keep them in sync.

## Hot rules / deferred
- Metrika/Webvisor untouched; `webvisor:true` vs `/privacy/` wording — deferred by user (compliance risk).
- `yandex-verification` meta needs the user's code.
- GitVerse token in `.git/config` `origin.pushurl` (plaintext) — rotate + move to credential helper/SSH (HIGH).
- `chapters.json`/`tools.json` — unreferenced dead data (remove or wire), decide separately.
- `build.js` `VERSION` static vs dynamic `BUILD_DATE` — couple on next release.
- Residual: `content_body` is raw HTML (malicious PR to `src/content/*.html`); rely on PR review/branch protection.
- **SSH 2222 flaky (VPS):** `Test-NetConnection` to `5.129.221.85:2222` intermittently
  succeeds while `ssh`/`scp` time out; ping + 443 stay green. `deploy.ps1` may abort on a
  mid-run ssh timeout although the dist upload/container restart already landed —
  **verify live (GET 200) before re-running**; the trailing Caddy reload is optional.
