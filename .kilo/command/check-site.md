---
description: Check the site — build and run the Playwright suite
---

Build the static site and run the full Playwright regression suite.

```powershell
Push-Location site
node build.js
npx playwright test
Pop-Location
```

Return the `passed`/`failed` counts from the Playwright summary. The suite is expected to be 84 passed (28 per project: mobile, tablet, desktop).
