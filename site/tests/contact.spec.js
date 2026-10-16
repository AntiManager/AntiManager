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

  test('rate limit (429) shows a specific, actionable message', async ({ page }) => {
    await page.goto(CONTACT);

    await page.route('**/api/feedback', (route) => route.fulfill({ status: 429, contentType: 'application/json', body: '{"error":"too many requests"}' }));

    await page.fill('#cf-name', 'Иван');
    await page.fill('#cf-contact', 'ivan@example.com');
    await page.fill('#cf-message', 'Тест');
    await page.check('#cf-consent');
    await page.locator('#feedbackForm button[type="submit"]').click();

    await expect(page.locator('#formStatus')).toHaveClass(/err/);
    await expect(page.locator('#formStatus')).toContainText('Слишком много заявок');
  });

  test('keyboard navigation shows a visible focus indicator on the fields', async ({ page }) => {
    await page.goto(CONTACT);
    await page.evaluate(() => document.body.focus());

    let focused = null;
    for (let i = 0; i < 40; i += 1) {
      await page.keyboard.press('Tab');
      focused = await page.evaluate(() => document.activeElement.id);
      if (focused === 'cf-name') break;
    }
    expect(focused).toBe('cf-name');

    const outline = await page.evaluate(() => {
      const cs = getComputedStyle(document.activeElement);
      return { style: cs.outlineStyle, width: cs.outlineWidth };
    });
    expect(outline.style).toBe('solid');
    expect(parseFloat(outline.width)).toBeGreaterThan(0);
  });

  test('submit button looks disabled while sending', async ({ page }) => {
    await page.goto(CONTACT);

    let release;
    const gate = new Promise((resolve) => { release = resolve; });
    await page.route('**/api/feedback', async (route) => {
      await gate;
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
    });

    await page.fill('#cf-name', 'Иван');
    await page.fill('#cf-contact', 'ivan@example.com');
    await page.fill('#cf-message', 'Тест');
    await page.check('#cf-consent');

    const button = page.locator('#feedbackForm button[type="submit"]');
    await button.click();
    await expect(button).toBeDisabled();
    // toHaveCSS polls, so it is not racy against the .btn opacity transition.
    await expect(button).toHaveCSS('opacity', '0.5');

    release();
    await expect(page.locator('#formStatus')).toHaveClass(/ok/);
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
