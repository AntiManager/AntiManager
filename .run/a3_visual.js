/**
 * Visual check of the live A3 document page with Playwright Chromium.
 *
 * Captures the page at desktop/tablet/mobile widths, reports layout problems
 * (horizontal scroll, overflowing tables, console errors, failed requests),
 * and writes screenshots into .run/shots/.
 *
 * Usage: node .run/a3_visual.js <repo-root>
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

const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'mobile', width: 375, height: 812 },
];

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch({ executablePath: CHROMIUM });
  const report = [];
  try {
    for (const vp of VIEWPORTS) {
      const context = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        deviceScaleFactor: 1,
      });
      const page = await context.newPage();
      const consoleErrors = [];
      const failed = [];
      page.on('console', function(m) { if (m.type() === 'error') consoleErrors.push(m.text()); });
      page.on('requestfailed', function(r) { failed.push(r.url() + ' :: ' + (r.failure() || {}).errorText); });

      const resp = await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(600);

      const metrics = await page.evaluate(function() {
        var de = document.documentElement;
        var hscroll = de.scrollWidth > de.clientWidth + 1;
        // Any element wider than the viewport that is not inside a .table-wrap
        var overflow = [];
        document.querySelectorAll('body *').forEach(function(el) {
          var r = el.getBoundingClientRect();
          if (r.width > de.clientWidth + 2 && el.tagName !== 'HTML' && el.tagName !== 'BODY') {
            var wrap = el.closest('.table-wrap');
            if (!wrap) overflow.push(el.tagName + '.' + (el.className || '').toString().slice(0, 40));
          }
        });
        return {
          hscroll: hscroll,
          scrollWidth: de.scrollWidth,
          clientWidth: de.clientWidth,
          docHeight: de.scrollHeight,
          h1: (document.querySelector('h1') || {}).textContent || '',
          h2count: document.querySelectorAll('h2').length,
          tables: document.querySelectorAll('.table-wrap table').length,
          tocLinks: document.querySelectorAll('.article-toc a').length,
          downloads: Array.prototype.map.call(
            document.querySelectorAll('a[href*="/materials/a3-reshenie-problem"]'),
            function(a) { return a.getAttribute('href'); }),
          links: Array.prototype.map.call(
            document.querySelectorAll('.article-links a'),
            function(a) { return a.getAttribute('href'); }),
          overflow: overflow.slice(0, 6),
        };
      });

      const shot = path.join(SHOTS, 'a3-' + vp.name + '.png');
      await page.screenshot({ path: shot, fullPage: false });

      // Full page only for desktop (keeps the files small).
      if (vp.name === 'desktop') {
        await page.screenshot({ path: path.join(SHOTS, 'a3-desktop-full.png'), fullPage: true });
      }

      report.push({
        viewport: vp.name + ' ' + vp.width + 'x' + vp.height,
        status: resp ? resp.status() : 'no response',
        hscroll: metrics.hscroll,
        scrollWidth: metrics.scrollWidth,
        clientWidth: metrics.clientWidth,
        docHeight: metrics.docHeight,
        h1: metrics.h1,
        h2count: metrics.h2count,
        tables: metrics.tables,
        tocLinks: metrics.tocLinks,
        downloads: metrics.downloads,
        links: metrics.links,
        overflow: metrics.overflow,
        consoleErrors: consoleErrors,
        failedRequests: failed,
      });
      await context.close();
    }
  } finally {
    await browser.close();
  }
  console.log(JSON.stringify(report, null, 2));
})().catch(function(err) { console.error(err); process.exit(1); });
