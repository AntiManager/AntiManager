const { test, expect } = require('@playwright/test');

// /playbook/ facets: two chip groups, shareable ?situation=&role= state and a
// no-JS baseline where every chapter is visible.
test.describe('Book facets', () => {
  test('situation and role filters combine and stay in the URL', async ({ page }) => {
    await page.goto('/playbook/');
    await page.waitForLoadState('networkidle');

    await page.locator('.filter-btn[data-filter-type="situation"][data-filter="crisis"]').click();
    await expect(page).toHaveURL(/situation=crisis/);

    await page.locator('.filter-btn[data-filter-type="role"][data-filter="director"]').click();
    await expect(page).toHaveURL(/situation=crisis/);
    await expect(page).toHaveURL(/role=director/);

    const shown = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('#arsenalGrid .weapon-card'))
        .filter(function(card) { return !card.hidden; })
        .map(function(card) { return { situation: card.dataset.situation, roles: card.dataset.roles.split(' ') }; });
    });
    expect(shown.length).toBeGreaterThan(0);
    expect(shown.length).toBeLessThan(23);
    for (const card of shown) {
      expect(card.situation).toBe('crisis');
      expect(card.roles).toContain('director');
    }
    await expect(page.locator('#bookFilterStatus')).toContainText('Показано ' + shown.length);
  });

  test('a shareable deep link applies both filters on load', async ({ page }) => {
    await page.goto('/playbook/?situation=team&role=hr');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.filter-btn[data-filter-type="situation"][data-filter="team"]')).toHaveClass(/active/);
    await expect(page.locator('.filter-btn[data-filter-type="role"][data-filter="hr"]')).toHaveClass(/active/);

    const count = await page.locator('#arsenalGrid .weapon-card:not([hidden])').count();
    const total = await page.locator('#arsenalGrid .weapon-card').count();
    expect(total).toBe(23);
    expect(count).toBeGreaterThan(0);
    expect(count).toBeLessThan(total);
  });

  test('invalid params fall back to every chapter', async ({ page }) => {
    await page.goto('/playbook/?situation=nope&role=ghost');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.filter-btn[data-filter-type="situation"][data-filter="all"]')).toHaveClass(/active/);
    await expect(page.locator('.filter-btn[data-filter-type="role"][data-filter="all"]')).toHaveClass(/active/);
    await expect(page.locator('#arsenalGrid .weapon-card:not([hidden])')).toHaveCount(23);
  });

  test('without JavaScript every chapter stays visible', async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto('/playbook/');

    await expect(page.locator('#arsenalGrid .weapon-card')).toHaveCount(23);
    await expect(page.locator('#arsenalGrid .weapon-card[hidden]')).toHaveCount(0);
    await context.close();
  });
});

// /start/: four anchored situations, three steps each, and a CTA that opens the
// filtered book. A hash link must land on the requested block.
test.describe('Start here', () => {
  test('four situations render symptoms, steps, materials and a filtered CTA', async ({ page }) => {
    await page.goto('/start/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.start-situation')).toHaveCount(4);
    await expect(page.locator('.start-situation .start-symptoms li')).toHaveCount(11);
    await expect(page.locator('.start-situation .start-step-link')).toHaveCount(12);
    await expect(page.locator('.start-situation .start-material')).toHaveCount(8);
    await expect(page.locator('.start-cta')).toHaveCount(4);

    for (const id of ['crisis', 'team', 'changes', 'system']) {
      await expect(page.locator('#' + id)).toHaveCount(1);
      await expect(page.locator('#' + id + ' .start-steps ol > li')).toHaveCount(3);
    }
  });

  test('a hash link opens its situation block', async ({ page }) => {
    await page.goto('/start/#changes');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('#changes')).toBeInViewport();
  });

  test('the CTA opens the book filtered to the situation', async ({ page }) => {
    await page.goto('/start/');
    await page.locator('#crisis .start-cta').click();
    await expect(page).toHaveURL(/\/playbook\/\?situation=crisis/);
    await expect(page.locator('.filter-btn[data-filter-type="situation"][data-filter="crisis"]')).toHaveClass(/active/);
    const shown = await page.locator('#arsenalGrid .weapon-card:not([hidden])').count();
    expect(shown).toBe(4);
  });
});
