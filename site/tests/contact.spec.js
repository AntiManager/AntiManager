const { test, expect } = require('@playwright/test');

// Hermetic: block external analytics (Yandex.Metrika) so networkidle is deterministic.
test.beforeEach(async ({ page }) => {
  await page.route('**/mc.yandex.ru/**', (route) => route.abort());
});

const CONTACT = '/contact/';

// === CF01 — Contact / feedback form ===
test.describe('CF01 — Contact form', () => {
  test('renders the feedback form', async ({ page }) => {
    await page.goto(CONTACT);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('#feedbackForm')).toBeVisible();
    await expect(page.locator('#cf-name')).toBeVisible();
    await expect(page.locator('#cf-contact')).toBeVisible();
    await expect(page.locator('#cf-message')).toBeVisible();
    await expect(page.locator('#cf-consent')).toBeVisible();
  });

  test('native validation blocks an empty submit', async ({ page }) => {
    await page.goto(CONTACT);

    let posted = 0;
    await page.route('**/api/feedback', (route) => { posted += 1; route.fulfill({ status: 200, body: '{"ok":true}' }); });

    await page.locator('#feedbackForm button[type="submit"]').click();
    await page.waitForTimeout(200);

    expect(posted).toBe(0);
    await expect(page.locator('#formStatus')).toHaveText('');
  });

  test('successful submit posts the payload and clears the form', async ({ page }) => {
    await page.goto(CONTACT);

    let payload = null;
    await page.route('**/api/feedback', (route) => {
      payload = JSON.parse(route.request().postData());
      route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
    });

    await page.fill('#cf-name', 'Иван');
    await page.fill('#cf-contact', 'ivan@example.com');
    await page.fill('#cf-message', 'Нужен аудит процессов');
    await page.check('#cf-consent');
    await page.locator('#feedbackForm button[type="submit"]').click();

    await expect(page.locator('#formStatus')).toHaveClass(/ok/);
    expect(payload).toEqual({
      name: 'Иван',
      contact: 'ivan@example.com',
      message: 'Нужен аудит процессов',
      pack: '',
      website: '',
      consent: true,
    });
    await expect(page.locator('#cf-name')).toHaveValue('');
  });

  test('?pack= prefills the offer context', async ({ page }) => {
    await page.goto(CONTACT + '?pack=process');

    await expect(page.locator('#packNote')).toBeVisible();
    await expect(page.locator('#packNote')).toContainText('Проработка процессов');
    await expect(page.locator('#cf-pack')).toHaveValue('process');
  });

  test('server error shows the error status and re-enables the button', async ({ page }) => {
    await page.goto(CONTACT);

    await page.route('**/api/feedback', (route) => route.fulfill({ status: 500, contentType: 'application/json', body: '{"error":"delivery failed"}' }));

    await page.fill('#cf-name', 'Иван');
    await page.fill('#cf-contact', 'ivan@example.com');
    await page.fill('#cf-message', 'Тест');
    await page.check('#cf-consent');
    await page.locator('#feedbackForm button[type="submit"]').click();

    await expect(page.locator('#formStatus')).toHaveClass(/err/);
    await expect(page.locator('#feedbackForm button[type="submit"]')).toBeEnabled();
  });
});
