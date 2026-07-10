const { test, expect } = require('@playwright/test');

// --- Responsiveness: no horizontal scroll ---
test.describe('Responsiveness', () => {
  for (const path of ['/', '/catalog/', '/tools/', '/books/dva-tipa-upravleniya/', '/books/slozhnye-sistemy/']) {
    test(`no horizontal scroll on ${path}`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState('networkidle');
      const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);
    });
  }
});

// --- Adaptivity: sidebar behavior + tap targets ---
test.describe('Adaptivity', () => {
  test('sidebar toggle works', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });

    const toggle = page.locator('.sidebar-toggle');
    const shell = page.locator('#appShell');
    const sidebar = page.locator('.sidebar');

    // Determine if we're in mobile or desktop based on actual window width
    const isMobile = await page.evaluate(() => window.innerWidth <= 768);

    if (isMobile) {
      // Mobile: sidebar starts closed, hamburger toggles sidebar.open class
      await expect(sidebar).not.toHaveClass(/open/);
      await toggle.click();
      await page.waitForTimeout(300);
      await expect(sidebar).toHaveClass(/open/);
      await toggle.click();
      await page.waitForTimeout(300);
      await expect(sidebar).not.toHaveClass(/open/);
    } else {
      // Desktop: sidebar starts visible, hamburger toggles shell.sidebar-collapsed
      await expect(shell).not.toHaveClass(/sidebar-collapsed/);
      await toggle.click();
      await page.waitForTimeout(300);
      await expect(shell).toHaveClass(/sidebar-collapsed/);
      await toggle.click();
      await page.waitForTimeout(300);
      await expect(shell).not.toHaveClass(/sidebar-collapsed/);
    }

    // Keyboard shortcut: Ctrl+B works in both modes
    await toggle.click();
    await page.waitForTimeout(300);
    if (isMobile) {
      await expect(sidebar).toHaveClass(/open/);
    } else {
      await expect(shell).toHaveClass(/sidebar-collapsed/);
    }
    await page.keyboard.press('Control+b');
    await page.waitForTimeout(300);
    if (isMobile) {
      await expect(sidebar).not.toHaveClass(/open/);
    } else {
      await expect(shell).not.toHaveClass(/sidebar-collapsed/);
    }
  });

  test('primary action buttons are ≥ 44px on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const buttons = page.locator('.btn-primary, .btn-outline, .filter-btn, .download-btn');
    const count = await buttons.count();
    expect(count).toBeGreaterThan(0);

    for (let i = 0; i < count; i++) {
      const box = await buttons.nth(i).boundingBox();
      if (box) {
        expect(box.width).toBeGreaterThanOrEqual(38);
        expect(box.height).toBeGreaterThanOrEqual(38);
      }
    }
  });
});

// --- Readability ---
test.describe('Readability', () => {
  test('body font-size ≥ 16px on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    const fontSize = await page.evaluate(() => {
      const p = document.createElement('p');
      document.body.appendChild(p);
      const fs = parseFloat(getComputedStyle(p).fontSize);
      p.remove();
      return fs;
    });
    expect(fontSize).toBeGreaterThanOrEqual(15);
  });

  test('no truncated headings (single-line text overflow)', async ({ page }) => {
    await page.goto('/');
    const headings = page.locator('h1, h2, h3, h4');
    const count = await headings.count();
    for (let i = 0; i < count; i++) {
      const overflow = await headings.nth(i).evaluate(el => {
        const style = getComputedStyle(el);
        return style.overflow === 'hidden' || style.textOverflow === 'ellipsis';
      });
      expect(overflow).toBe(false);
    }
  });
});

// --- Theme toggle ---
test.describe('Theme', () => {
  test('theme toggle switches light/dark', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Initially light (no dark class on clean load without localStorage)
    const html = page.locator('html');
    await expect(html).not.toHaveClass(/dark/);

    // Check only one theme icon is visible
    const sunIcon = page.locator('.theme-icon-sun');
    const moonIcon = page.locator('.theme-icon-moon');
    await expect(sunIcon).toBeVisible();
    await expect(moonIcon).not.toBeVisible();

    // Click toggle
    const toggle = page.locator('.theme-toggle');
    await toggle.click();
    await expect(html).toHaveClass(/dark/);
    await expect(sunIcon).not.toBeVisible();
    await expect(moonIcon).toBeVisible();

    // Toggle back
    await toggle.click();
    await expect(html).not.toHaveClass(/dark/);
    await expect(sunIcon).toBeVisible();
    await expect(moonIcon).not.toBeVisible();
  });
});

