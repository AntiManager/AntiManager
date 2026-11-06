// Plan 12.6 — Metrika goals. The counter itself is stubbed and the tag script
// is blocked, so the test proves our event wiring, not Yandex availability.

const { test, expect } = require('@playwright/test');

async function stubMetrika(page) {
  await page.route('**/mc.yandex.ru/**', function(route) { return route.abort(); });
  await page.addInitScript(function() {
    window.__goals = [];
    window.ym = function(id, method, goal, params) {
      if (method === 'reachGoal') window.__goals.push({ goal: goal, params: params || {} });
    };
    // Keep every link on the page: navigation would wipe the collected goals.
    document.addEventListener('click', function(e) {
      var link = e.target && e.target.closest ? e.target.closest('a') : null;
      if (link) e.preventDefault();
    }, true);
  });
}

function goals(page) {
  return page.evaluate(function() { return window.__goals.map(function(g) { return g.goal; }); });
}

function goalParams(page, name) {
  return page.evaluate(function(goalName) {
    var hit = window.__goals.filter(function(g) { return g.goal === goalName; }).pop();
    return hit ? hit.params : null;
  }, name);
}

test('search goals fire on open, query and result click', async ({ page }) => {
  await stubMetrika(page);
  await page.goto('/search/?q=OEE');

  await expect.poll(function() { return goals(page); }).toContain('search_open');
  await expect.poll(function() { return goals(page); }).toContain('search_query');

  const query = await goalParams(page, 'search_query');
  expect(query.query).toBe('OEE');
  expect(query.results).toBeGreaterThan(0);

  await page.locator('.search-result-link').first().click();
  await expect.poll(function() { return goals(page); }).toContain('search_result_click');
  const click = await goalParams(page, 'search_result_click');
  expect(click.position).toBe(1);
  expect(click.url).toMatch(/^\//);
});

test('CTA and scroll goals fire on the home page', async ({ page }) => {
  await stubMetrika(page);
  await page.goto('/');

  await page.locator('[data-cta="hero_start"]').click();
  await expect.poll(function() { return goals(page); }).toContain('cta_click');
  const cta = await goalParams(page, 'cta_click');
  expect(cta.cta).toBe('hero_start');

  await page.evaluate(function() { window.scrollTo(0, document.documentElement.scrollHeight); });
  await expect.poll(function() { return goals(page); }).toContain('scroll_75');
});

test('download and Telegram goals fire; Telegram links carry UTM', async ({ page }) => {
  await stubMetrika(page);
  await page.goto('/');

  const telegram = page.locator('footer a[href*="t.me/"]').first();
  const href = await telegram.getAttribute('href');
  expect(href).toContain('utm_source=antimanager.pro');
  expect(href).toContain('utm_medium=site');
  expect(href).toContain('utm_campaign=home');
  await telegram.click();
  await expect.poll(function() { return goals(page); }).toContain('outbound_telegram');

  await page.goto('/method/audit/');
  await page.locator('a[download]').first().click();
  await expect.poll(function() { return goals(page); }).toContain('download');
  const download = await goalParams(page, 'download');
  expect(download.file).toBe('express-audit-ps.xlsx');
});
