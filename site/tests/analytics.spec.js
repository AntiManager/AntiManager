// Plan 12.6 — Metrika goals, mirrored into GA4. Both tags are stubbed/blocked,
// so the test proves our event wiring, not Yandex or Google availability.

const { test, expect } = require('@playwright/test');

async function stubMetrika(page) {
  await page.route('**/mc.yandex.ru/**', function(route) { return route.abort(); });
  // GA4 must not reach the network either; the inline gtag() copies events into
  // window.dataLayer, which is what we assert on.
  await page.route('**/googletagmanager.com/**', function(route) { return route.abort(); });
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

// The inline declaration is `function gtag(){dataLayer.push(arguments)}`, so a
// window.__ga stub would be irrelevant: read the queue the real gtag() fills.
function gaEvents(page) {
  return page.evaluate(function() {
    return (window.dataLayer || []).filter(function(item) {
      return item && item[0] === 'event';
    }).map(function(item) {
      return { name: item[1], params: item[2] || {} };
    });
  });
}

function gaEventNames(page) {
  return page.evaluate(function() {
    return (window.dataLayer || []).filter(function(item) {
      return item && item[0] === 'event';
    }).map(function(item) { return item[1]; });
  });
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

  await expect.poll(function() { return gaEventNames(page); }).toEqual(
    expect.arrayContaining(['search_open', 'search_query', 'search_result_click'])
  );
  const gaQuery = (await gaEvents(page)).filter(function(e) { return e.name === 'search_query'; }).pop();
  expect(gaQuery.params.query).toBe('OEE');
});

test('CTA and scroll goals fire on the home page', async ({ page }) => {
  await stubMetrika(page);
  await page.goto('/');

  await page.locator('[data-cta="hero_start"]').click();
  await expect.poll(function() { return goals(page); }).toContain('cta_click');
  const cta = await goalParams(page, 'cta_click');
  expect(cta.cta).toBe('hero_start');

  await expect.poll(function() { return gaEventNames(page); }).toContain('cta_click');
  const gaCta = (await gaEvents(page)).filter(function(e) { return e.name === 'cta_click'; }).pop();
  expect(gaCta.params.cta).toBe('hero_start');

  await page.evaluate(function() { window.scrollTo(0, document.documentElement.scrollHeight); });
  await expect.poll(function() { return goals(page); }).toContain('scroll_75');
  await expect.poll(function() { return gaEventNames(page); }).toContain('scroll_75');
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

  await expect.poll(function() { return gaEventNames(page); }).toContain('download');
  const gaDownload = (await gaEvents(page)).filter(function(e) { return e.name === 'download'; }).pop();
  expect(gaDownload.params.file).toBe('express-audit-ps.xlsx');
});
