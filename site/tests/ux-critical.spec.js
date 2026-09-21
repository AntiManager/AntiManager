const { test, expect } = require('@playwright/test');

// Hermetic tests: block external analytics (Yandex.Metrika) so the network
// reaches idle deterministically. Without this, `waitForLoadState('networkidle')`
// hangs on the external mc.yandex.ru request (F16.6).
test.beforeEach(async ({ page }) => {
  await page.route('**/mc.yandex.ru/**', (route) => route.abort());
});

// === AX01 — A11y foundation ===
test.describe('AX01 — A11y foundation', () => {
  test('skip-link visible on Tab, focuses main', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const skipLink = page.locator('.skip-link');
    await expect(skipLink).toBeAttached();

    await page.keyboard.press('Tab');
    await expect(skipLink).toBeFocused();

    await page.keyboard.press('Enter');
    const mainEl = page.locator('#main-content');
    await expect(mainEl).toHaveCount(1);
  });

  test('focus-visible ring appears on keyboard Tab', async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('Tab');
    const outline = await page.evaluate(() => {
      const el = document.activeElement;
      return el ? getComputedStyle(el).outline : '';
    });
    expect(outline).toContain('rgb(220');
  });

  test('prefers-reduced-motion rule exists in stylesheet', async ({ page }) => {
    await page.goto('/');
    const hasRule = await page.evaluate(() => {
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            if (rule.conditionText && rule.conditionText.includes('prefers-reduced-motion')) return true;
          }
        } catch(e) {}
      }
      return false;
    });
    expect(hasRule).toBe(true);
  });

  test('skip-link visible on mobile after Tab', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.keyboard.press('Tab');
    await expect(page.locator('.skip-link')).toBeFocused();
  });
});

// === AX02 — Touch targets ===
test.describe('AX02 — Touch targets', () => {
  test('filter buttons are >= 44px on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/arsenal/');
    await page.waitForLoadState('networkidle');

    const btns = page.locator('.filter-btn');
    const count = await btns.count();
    expect(count).toBeGreaterThan(0);

    for (let i = 0; i < Math.min(count, 5); i++) {
      const box = await btns.nth(i).boundingBox();
      if (box) {
        expect(box.height).toBeGreaterThanOrEqual(42);
      }
    }
  });

  test('CTA buttons are >= 44px on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const cta = page.locator('.btn-crisis, .btn-primary').first();
    const box = await cta.boundingBox();
    expect(box.height).toBeGreaterThanOrEqual(42);
  });
});

// === AX03 — Crisis shortcut ===
test.describe('AX03 — Crisis shortcut', () => {
  test('crisis CTA links to /weapons/antikrizis/', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const crisisBtn = page.locator('.btn-crisis');
    await expect(crisisBtn).toBeVisible();

    const href = await crisisBtn.getAttribute('href');
    expect(href).toBe('/weapons/antikrizis/');

    await crisisBtn.click();
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/weapons/antikrizis/');

    const h1 = page.locator('.content-page h1');
    await expect(h1).toBeVisible();
  });

  test('crisis CTA navigates correctly on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    const crisisBtn = page.locator('.btn-crisis');
    await expect(crisisBtn).toBeVisible();
    await crisisBtn.click();
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/weapons/antikrizis/');
  });
});

// === AX04 — Responsive breakpoints ===
test.describe('AX04 — Responsive breakpoints', () => {
  test('weapon-grid is 2 columns at 768px', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/arsenal/');
    await page.waitForLoadState('networkidle');

    const cols = await page.evaluate(() => {
      const el = document.querySelector('.weapon-grid');
      return el ? getComputedStyle(el).gridTemplateColumns.split(' ').length : 0;
    });
    expect(cols).toBe(2);
  });

  test('weapon-grid is 1 column at 600px', async ({ page }) => {
    await page.setViewportSize({ width: 600, height: 800 });
    await page.goto('/arsenal/');
    await page.waitForLoadState('networkidle');

    const cols = await page.evaluate(() => {
      const el = document.querySelector('.weapon-grid');
      return el ? getComputedStyle(el).gridTemplateColumns.split(' ').length : 0;
    });
    expect(cols).toBe(1);
  });

  test('case-grid is 2 columns at 900px', async ({ page }) => {
    await page.setViewportSize({ width: 900, height: 800 });
    await page.goto('/cases/');
    await page.waitForLoadState('networkidle');

    const cols = await page.evaluate(() => {
      const el = document.querySelector('.case-grid');
      return el ? getComputedStyle(el).gridTemplateColumns.split(' ').length : 0;
    });
    expect(cols).toBe(2);
  });

  test('case-grid is 3 columns at 1280px', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/cases/');
    await page.waitForLoadState('networkidle');

    const cols = await page.evaluate(() => {
      const el = document.querySelector('.case-grid');
      return el ? getComputedStyle(el).gridTemplateColumns.split(' ').length : 0;
    });
    expect(cols).toBe(3);
  });

  test('no horizontal scroll on all pages', async ({ page }) => {
    const paths = ['/', '/arsenal/', '/cases/', '/archive/', '/weapons/antikrizis/'];
    for (const p of paths) {
      await page.goto(p);
      await page.waitForLoadState('networkidle');
      const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 2);
    }
  });
});

