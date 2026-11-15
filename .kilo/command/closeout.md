---
description: Close out a session — run the gate, check artifacts, then write memory once
---

Close the session in this order. Never touch memory before the gate passes.

1. Read `.kilo/harness.md` §Verify and pick the gate that matches the change:
   - `site/**` changed → `Push-Location site; npm test; Pop-Location`
   - vault generators/checkers changed → each changed script with `--check` exits 0
   - harness/docs/config only → `pwsh -NoProfile -File "$env:USERPROFILE\.config\kilo\scripts\verify_repo.ps1" -Repo "C:\Work\Python\AntiManager"`
2. Check artifacts: `git status --porcelain` must show only intended files. `.run/` is ignored
   scratch (only the 8 `a3_*` scripts are tracked); `.kilo/reports/` is local-only. Delete session
   scratch instead of staging it.
3. Draft the resume pointer and the ledger entry; do not write yet.
4. Write `.memory/active_context.md` (≤3 KB) and `.memory/progress.md` (≤8 KB) once each, full file,
   with no tool call between the writes. Older details go to `.memory/archive/`.
5. Stop. Do not commit unless the user asked; record `VERSION` ↔ SHA only after a deploy.

Expected success: the gate's own success line (e.g. `STATUS: OK`) and
`git status --porcelain` empty or only intended files.