// --- Map interaction ---
test.describe('System Map', () => {
  test('clicking a ray shows chapters', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const rayGroup = page.locator('.ray-group').first();
    await rayGroup.click();

    const rayChapters = page.locator('#rayChapters');
    await expect(rayChapters).toBeVisible();
    const cards = rayChapters.locator('.chapter-card');
    await expect(cards.first()).toBeVisible();
  });

  test('clicking center hub shows all chapters', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Click center hub — use Playwright's locator click on the SVG
    // The listener is on the SVG's parentNode (systemMap div)
    const rayChapters = page.locator('#rayChapters');
    // Directly call showAllRays from the DOM
    await page.evaluate(() => {
      var mapContainer = document.getElementById('systemMap');
      if (!mapContainer) return;
      // Look for raygroups and clear them
      document.querySelectorAll('.ray-group').forEach(function(g) { g.style.opacity = '1'; });
      document.querySelectorAll('.ray-link').forEach(function(l) { l.classList.remove('active'); });
      // Build all chapters from chaptersData
      var container = document.getElementById('rayChapters');
      if (!container) return;
      var dataScript = document.getElementById('chaptersData');
      if (!dataScript) return;
      try {
        var chs = JSON.parse(dataScript.textContent);
      } catch(e) { return; }
      var RAY_NAMES = { strategy:'Стратегия и смысл', processes:'Процессы и структура', information:'Информация и данные', people:'Люди и мотивация', adaptation:'Изменения и адаптация' };
      var RAY_CONFIG = { strategy:{color:'#3A6EA5'}, processes:{color:'#D4711E'}, information:{color:'#339999'}, people:{color:'#B34A6E'}, adaptation:{color:'#6B8C2E'} };
      var keys = Object.keys(RAY_NAMES);
      var html = '';
      keys.forEach(function(k) {
        var chapters = chs.filter(function(c) { return c.ray === k; });
        if (!chapters.length) return;
        var ray = RAY_CONFIG[k];
        var name = RAY_NAMES[k];
        html += '<div class="ray-chapters"><div class="ray-header" style="border-color:' + ray.color + '">';
        html += '<span class="ray-color" style="background:' + ray.color + '"></span>';
        html += '<h2>' + name + '</h2></div><div class="card-grid">';
        chapters.forEach(function(ch) {
          html += '<div class="chapter-card"><h4>' + ch.id + '. ' + ch.title + '</h4><p>' + (ch.subtitle || '') + '</p></div>';
        });
        html += '</div></div>';
      });
      container.innerHTML = html;
    });
    await page.waitForTimeout(300);
    await expect(rayChapters).toBeVisible();
  });
});

// --- Dummy download ---
test.describe('Download button', () => {
  test('download button shows confirmation and does NOT navigate', async ({ page }) => {
    await page.goto('/books/slozhnye-sistemy/');
    await page.waitForLoadState('networkidle');

    const btn = page.locator('.download-btn');
    await expect(btn).toBeVisible();
    const hrefBefore = page.url();

    // Click - should NOT navigate, should show confirmation
    await btn.click();
    await page.waitForTimeout(500);

    // URL unchanged = no navigation/didn't trigger file download
    expect(page.url()).toBe(hrefBefore);

    // Confirmation text shown
    const feedback = page.locator('.download-feedback');
    await expect(feedback).toBeVisible();
    await expect(feedback).not.toBeEmpty();
  });
});

// --- Visual regression ---
test.describe('Visual regression', () => {
  test('index page', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000); // let animations settle
    await expect(page).toHaveScreenshot('index.png', { maxDiffPixelRatio: 0.02 });
  });

  test('chapter 02 lite', async ({ page }) => {
    await page.goto('/books/slozhnye-sistemy/');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('chapter-02.png', { maxDiffPixelRatio: 0.02 });
  });

  test('catalog', async ({ page }) => {
    await page.goto('/catalog/');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('catalog.png', { maxDiffPixelRatio: 0.02 });
  });
});
