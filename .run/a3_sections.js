/**
 * Capture specific sections of the live A3 page as element screenshots, so the
 * tables and the blank form can be inspected visually without a 30 000px image.
 *
 * Usage: node .run/a3_sections.js <repo-root>
 */
'use strict';

const fs = require('fs');
const path = require('path');

const root = path.resolve(process.argv[2] || '.');
const SITE_DIR = path.join(root, 'site');
const { chromium } = require(path.join(SITE_DIR, 'node_modules', '@playwright', 'test'));

const CHROMIUM = path.join(process.env.LOCALAPPDATA, 'ms-playwright',
  'chromium-1248', 'chrome-win64', 'chrome.exe');
const SHOTS = path.join(root, '.run', 'shots');
const URL = 'https://antimanager.pro/genome/documents/a3-reshenie-problem/';

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch({ executablePath: CHROMIUM });
  const out = [];
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });

    // 1. The П1-П16 parameters table (section 3.3).
    const params = page.locator('p', { hasText: 'заполняются один раз приказом' });
    if (await params.count()) {
      const wrap = params.first().locator('xpath=following::div[contains(@class,"table-wrap")][1]');
      await wrap.screenshot({ path: path.join(SHOTS, 'sec-params.png') });
      out.push('sec-params.png (П1–П16 table)');
    }

    // 2. The blank A3 form (Приложение Б) — first table after Б.1.
    const b1 = page.locator('p', { hasText: 'Б.1 Бланк А3' });
    if (await b1.count()) {
      const form = b1.first().locator('xpath=following::div[contains(@class,"table-wrap")][1]');
      await form.screenshot({ path: path.join(SHOTS, 'sec-form-b1.png') });
      out.push('sec-form-b1.png (blank А3 form)');
    }

    // 3. The download block + interlinks ("Читайте также").
    const links = page.locator('section.article-links').first();
    if (await links.count()) {
      await links.screenshot({ path: path.join(SHOTS, 'sec-links.png') });
      out.push('sec-links.png (interlinks)');
    }

    // 4. Verify the download links actually resolve.
    const dl = await page.evaluate(function() {
      return Array.prototype.map.call(
        document.querySelectorAll('a[href*="/materials/a3-reshenie-problem"]'),
        function(a) { return { href: a.getAttribute('href'), text: a.textContent.trim() }; });
    });
    for (const d of dl) {
      const r = await page.request.get('https://antimanager.pro' + d.href);
      out.push('download ' + d.href + ' -> ' + r.status() + ' (' + (r.headers()['content-type'] || '?') + ')');
    }

    // 5. Click the TOC and confirm the anchor navigates.
    const tocFirst = page.locator('.article-toc a').first();
    if (await tocFirst.count()) {
      const href = await tocFirst.getAttribute('href');
      await tocFirst.click();
      await page.waitForTimeout(400);
      const y = await page.evaluate(function() { return window.scrollY; });
      out.push('TOC click ' + href + ' -> scrollY=' + Math.round(y));
    }

    // 6. Mobile hero + hub page.
    const mob = await browser.newContext({ viewport: { width: 375, height: 812 } });
    const mp = await mob.newPage();
    await mp.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
    await mp.screenshot({ path: path.join(SHOTS, 'mob-hero.png') });
    out.push('mob-hero.png (mobile hero)');
    const hub = await mob.newPage();
    await hub.goto('https://antimanager.pro/genome/documents/', { waitUntil: 'networkidle', timeout: 60000 });
    await hub.screenshot({ path: path.join(SHOTS, 'hub-desktop.png'), fullPage: false });
    out.push('hub-desktop.png (documents hub)');
    await mob.close();

    await context.close();
  } finally {
    await browser.close();
  }
  console.log(out.join('\n'));
})().catch(function(err) { console.error(err); process.exit(1); });
