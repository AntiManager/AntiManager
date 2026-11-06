const { test, expect } = require('@playwright/test');

// Hermetic: block external analytics so networkidle is deterministic.
test.beforeEach(async ({ page }) => {
  await page.route('**/mc.yandex.ru/**', (route) => route.abort());
});

test.describe('HOME01 — book positioning', () => {
  test('hero answers what, for whom and where to start', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('h1')).toContainText('ПЛЕЙБУК: КАК НА САМОМ ДЕЛЕ РАБОТАЕТ ЗАВОД');
    await expect(page.locator('.hero-lead')).toContainText('long-reads');
    await expect(page.locator('.hero-cta a[href="/start/"]')).toBeVisible();
    await expect(page.locator('.hero-cta a[href="/playbook/"]')).toBeVisible();
    await expect(page.locator('.hero-cta a[href="/method/audit/"]')).toBeVisible();
    await expect(page.locator('.home-manifesto')).toContainText('Её нет');
  });

  test('the first CTA is above the fold on a 375x812 phone', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const box = await page.locator('.hero-cta a').first().boundingBox();
    expect(box).not.toBeNull();
    expect(box.y + box.height).toBeLessThanOrEqual(812);
  });
});

test.describe('HOME02 — no duplicated blocks', () => {
  test('six sections, one chooser, one map, no manifesto wall or cases', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('main > section')).toHaveCount(6);
    await expect(page.locator('.zone-grid')).toHaveCount(1);
    await expect(page.locator('.map-container')).toHaveCount(1);
    await expect(page.locator('#weapons-section .weapon-card')).toHaveCount(6);
    await expect(page.locator('.home-articles .article-card')).toHaveCount(3);
    await expect(page.locator('.home-method-tools .method-tool')).toHaveCount(3);
    await expect(page.locator('.home-project-links .method-tool')).toHaveCount(3);
    await expect(page.locator('.manifesto-teaser')).toHaveCount(0);
    await expect(page.locator('.hq-section')).toHaveCount(0);
  });

  test('situation cards open the matching /start/ block', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const cards = page.locator('.zone-grid .zone-card');
    await expect(cards).toHaveCount(4);
    for (const id of ['crisis', 'team', 'changes', 'system']) {
      await expect(page.locator('.zone-grid .zone-card[href="/start/#' + id + '"]')).toBeVisible();
    }
  });

  test('project block links to about, manifesto and archive', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.home-project-links a[href="/about/"]')).toBeVisible();
    await expect(page.locator('.home-project-links a[href="/about/manifesto/"]')).toBeVisible();
    await expect(page.locator('.home-project-links a[href="/about/origins/"]')).toBeVisible();
  });
});

test.describe('HOME03 — layout', () => {
  test('home does not overflow horizontally at 320-1920', async ({ page }) => {
    for (const width of [320, 375, 768, 980, 1280, 1920]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
      expect(scrollWidth, width + 'px overflows').toBeLessThanOrEqual(clientWidth + 2);
    }
  });
});
