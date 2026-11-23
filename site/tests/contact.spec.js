const { test, expect } = require('@playwright/test');
const crypto = require('crypto');

// Hermetic: block external analytics (Yandex.Metrika) so networkidle is deterministic.
test.beforeEach(async ({ page }) => {
  await page.route('**/mc.yandex.ru/**', (route) => route.abort());
});

const CONTACT = '/contact/';

function leadingZeroBits(buffer) {
  let bits = 0;
  for (const byte of buffer) {
    if (byte === 0) { bits += 8; continue; }
    bits += Math.clz32(byte) - 24;
    break;
  }
  return bits;
}

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
      url: '',
      consent: true,
    });
    await expect(page.locator('#cf-name')).toHaveValue('');
  });

  test('submits without an optional message', async ({ page }) => {
    await page.goto(CONTACT);

    let payload = null;
    await page.route('**/api/feedback', (route) => {
      payload = JSON.parse(route.request().postData());
      route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
    });

    await page.fill('#cf-name', 'Иван');
    await page.fill('#cf-contact', 'ivan@example.com');
    await page.check('#cf-consent');
    await page.locator('#feedbackForm button[type="submit"]').click();

    await expect(page.locator('#formStatus')).toHaveClass(/ok/);
    expect(payload.message).toBe('');
    expect(payload.name).toBe('Иван');
  });

  test('successful submit fires the lead_sent goal in both systems', async ({ page }) => {
    await page.addInitScript(() => {
      window.__goals = [];
      window.ym = (id, method, goal, params) => {
        if (method === 'reachGoal') window.__goals.push({ goal, params });
      };
    });
    await page.goto(CONTACT + '?pack=process');
    await page.route('**/api/feedback', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' }));

    await page.fill('#cf-name', 'Иван');
    await page.fill('#cf-contact', 'ivan@example.com');
    await page.check('#cf-consent');
    await page.locator('#feedbackForm button[type="submit"]').click();

    await expect(page.locator('#formStatus')).toHaveClass(/ok/);
    await expect.poll(() => page.evaluate(() => window.__goals.map((g) => g.goal))).toContain('lead_sent');
    const params = await page.evaluate(() => window.__goals.filter((g) => g.goal === 'lead_sent').pop().params);
    expect(params.pack).toBe('process');
    await expect.poll(() => page.evaluate(() => (window.dataLayer || [])
      .filter((item) => item && item[0] === 'event')
      .map((item) => item[1]))).toContain('lead_sent');
  });

  test('?pack= prefills the offer context', async ({ page }) => {
    await page.goto(CONTACT + '?pack=process');

    await expect(page.locator('#packNote')).toBeVisible();
    await expect(page.locator('#packNote')).toContainText('Проработка процессов');
    await expect(page.locator('#cf-pack')).toHaveValue('process');
  });

  test('?pack= accepts the /products/ page slugs', async ({ page }) => {
    const cases = [
      { pack: 'dengi', label: 'Деньги на виду' },
      { pack: 'peredacha', label: 'Система без автора' },
    ];
    for (const c of cases) {
      await page.goto(CONTACT + '?pack=' + c.pack);
      await expect(page.locator('#packNote')).toBeVisible();
      await expect(page.locator('#packNote')).toContainText(c.label);
      await expect(page.locator('#cf-pack')).toHaveValue(c.pack);
    }
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

// === CF02 — Anti-bot challenge (proof of work) ===
test.describe('CF02 — Anti-bot challenge', () => {
  function challenge(overrides = {}) {
    return {
      challenge: 'c0ffee'.repeat(5) + 'abcd',
      bits: 8,
      issued: Math.floor(Date.now() / 1000),
      signature: 'a'.repeat(64),
      ...overrides,
    };
  }

  function fillLead(page) {
    return (async () => {
      await page.fill('#cf-name', 'Иван');
      await page.fill('#cf-contact', 'ivan@example.com');
      await page.fill('#cf-message', 'Нужен аудит производственных процессов.');
      await page.check('#cf-consent');
    })();
  }

  test('fetches a signed challenge when the page loads', async ({ page }) => {
    let requested = 0;
    await page.route('**/api/feedback/challenge', (route) => {
      requested += 1;
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(challenge()) });
    });

    await page.goto(CONTACT);
    await expect.poll(() => requested).toBe(1);
  });

  test('submits a solved proof of work alongside the lead', async ({ page }) => {
    const issued = challenge();
    await page.route('**/api/feedback/challenge', (route) => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(issued) });
    });

    let payload = null;
    await page.route('**/api/feedback', (route) => {
      payload = JSON.parse(route.request().postData());
      route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
    });

    const challengeServed = page.waitForResponse('**/api/feedback/challenge');
    await page.goto(CONTACT);
    await challengeServed;
    await page.waitForTimeout(50);
    await fillLead(page);
    await page.locator('#feedbackForm button[type="submit"]').click();
    await expect(page.locator('#formStatus')).toHaveClass(/ok/);

    expect(payload.challenge).toBe(issued.challenge);
    expect(payload.challenge_signature).toBe(issued.signature);
    expect(payload.challenge_issued).toBe(issued.issued);
    const digest = crypto.createHash('sha256')
      .update(issued.challenge + ':' + payload.challenge_nonce)
      .digest();
    expect(leadingZeroBits(digest)).toBeGreaterThanOrEqual(issued.bits);
  });

  test('submits without a proof when the challenge endpoint is down', async ({ page }) => {
    await page.route('**/api/feedback/challenge', (route) => route.fulfill({ status: 503, body: 'nope' }));

    let payload = null;
    await page.route('**/api/feedback', (route) => {
      payload = JSON.parse(route.request().postData());
      route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
    });

    await page.goto(CONTACT);
    await fillLead(page);
    await page.locator('#feedbackForm button[type="submit"]').click();
    await expect(page.locator('#formStatus')).toHaveClass(/ok/);
    expect(payload.challenge).toBeUndefined();
    expect(payload.name).toBe('Иван');
  });

  test('the decoy field is off-screen and outside the tab order', async ({ page }) => {
    await page.goto(CONTACT);

    const decoy = page.locator('#cf-url');
    await expect(decoy).toHaveAttribute('tabindex', '-1');
    await expect(decoy).toHaveAttribute('autocomplete', 'off');
    const box = await decoy.boundingBox();
    expect(box === null || box.x < 0).toBe(true);
  });
});

