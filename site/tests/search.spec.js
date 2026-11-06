const { test, expect } = require('@playwright/test');

// Site search (Pagefind) — plan 1793969494727, task 10.
// The dialog is global; the index bundle is imported lazily on first open.
test.beforeEach(async ({ page }) => {
  await page.route('**/mc.yandex.ru/**', (route) => route.abort());
});

async function openSearch(page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.locator('.header-search').click();
  await expect(page.locator('#site-search')).toBeVisible();
  await expect(page.locator('#site-search-input')).toBeFocused();
}

async function expectResults(page) {
  await expect(page.locator('.search-result').first()).toBeVisible({ timeout: 20000 });
  await expect(page.locator('.search-status')).toContainText('Найдено');
}

test.describe('search — dialog', () => {
  test('header entry opens the dialog with focus in the input', async ({ page }) => {
    await openSearch(page);
    await expect(page.locator('.header-search')).toHaveAttribute('aria-expanded', 'true');
  });

  test('/ shortcut opens it from the page body', async ({ page }) => {
    await page.goto('/playbook/');
    await page.waitForLoadState('networkidle');
    await page.keyboard.press('/');
    await expect(page.locator('#site-search')).toBeVisible();
    await expect(page.locator('#site-search-input')).toBeFocused();
  });

  test('Escape closes and returns focus to the header trigger', async ({ page }) => {
    await openSearch(page);
    await page.keyboard.press('Escape');
    await expect(page.locator('#site-search')).toBeHidden();
    await expect(page.locator('.header-search')).toBeFocused();
    await expect(page.locator('.header-search')).toHaveAttribute('aria-expanded', 'false');
  });

  test('close button dismisses the dialog', async ({ page }) => {
    await openSearch(page);
    await page.locator('[data-search-close]').click();
    await expect(page.locator('#site-search')).toBeHidden();
  });
});

test.describe('search — results', () => {
  for (const query of ['OEE', 'антикризис', 'A3']) {
    test('query «' + query + '» returns relevant results', async ({ page }) => {
      await openSearch(page);
      await page.locator('#site-search-input').fill(query);
      await expectResults(page);
      await expect(page.locator('.search-result-meta').first()).not.toBeEmpty();
    });
  }

  test('arrow keys move through results and Enter follows the link', async ({ page }) => {
    await openSearch(page);
    await page.locator('#site-search-input').fill('OEE');
    await expectResults(page);

    await page.keyboard.press('ArrowDown');
    const first = page.locator('.search-result-link').first();
    await expect(first).toBeFocused();
    await page.keyboard.press('ArrowDown');
    await expect(page.locator('.search-result-link').nth(1)).toBeFocused();
    await page.keyboard.press('ArrowUp');
    await expect(first).toBeFocused();

    const href = await first.getAttribute('href');
    await page.keyboard.press('Enter');
    await page.waitForURL('**' + href);
  });

  test('unknown query shows the empty state', async ({ page }) => {
    await openSearch(page);
    await page.locator('#site-search-input').fill('ъъъъъъъ');
    await expect(page.locator('.search-empty')).toBeVisible({ timeout: 20000 });
    await expect(page.locator('.search-result')).toHaveCount(0);
  });

  test('debounced typing searches without submitting', async ({ page }) => {
    await openSearch(page);
    await page.locator('#site-search-input').pressSequentially('OEE', { delay: 40 });
    await expectResults(page);
  });
});

test.describe('search — fallback page and mobile', () => {
  test('/search/?q=OEE opens the dialog and shows results', async ({ page }) => {
    await page.goto('/search/?q=OEE');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('#site-search')).toBeVisible();
    await expect(page.locator('#site-search-input')).toHaveValue('OEE');
    await expectResults(page);
  });

  test('/search/ is noindex and carries the fallback form', async ({ page }) => {
    await page.goto('/search/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('meta[name="robots"][content="noindex"]')).toHaveCount(1);
    await expect(page.locator('form[action="/search/"][method="get"]')).toHaveCount(2);
  });

  test('mobile overlay fits the viewport and stays usable', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'mobile', 'mobile-specific check');

    await openSearch(page);
    const box = await page.locator('#site-search').boundingBox();
    const viewport = page.viewportSize();
    expect(box.width).toBeLessThanOrEqual(viewport.width - 2);
    expect(box.x).toBeGreaterThanOrEqual(0);

    await page.locator('#site-search-input').fill('OEE');
    await expectResults(page);
    await expect(page.locator('[data-search-close]')).toBeVisible();
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth).toBeLessThanOrEqual(viewport.width + 2);
  });
});
