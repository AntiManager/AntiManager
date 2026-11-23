const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

// Release B (11.6): smoke-level axe pass over the main page types. Only
// critical violations fail the build. `serious` findings are attached to the
// report as a visible backlog; promoting them to the gate is a separate
// decision after reviewing contrast on the black-and-red palette.
const PAGES = [
  { path: '/', label: 'home' },
  { path: '/playbook/', label: 'playbook hub' },
  { path: '/playbook/processy/', label: 'chapter' },
  { path: '/method/', label: 'method hub' },
  { path: '/articles/practice/raschet-oee/', label: 'article' },
  { path: '/search/', label: 'search' },
  { path: '/start/', label: 'start' },
  { path: '/contact/', label: 'contact' },
  { path: '/method/audit/', label: 'express audit' },
  { path: '/playbook/antikrizis/full/', label: 'full chapter' },
  { path: '/articles/strategy/antihrupkaya-strategiya/', label: 'strategy article' },
  { path: '/products/', label: 'products' },
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
      const serious = results.violations.filter((violation) => violation.impact === 'serious');
      const summary = critical.map((violation) => ({
        id: violation.id,
        help: violation.help,
        nodes: violation.nodes.map((node) => node.target.join(' ')),
      }));
      const backlog = serious.map((violation) => ({
        id: violation.id,
        help: violation.help,
        nodes: violation.nodes.map((node) => node.target.join(' ')),
      }));

      // Visible backlog, not a gate: review before promoting to a failure.
      await test.info().attach('axe-serious', {
        body: JSON.stringify(backlog, null, 2),
        contentType: 'application/json',
      });

      expect(summary, JSON.stringify(summary, null, 2)).toEqual([]);
    });
  }
});
