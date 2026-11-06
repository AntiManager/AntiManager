const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

// Release B (11.6): smoke-level axe pass over the main page types. Only
// critical violations fail the build; lower-impact findings stay visible in
// the report so they can be scheduled deliberately instead of blocking deploy.
const PAGES = [
  { path: '/', label: 'home' },
  { path: '/playbook/', label: 'playbook hub' },
  { path: '/playbook/processy/', label: 'chapter' },
  { path: '/method/', label: 'method hub' },
  { path: '/articles/practice/raschet-oee/', label: 'article' },
  { path: '/search/', label: 'search' },
];

test.beforeEach(async ({ page }) => {
  await page.route('**/mc.yandex.ru/**', (route) => route.abort());
});

test.describe('AX — axe smoke', () => {
  for (const target of PAGES) {
    test(`${target.label}: no critical violations`, async ({ page }) => {
      await page.goto(target.path);
      await page.waitForLoadState('networkidle');

      const results = await new AxeBuilder({ page }).analyze();
      const critical = results.violations.filter((violation) => violation.impact === 'critical');
      const summary = critical.map((violation) => ({
        id: violation.id,
        help: violation.help,
        nodes: violation.nodes.map((node) => node.target.join(' ')),
      }));

      expect(summary, JSON.stringify(summary, null, 2)).toEqual([]);
    });
  }
});
