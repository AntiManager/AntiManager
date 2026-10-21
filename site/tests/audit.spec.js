const { test, expect } = require('@playwright/test');

// Hermetic: block external analytics (Yandex.Metrika) so waits are deterministic.
test.beforeEach(async ({ page }) => {
  await page.route('**/mc.yandex.ru/**', (route) => route.abort());
});

const PAGE = '/genome/audit/';

test.describe('AUDIT01 — Express audit page', () => {
  test('renders 40 collapsed criteria and opens one with levels, KPI and verification', async ({ page }) => {
    const response = await page.goto(PAGE);
    expect(response.status()).toBe(200);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('h1')).toContainText('Экспресс-аудит');
    await expect(page.locator('.audit-criterion')).toHaveCount(40);
    await expect(page.locator('.audit-criterion[open]')).toHaveCount(0);

    await page.locator('.audit-criterion').first().locator('summary').click();
    const first = page.locator('.audit-criterion').first();
    await expect(first).toHaveAttribute('open', '');
    await expect(first.locator('.audit-levels tbody tr')).toHaveCount(6);
    await expect(first.locator('.audit-kpi')).toContainText('KPI/результат');
    await expect(first.locator('.audit-verify')).toContainText('Способ верификации');
  });

  test('toggle-all opens and closes every criterion', async ({ page }) => {
    await page.goto(PAGE);

    await page.locator('[data-audit-toggle="open"]').click();
    await expect(page.locator('.audit-criterion[open]')).toHaveCount(40);

    await page.locator('[data-audit-toggle="close"]').click();
    await expect(page.locator('.audit-criterion[open]')).toHaveCount(0);
  });

  test('a criterion deep link opens its details element', async ({ page }) => {
    await page.goto(PAGE + '#c07');
    await expect(page.locator('#c07')).toHaveAttribute('open', '');
  });

  test('the CTA opens the contact form with the audit pack context', async ({ page }) => {
    await page.goto(PAGE);
    await page.locator('a[href="/contact/?pack=audit"]').click();

    await expect(page).toHaveURL(/\/contact\/\?pack=audit$/);
    await expect(page.locator('#packNote')).toBeVisible();
    await expect(page.locator('#packNote')).toContainText('Интересует: Полный чек-лист ПС (120 критериев)');
  });

  test('the workbook is downloadable', async ({ page }) => {
    await page.goto(PAGE);

    const link = page.locator('.materials-list a[download]');
    await expect(link).toHaveAttribute('download', 'Экспресс-чек-лист-аудита-ПС-v3.0.xlsx');

    const href = await link.getAttribute('href');
    expect(href).toContain('?v=');
    const response = await page.request.get(href);
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('spreadsheetml');
    expect((await response.body()).length).toBeGreaterThan(10240);
  });

  test('print media hides controls and keeps block headings', async ({ page }) => {
    await page.goto(PAGE);
    await page.emulateMedia({ media: 'print' });

    await expect(page.locator('.audit-controls')).toBeHidden();
    await expect(page.locator('.audit-chips')).toBeHidden();
    await expect(page.locator('.audit-block-title').first()).toBeVisible();
  });
});
