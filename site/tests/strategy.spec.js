const { test, expect } = require('@playwright/test');

// Role: production leader reads a strategy long-read and reaches out.
// One-tier section: /strategy/ hub → /strategy/<slug>/ (full text, TOC, FAQ, CTA).

const ARTICLES = ['antihrupkaya-strategiya', 'amortizacionnaya-lovushka'];

test.describe('Стратегия — hub', () => {
  test('lists both long-reads and links to them', async ({ page }) => {
    await page.goto('/strategy/');
    await expect(page.locator('h1')).toContainText('Стратегия');
    await expect(page.locator('.strategy-card')).toHaveCount(2);
    await expect(page.locator('a[href="/strategy/antihrupkaya-strategiya/"]').first()).toBeVisible();
    await expect(page.locator('a[href="/strategy/amortizacionnaya-lovushka/"]').first()).toBeVisible();
  });

  test('is exposed in the header nav', async ({ page }) => {
    await page.goto('/');
    // On mobile/tablet the nav collapses behind the menu toggle, so assert the
    // link is present in the DOM (count is layout-independent) rather than click.
    await expect(page.locator('.header-nav a[href="/strategy/"]')).toHaveCount(1);
  });
});

test.describe('Стратегия — статья', () => {
  for (const slug of ARTICLES) {
    test(slug + ': hero, breadcrumb, TOC, FAQ, materials and CTA render', async ({ page }) => {
      await page.goto('/strategy/' + slug + '/');
      await expect(page.locator('.full-hero h1')).toBeVisible();
      await expect(page.locator('.breadcrumbs a[href="/strategy/"]')).toHaveCount(1);
      await expect(page.locator('.article-toc')).toBeVisible();
      await expect(page.locator('.full-article h2').first()).toBeVisible();
      await expect(page.locator('.strategy-faq')).toBeVisible();
      await expect(page.locator('.strategy-faq .faq-item')).toHaveCount(4);
      await expect(page.locator('.materials-section')).toBeVisible();
      await expect(page.locator('.cta-band a[href="https://t.me/antimanagerpro_bot"]')).toBeVisible();
      await expect(page.locator('.strategy-links a')).not.toHaveCount(0);
    });
  }

  test('TOC link jumps to an in-page section', async ({ page }) => {
    await page.goto('/strategy/antihrupkaya-strategiya/');
    const first = page.locator('.article-toc a').first();
    const href = await first.getAttribute('href');
    await first.click();
    await expect(page.locator(href)).toBeVisible();
  });

  test('sibling article is cross-linked both ways', async ({ page }) => {
    await page.goto('/strategy/antihrupkaya-strategiya/');
    await expect(page.locator('a[href="/strategy/amortizacionnaya-lovushka/"]').first()).toBeVisible();
    await page.goto('/strategy/amortizacionnaya-lovushka/');
    await expect(page.locator('a[href="/strategy/antihrupkaya-strategiya/"]').first()).toBeVisible();
  });
});
