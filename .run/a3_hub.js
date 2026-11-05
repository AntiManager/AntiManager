/**
 * Capture the documents hub at desktop width: the five-step flow and the
 * card list (which must now include the A3 document).
 *
 * Usage: node .run/a3_hub.js <repo-root>
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

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch({ executablePath: CHROMIUM });
  const out = [];
  try {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await ctx.newPage();
    await page.goto('https://antimanager.pro/genome/documents/',
      { waitUntil: 'networkidle', timeout: 60000 });

    const flow = page.locator('.doc-flow').first();
    await flow.screenshot({ path: path.join(SHOTS, 'hub-flow.png') });
    out.push('hub-flow.png');

    const steps = await page.evaluate(function() {
      return Array.prototype.map.call(document.querySelectorAll('.doc-flow-step'),
        function(s) {
          return {
            k: (s.querySelector('.doc-flow-k') || {}).textContent,
            t: (s.querySelector('.doc-flow-t') || {}).textContent,
          };
        });
    });
    out.push('flow steps: ' + JSON.stringify(steps));

    const tiles = await page.evaluate(function() {
      return Array.prototype.map.call(document.querySelectorAll('.doc-tile'),
        function(t) {
          return {
            title: (t.querySelector('.doc-tile-title') || {}).textContent,
            href: (t.querySelector('.doc-tile-title a') || {}).getAttribute
              ? t.querySelector('.doc-tile-title a').getAttribute('href') : null,
            meta: (t.querySelector('.doc-tile-meta') || {}).textContent,
          };
        });
    });
    out.push('tiles: ' + JSON.stringify(tiles, null, 1));

    const list = page.locator('h2', { hasText: 'Комплект' }).first();
    const section = list.locator('xpath=following-sibling::article[1]');
    await page.locator('article.doc-tile').first().screenshot({ path: path.join(SHOTS, 'hub-card-1.png') });
    await page.locator('article.doc-tile').last().screenshot({ path: path.join(SHOTS, 'hub-card-a3.png') });
    out.push('hub-card-1.png, hub-card-a3.png');

    await ctx.close();
  } finally {
    await browser.close();
  }
  console.log(out.join('\n'));
})().catch(function(err) { console.error(err); process.exit(1); });