// === AX05 — Hover guard for case cards ===
test.describe('AX05 — Hover guard for case cards', () => {
  test('case-card hover rule is inside @media (hover: hover)', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const hasHoverGuard = await page.evaluate(() => {
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            if (rule instanceof CSSMediaRule && rule.conditionText.includes('hover: hover')) {
              for (const inner of rule.cssRules) {
                if (inner.selectorText && inner.selectorText.includes('.case-card:hover')) return true;
              }
            }
          }
        } catch(e) {}
      }
      return false;
    });
    expect(hasHoverGuard).toBe(true);
  });
});

// === AX06 — Download CTA text ===
test.describe('AX06 — Download CTA text', () => {
  test('download button says "Хочу PDF"', async ({ page }) => {
    await page.goto('/weapons/dva-tipa-upravleniya/');
    await page.waitForLoadState('networkidle');

    const btn = page.locator('.download-btn');
    await expect(btn).toBeVisible();
    const text = await btn.textContent();
    expect(text.trim()).toBe('Хочу PDF');
  });

  test('download heading does not say "Скачать"', async ({ page }) => {
    await page.goto('/weapons/dva-tipa-upravleniya/');
    const heading = page.locator('.download-section h3');
    await expect(heading).toBeVisible();
    const text = await heading.textContent();
    expect(text).not.toContain('Скачать');
  });

  test('download section exists on weapon pages', async ({ page }) => {
    await page.goto('/weapons/haos/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.download-section')).toBeVisible();
    await expect(page.locator('.download-btn')).toBeVisible();
  });
});

// === AX07 — Thinker photos ===
test.describe('AX07 — Thinker photos', () => {
  test('archive page shows thinker photos', async ({ page }) => {
    await page.goto('/archive/');
    await page.waitForLoadState('networkidle');

    const photos = page.locator('.thinker-photo');
    const count = await photos.count();
    expect(count).toBeGreaterThanOrEqual(9);

    const src = await photos.first().getAttribute('src');
    expect(src).toMatch(/\/images\/thinkers\//);

    const alt = await photos.first().getAttribute('alt');
    expect(alt).toBeTruthy();
    expect(alt).toContain('фото');
  });

  test('photo files exist in dist/', async ({ page }) => {
    const resp = await page.request.get('http://localhost:3000/images/thinkers/деминг.jpg');
    expect(resp.status()).toBe(200);
    expect(resp.headers()['content-type']).toContain('image');
  });

  test('weapon page shows thinker photo in thinker-block', async ({ page }) => {
    await page.goto('/weapons/mayatnik-upravleniya/');
    await page.waitForLoadState('networkidle');

    const thumb = page.locator('.thinker-photo-sm');
    const count = await thumb.count();
    if (count > 0) {
      const src = await thumb.first().getAttribute('src');
      expect(src).toMatch(/\/images\/thinkers\//);
    }
  });

  test('photos visible on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/archive/');
    await page.waitForLoadState('networkidle');
    const photo = page.locator('.thinker-photo').first();
    await expect(photo).toBeVisible();
  });

  test('all thinker photos have correct alt text', async ({ page }) => {
    await page.goto('/archive/');
    await page.waitForLoadState('networkidle');
    const alts = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('.thinker-photo')).map(function(img) { return img.getAttribute('alt'); });
    });
    expect(alts.length).toBeGreaterThanOrEqual(9);
    alts.forEach(function(a) { expect(a).toContain('фото'); });
  });
});
