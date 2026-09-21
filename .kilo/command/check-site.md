---
description: Check the site — build and run the full test suite
---

Build the static site and run the full test suite (unit + Playwright).

```powershell
Push-Location site
node build.js
npm test
Pop-Location
```

`npm test` = `npm run test:unit` (Node test runner, `--test-concurrency=1`) followed by
`npx playwright test`. Return the unit pass/fail counts and the Playwright
`passed`/`failed` counts. Expected: 5 unit tests; 99 Playwright tests
(33 per project: mobile, tablet, desktop).
