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

// === AX08 — Mobile navigation (hamburger) ===
test.describe('AX08 — Mobile navigation', () => {
  test('hamburger toggles the mobile nav and aria-expanded', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const toggle = page.locator('.menu-toggle');
    const nav = page.locator('.header-nav');

    await expect(toggle).toBeVisible();
    await expect(nav).toBeHidden();
    await expect(toggle).toHaveAttribute('aria-expanded', 'false');

    await toggle.click();
    await expect(nav).toBeVisible();
    await expect(toggle).toHaveAttribute('aria-expanded', 'true');
    await expect(toggle).toHaveText('✕');

    await toggle.click();
    await expect(nav).toBeHidden();
    await expect(toggle).toHaveAttribute('aria-expanded', 'false');
    await expect(toggle).toHaveText('☰');
  });

  test('menu closes after selecting a nav link', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await page.locator('.menu-toggle').click();
    await expect(page.locator('.header-nav')).toBeVisible();

    await page.locator('.header-nav a', { hasText: 'Арсенал' }).click();
    await page.waitForURL('**/arsenal/');
    expect(page.url()).toContain('/arsenal/');
    await expect(page.locator('.header-nav')).toBeHidden();
  });
});

// === AX09 — Arsenal zone filter ===
test.describe('AX09 — Arsenal zone filter', () => {
  test('zone filter shows only weapons of that zone', async ({ page }) => {
    await page.goto('/arsenal/');
    await page.waitForLoadState('networkidle');

    const zoneBtn = page.locator('.filters .filter-btn:not([data-filter="all"])').first();
    const zone = await zoneBtn.getAttribute('data-filter');
    expect(zone).toBeTruthy();
    await zoneBtn.click();

    const state = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('#arsenalGrid .weapon-card'));
      const shown = cards.filter(function(c) { return c.style.display !== 'none'; });
      return {
        total: cards.length,
        shown: shown.length,
        zones: Array.from(new Set(shown.map(function(c) { return c.dataset.zone; }))),
      };
    });

    expect(state.shown).toBeGreaterThan(0);
    expect(state.zones).toEqual([zone]);
    expect(state.shown).toBeLessThan(state.total);
    await expect(zoneBtn).toHaveClass(/active/);
  });

  test('"ВСЕ" restores every weapon', async ({ page }) => {
    await page.goto('/arsenal/');
    await page.waitForLoadState('networkidle');

    const total = await page.locator('#arsenalGrid .weapon-card').count();
    expect(total).toBeGreaterThan(0);

    await page.locator('.filters .filter-btn:not([data-filter="all"])').first().click();
    const allBtn = page.locator('.filters .filter-btn[data-filter="all"]');
    await allBtn.click();

    const shown = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('#arsenalGrid .weapon-card'))
        .filter(function(c) { return c.style.display !== 'none'; }).length;
    });
    expect(shown).toBe(total);
    await expect(allBtn).toHaveClass(/active/);
  });
});

// === AX10 — System map presence ===
// The landing "star map" is a static, data-driven SVG generated by build.js (starSvg()).
// There is no interactive ray behaviour to test.
test.describe('AX10 — System map', () => {
  test('home renders the system map with an accessible label', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const section = page.locator('#system-map');
    await expect(section).toBeVisible();

    const svg = section.locator('svg[role="img"]');
    await expect(svg).toHaveCount(1);
    await expect(svg).toHaveAttribute('aria-label', /Карта зон/);
  });

  test('map labels every zone from scenarios.json', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const labels = await page.locator('#system-map svg text').allTextContents();
    for (const zone of ['КРИЗИС', 'КОМАНДА', 'ИЗМЕНЕНИЯ', 'СИСТЕМА']) {
      expect(labels).toContain(zone);
    }
  });
});

// === AX11 — Widget input is escaped, not executed as HTML (XSS regression) ===
test.describe('AX11 — Widget input escaped (XSS)', () => {
  const payload = '<img src=x onerror="window.__xss=1">';

  test('hypothesis builder renders input as text', async ({ page }) => {
    await page.goto('/weapons/upravlenie-eksperiment/');
    await page.waitForLoadState('networkidle');

    await page.fill('#hbAction', payload);
    await page.fill('#hbBehavior', payload);
    await page.fill('#hbWhy', payload);
    await page.fill('#hbMetric', payload);
    await page.locator('#hypothesisBuilder .btn-primary').click();

    await expect(page.locator('#hbResultText')).toContainText('<img');
    expect(await page.evaluate(() => window.__xss)).toBeUndefined();
  });

  test('pre-mortem tool renders input as text', async ({ page }) => {
    await page.goto('/weapons/haos/');
    await page.waitForLoadState('networkidle');

    await page.fill('#pmDecision', payload);
    await page.fill('#pmReasons', payload);
    await page.fill('#pmPrevent', payload);
    await page.locator('#premortemTool .btn-primary').click();

    await expect(page.locator('#pmResultText')).toContainText('<img');
    expect(await page.evaluate(() => window.__xss)).toBeUndefined();
  });

  test('object map builder renders input as text', async ({ page }) => {
    await page.goto('/weapons/cifrovoy-dvoynik/');
    await page.waitForLoadState('networkidle');

    await page.selectOption('#oopClass', 'ТПА');
    await page.fill('#oopName', payload);
    await page.fill('#oopAttrs', payload);
    await page.fill('#oopLinks', payload);
    await page.locator('#oopBuilder .btn-primary').click();

    await expect(page.locator('#oopResultText')).toContainText('<img');
    expect(await page.evaluate(() => window.__xss)).toBeUndefined();
  });
});

// === AX12 — Landing featured weapons ===
test.describe('AX12 — Landing featured weapons', () => {
  test('landing features four weapon cards', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const cards = page.locator('#weapons-section .weapon-card');
    await expect(cards).toHaveCount(4);
  });
});

// === AX13 — Manifesto page renders the full document ===
// Regression: the page used to show only the 10 value titles (no preamble,
// explanations, principles or closing) while the homepage button says "read in full".
test.describe('AX13 — Manifesto full content', () => {
  test('manifesto page shows preamble, 10 values, 15 principles and closing', async ({ page }) => {
    await page.goto('/manifesto/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.content-page h1')).toHaveText('Манифест');
    await expect(page.locator('.manifesto-value')).toHaveCount(10);
    await expect(page.locator('.manifesto-principles li')).toHaveCount(15);

    const content = page.locator('.content-page');
    await expect(content).toContainText('Мы — инженеры человеческих управленческих систем');
    await expect(content).toContainText('живой документ');
  });
});