// === CF03 — no-JS fallback ===
test.describe('CF03 — no-JS fallback', () => {
  test.use({ javaScriptEnabled: false });

  test('native submit posts the form-encoded fields', async ({ page }) => {
    let body = null;
    await page.route('**/api/feedback', (route) => {
      body = route.request().postData();
      route.fulfill({
        status: 200,
        contentType: 'text/html; charset=utf-8',
        body: '<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>ok</title></head><body><p>Заявка отправлена</p></body></html>',
      });
    });

    await page.goto(CONTACT);
    await page.fill('#cf-name', 'Иван');
    await page.fill('#cf-contact', '+7 900 000-00-00');
    await page.fill('#cf-message', 'Нужен аудит производственных процессов.');
    await page.check('#cf-consent');
    await page.locator('#feedbackForm button[type="submit"]').click();

    await expect(page.locator('body')).toContainText('Заявка отправлена');
    expect(body).toContain('name=');
    expect(body).toContain('consent=on');
    expect(body).not.toContain('challenge');
  });

  test('native submit works without a message', async ({ page }) => {
    let body = null;
    await page.route('**/api/feedback', (route) => {
      body = route.request().postData();
      route.fulfill({
        status: 200,
        contentType: 'text/html; charset=utf-8',
        body: '<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>ok</title></head><body><p>Заявка отправлена</p></body></html>',
      });
    });

    await page.goto(CONTACT);
    await page.fill('#cf-name', 'Иван');
    await page.fill('#cf-contact', '+7 900 000-00-00');
    await page.check('#cf-consent');
    await page.locator('#feedbackForm button[type="submit"]').click();

    await expect(page.locator('body')).toContainText('Заявка отправлена');
    expect(body).toContain('name=');
    expect(body).toContain('consent=on');
  });
});
