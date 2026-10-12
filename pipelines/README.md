# Pipelines

Two content pipelines share one vault and the site. Each pipeline keeps its own
tooling and `.gitignore`; shared vault utilities live in `common/`.

| Pipeline | Direction | Entry points |
|----------|-----------|--------------|
| `obsidian-to-site/` | Obsidian articles & materials → site HTML/PDF | `article_readiness.py`, `md_to_partial.py` |
| `proc-library/` | source `Proc_library/` → Obsidian process library | `engine.py`, `author_*.py`, `rollup.py`, `token_scan.py` |
| `common/` | shared vault utilities | `guard_encoding.py`, `to_crlf.py` |

- Pipeline-1 procedure: `/full-article` command + `content-publisher` skill.
- Pipeline-2 procedure: `proc-library/README.md` (engine doc) + `.kilo/plans/`;
  design specs mirrored at `proc-library/specs/` (the vault copy stays canonical).
- The vault itself (articles and `Библиотека процессов/`) lives outside the
  repository; these pipelines transform it.
