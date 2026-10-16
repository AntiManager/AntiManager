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
`npx playwright test`. Report the unit pass/fail counts and the Playwright
`passed`/`failed` counts straight from the run output — there is no fixed number
to hard-code (the suite grows per feature); a green run means 0 failures.
