const { test, expect } = require('@playwright/test');

// Hermetic: block external analytics so networkidle is deterministic.
test.beforeEach(async ({ page }) => {
  await page.route('**/mc.yandex.ru/**', (route) => route.abort());
});

const ABOUT = '/about/';
const SUBPAGES = ['/about/manifesto/', '/about/origins/'];

test.describe('ABOUT01 — project page', () => {
  test('answers what, who and how, with a route into the site', async ({ page }) => {
    await page.goto(ABOUT);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('h1')).toHaveText('О проекте');
    await expect(page.locator('.breadcrumbs')).toBeVisible();
    await expect(page.locator('h2', { hasText: 'Что здесь есть' })).toBeVisible();
    await expect(page.locator('h2', { hasText: 'Для кого' })).toBeVisible();
    await expect(page.locator('h2', { hasText: 'С чего начать' })).toBeVisible();
    await expect(page.locator('main a[href="/start/"]').first()).toBeVisible();
    await expect(page.locator('main a[href="/playbook/"]').first()).toBeVisible();
    await expect(page.locator('main a[href="/method/audit/"]').first()).toBeVisible();
  });

  test('subpages keep the breadcrumb trail back to /about/', async ({ page }) => {
    for (const path of SUBPAGES) {
      await page.goto(path);
      await expect(page.locator('.breadcrumbs a[href="/about/"]')).toBeVisible();
    }
  });

  test('about pages do not overflow horizontally', async ({ page }) => {
    for (const path of [ABOUT].concat(SUBPAGES)) {
      await page.goto(path);
      await page.waitForLoadState('networkidle');
      const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
      expect(scrollWidth, path + ' overflows').toBeLessThanOrEqual(clientWidth + 2);
    }
  });
});
