const { test, expect } = require('@playwright/test');

// Hermetic: block external analytics (Yandex.Metrika) so networkidle is deterministic (F16.6).
test.beforeEach(async ({ page }) => {
  await page.route('**/mc.yandex.ru/**', (route) => route.abort());
});

const LANDING = '/method/';
const ROLE = '/method/role/';

// === GEN01 — Genome landing ===
test.describe('GEN01 — Genome landing', () => {
  test('renders hero, the four tool entry points and six document cards', async ({ page }) => {
    await page.goto(LANDING);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.hero-gen h1')).toContainText('Методология');
    await expect(page.locator('.weapon-status')).toContainText('Геном завода');
    await expect(page.locator('.method-tool')).toHaveCount(4);
    await expect(page.locator('.method-tool[href="/method/audit/"]')).toBeVisible();
    await expect(page.locator('.method-tool[href="/method/systems/"]')).toBeVisible();
    await expect(page.locator('.method-tool[href="/method/documents/"]')).toBeVisible();
    await expect(page.locator('.method-tool[href="/method/role/"]')).toBeVisible();
    await expect(page.locator('.breadcrumbs')).toBeVisible();
    await expect(page.locator('.tree details')).toHaveCount(3);
    // Free sample covers the whole PLAN group: 3 processes / 11 subprocesses / 49 operations.
    expect(await page.locator('.ops-table tbody tr').count()).toBe(49);
    await expect(page.locator('.doc-card')).toHaveCount(6);
  });

  test('tool entry points are above the fold and the section TOC is sticky', async ({ page }) => {
    await page.goto(LANDING);
    await page.waitForLoadState('networkidle');

    const viewport = page.viewportSize();
    const firstTool = await page.locator('.method-tool').first().boundingBox();
    expect(firstTool.y, 'first tool card must start above the fold').toBeLessThan(viewport.height);

    await expect(page.locator('.method-toc')).toHaveCSS('position', 'sticky');
    await page.locator('#model').scrollIntoViewIfNeeded();
    await expect(page.locator('.method-toc')).toBeVisible();
  });

  test('commercial CTAs open the feedback form', async ({ page }) => {
    await page.goto(LANDING);

    await expect(page.locator('.packs a.btn[href^="/contact/?pack="]')).toHaveCount(4);
    await expect(page.locator('.cta-band a[href="/contact/"]')).toHaveCount(1);
    await expect(page.locator('a[href="#"]')).toHaveCount(0);
  });

  test('КУ card opens the full document on the role-page anchor', async ({ page }) => {
    await page.goto(LANDING);
    await page.locator('a.doc-link[href="/method/role/#ku"]').click();

    await page.waitForURL('**/method/role/**');
    await expect(page.locator('section#ku')).toBeAttached();
  });
});

// === GEN02 — Genome role documents ===
test.describe('GEN02 — Genome role documents', () => {
  test('renders both document sections with converted tables', async ({ page }) => {
    await page.goto(ROLE);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('section#ku')).toBeAttached();
    await expect(page.locator('section#profile')).toBeAttached();
    expect(await page.locator('.doc-doc table').count()).toBeGreaterThan(30);
    await expect(page.locator('.doc-doc h3').first()).toBeVisible();
  });

  test('jump-nav anchor resolves to the section', async ({ page }) => {
    await page.goto(ROLE);
    await page.locator('.doc-jump a[href="#ku"]').click();
    await expect(page).toHaveURL(/#ku$/);
  });

  test('document TOC is sticky and reading progress advances', async ({ page }) => {
    await page.goto(ROLE);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.role-toc')).toHaveCSS('position', 'sticky');
    await expect(page.locator('.role-toc a[href="#ku"]')).toBeVisible();
    await expect(page.locator('.role-toc a[href="#profile"]')).toBeVisible();

    await page.locator('section#profile').scrollIntoViewIfNeeded();
    await expect.poll(async function() {
      return page.locator('.reading-progress-fill').evaluate(function(el) {
        return parseFloat(el.style.width) || 0;
      });
    }).toBeGreaterThan(0);
  });
});

// === GEN03 — no horizontal scroll ===
test.describe('GEN03 — Genome layout', () => {
  test('genome pages do not overflow horizontally', async ({ page }) => {
    for (const p of [LANDING, ROLE]) {
      await page.goto(p);
      await page.waitForLoadState('networkidle');
      const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
      expect(scrollWidth, p + ' overflows').toBeLessThanOrEqual(clientWidth + 2);
    }
  });
});
