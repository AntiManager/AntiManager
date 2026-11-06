const { defineConfig, devices } = require('@playwright/test');

// Dedicated port: 3000 is commonly occupied by other local dev servers, and
// `reuseExistingServer` would silently point every test at a foreign app.
const PORT = process.env.PLAYWRIGHT_PORT || 3100;

module.exports = defineConfig({
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html', { outputFolder: 'playwright-report' }]],
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:' + PORT,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'mobile',
      use: { viewport: { width: 375, height: 667 } },
    },
    {
      name: 'tablet',
      use: { viewport: { width: 768, height: 1024 } },
    },
    {
      name: 'desktop',
      use: { viewport: { width: 1280, height: 800 } },
    },
  ],
  testDir: './tests',
  snapshotPathTemplate: '{testDir}/snapshots/{projectName}/{testFilePath}/{arg}{ext}',
  webServer: {
    command: 'npx serve dist -l ' + PORT,
    port: Number(PORT),
    reuseExistingServer: !process.env.CI,
  },
});
