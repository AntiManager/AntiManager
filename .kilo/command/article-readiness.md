---
description: Assess publish-readiness of vault articles (objective screen + editorial checklist)
---
Assess article readiness. Optional `$1` = article number to focus on (e.g. `23`).

1. Run the deterministic screen:
   `python .kilo/scripts/article_readiness.py`
   → writes `.kilo/reports/article-readiness.md`.
2. Read that report with the Read tool (never trust Cyrillic console output).
3. Load the `article-readiness` skill (`.kilo/skills/article-readiness/SKILL.md`)
   and apply the Layer 2 editorial checklist to every non-READY article, or only
   to `$1` when given.
4. Report per article: verdict (`READY` / `NEEDS-EDIT` / `DRAFT`), the failed
   Layer 1 checks, and concrete fixes from Layer 2. Do not change any vault file
   unless the user asks for the fixes.
