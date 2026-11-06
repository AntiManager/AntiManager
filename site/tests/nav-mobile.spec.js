const { test, expect } = require('@playwright/test');

// Header/nav/footer behavior for the IA refactor (plan 1793969494727, task 4).
// Screen-specific checks set their own viewport and run once (desktop project)
// so the three-project matrix does not repeat identical navigations.
test.beforeEach(async ({ page }) => {
  await page.route('**/mc.yandex.ru/**', (route) => route.abort());
});

test.describe('nav — desktop header', () => {
  test('shows 4 nav links + CTA, hides the hamburger', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.header-nav a')).toHaveCount(4);
    await expect(page.locator('.header-cta')).toBeVisible();
    await expect(page.locator('.header-cta')).toHaveAttribute('href', '/contact/');
    await expect(page.locator('.menu-toggle')).toBeHidden();
  });

  test('marks the current section with aria-current at build time', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });

    await page.goto('/playbook/');
    await expect(page.locator('.header-nav a[data-nav="book"]')).toHaveAttribute('aria-current', 'page');

    await page.goto('/method/');
    await expect(page.locator('.header-nav a[data-nav="method"]')).toHaveAttribute('aria-current', 'page');

    await page.goto('/');
    await expect(page.locator('.header-nav a[aria-current="page"]')).toHaveCount(0);
  });

  test('red corner does not overlap the header CTA', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const gap = await page.evaluate(() => {
      const header = document.querySelector('.site-header');
      const cta = document.querySelector('.header-cta');
      const corner = parseFloat(getComputedStyle(header, '::after').width);
      return { gap: header.getBoundingClientRect().right - cta.getBoundingClientRect().right, corner: corner };
    });
    expect(gap.gap).toBeGreaterThanOrEqual(gap.corner);
  });
});

test.describe('nav — mobile header', () => {
  test('CTA lives inside the open menu', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const cta = page.locator('.header-cta');
    await expect(cta).toBeHidden();

    await page.locator('.menu-toggle').click();
    await expect(cta).toBeVisible();
    await expect(page.locator('.header-nav')).toBeVisible();

    const box = await cta.boundingBox();
    const navBox = await page.locator('.header-nav').boundingBox();
    expect(box.width).toBeGreaterThan(navBox.width - 2);
  });

  test('Escape closes the menu and returns focus to the toggle', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const toggle = page.locator('.menu-toggle');
    await toggle.click();
    await expect(page.locator('.header-nav')).toBeVisible();
    await expect(toggle).toHaveAttribute('aria-label', 'Закрыть меню');

    await page.keyboard.press('Escape');
    await expect(page.locator('.header-nav')).toBeHidden();
    await expect(toggle).toHaveAttribute('aria-expanded', 'false');
    await expect(toggle).toHaveAttribute('aria-label', 'Меню');
    await expect(toggle).toBeFocused();
  });

  test('header stays sticky after scrolling', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/playbook/');
    await page.waitForLoadState('networkidle');

    await page.evaluate(() => window.scrollTo(0, 1200));
    const top = await page.evaluate(() => document.querySelector('.site-header').getBoundingClientRect().top);
    expect(Math.abs(top)).toBeLessThanOrEqual(1);
  });

  test('red corner does not overlap the menu button', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const gap = await page.evaluate(() => {
      const header = document.querySelector('.site-header');
      const toggle = document.querySelector('.menu-toggle');
      const corner = parseFloat(getComputedStyle(header, '::after').width);
      return { gap: header.getBoundingClientRect().right - toggle.getBoundingClientRect().right, corner: corner };
    });
    expect(gap.gap).toBeGreaterThanOrEqual(gap.corner);
  });
});

test.describe('nav — overflow matrix', () => {
  test('769/800/900 no longer overflow; 1280/1920 stay clean', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'desktop', 'viewport matrix runs once');

    const widths = [320, 375, 769, 800, 900, 980, 981, 1280, 1920];
    const paths = ['/', '/playbook/'];

    for (const width of widths) {
      await page.setViewportSize({ width: width, height: 800 });
      for (const p of paths) {
        await page.goto(p);
        await page.waitForLoadState('networkidle');
        const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
        const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
        expect(scrollWidth, p + ' at ' + width + 'px').toBeLessThanOrEqual(clientWidth + 2);
      }
    }
  });

  test('the 980px breakpoint matches the mobile header switch', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'desktop', 'viewport matrix runs once');

    await page.setViewportSize({ width: 980, height: 800 });
    await page.goto('/');
    await expect(page.locator('.menu-toggle')).toBeVisible();

    await page.setViewportSize({ width: 981, height: 800 });
    await page.goto('/');
    await expect(page.locator('.menu-toggle')).toBeHidden();
  });
});

test.describe('nav — footer', () => {
  test('has four literal columns with all destinations', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.footer-col')).toHaveCount(4);
    const titles = await page.locator('.footer-col-title').allTextContents();
    expect(titles).toEqual(['Плейбук', 'Библиотека', 'Проект', 'Связаться']);

    const cols = await page.evaluate(() => {
      const el = document.querySelector('.footer-nav');
      return getComputedStyle(el).gridTemplateColumns.split(' ').length;
    });
    expect(cols).toBe(4);

    for (const href of ['/playbook/', '/articles/', '/about/', '/contact/', '/privacy/']) {
      await expect(page.locator('.footer-nav a[href="' + href + '"]')).toHaveCount(1);
    }
  });
});
