const { test, expect } = require('@playwright/test');

// Role: production leader reads a long-read and reaches out.
// Library: /articles/ hub → /articles/<topic>/ → /articles/<topic>/<slug>/.
const ARTICLES = require('../src/data/articles.json').filter((a) => a.status === 'published');
const TOPICS = require('../src/data/article-topics.json').filter((t) => ARTICLES.some((a) => a.topic === t.slug));

test.describe('Статьи — hub', () => {
  test('lists every published long-read and links to them', async ({ page }) => {
    await page.goto('/articles/');
    await expect(page.locator('h1')).toContainText('Статьи');
    // Scoped to the topic sections: the optional series block repeats its
    // members, so a page-wide count would over-count once a series ships.
    await expect(page.locator('.articles-topic .article-card')).toHaveCount(ARTICLES.length);
    for (const a of ARTICLES) {
      await expect(page.locator(`a[href="/articles/${a.topic}/${a.slug}/"]`).first()).toBeVisible();
    }
  });

  test('is exposed in the header nav and not the legacy section', async ({ page }) => {
    await page.goto('/');
    // On mobile/tablet the nav collapses behind the menu toggle, so assert the
    // link is present in the DOM (count is layout-independent) rather than click.
    await expect(page.locator('.header-nav a[href="/articles/"]')).toHaveCount(1);
    await expect(page.locator('.header-nav a[href="/strategy/"]')).toHaveCount(0);
  });
});

test.describe('Статьи — topic hubs', () => {
  for (const t of TOPICS) {
    test(`${t.slug}: lists its articles with a three-level breadcrumb`, async ({ page }) => {
      await page.goto(`/articles/${t.slug}/`);
      await expect(page.locator('h1')).toContainText(t.title);
      await expect(page.locator('.article-card')).toHaveCount(ARTICLES.filter((a) => a.topic === t.slug).length);
      await expect(page.locator('.breadcrumbs a[href="/articles/"]')).toHaveCount(1);
    });
  }
});

test.describe('Статьи — статья', () => {
  for (const a of ARTICLES) {
    test(`${a.topic}/${a.slug}: hero, breadcrumb, TOC, FAQ, materials and CTA render`, async ({ page }) => {
      await page.goto(`/articles/${a.topic}/${a.slug}/`);
      await expect(page.locator('.full-hero h1')).toBeVisible();
      await expect(page.locator('.breadcrumbs a[href="/articles/"]')).toHaveCount(1);
      await expect(page.locator(`.breadcrumbs a[href="/articles/${a.topic}/"]`)).toHaveCount(1);
      await expect(page.locator('.article-toc')).toBeVisible();
      await expect(page.locator('.full-article h2').first()).toBeVisible();
      await expect(page.locator('.article-faq')).toBeVisible();
      await expect(page.locator('.article-faq .faq-item')).toHaveCount(a.faq.length);
      await expect(page.locator('.materials-section')).toBeVisible();
      await expect(page.locator('.cta-band a[href="https://t.me/antimanagerpro_bot"]')).toBeVisible();
      await expect(page.locator('.article-links a')).not.toHaveCount(0);
    });
  }

  test('TOC link jumps to an in-page section', async ({ page }) => {
    await page.goto('/articles/strategy/antihrupkaya-strategiya/');
    const first = page.locator('.article-toc a').first();
    const href = await first.getAttribute('href');
    await first.click();
    await expect(page.locator(href)).toBeVisible();
  });

  test('sibling article is cross-linked both ways', async ({ page }) => {
    await page.goto('/articles/strategy/antihrupkaya-strategiya/');
    await expect(page.locator('a[href="/articles/strategy/amortizacionnaya-lovushka/"]').first()).toBeVisible();
    await page.goto('/articles/strategy/amortizacionnaya-lovushka/');
    await expect(page.locator('a[href="/articles/strategy/antihrupkaya-strategiya/"]').first()).toBeVisible();
  });
});
