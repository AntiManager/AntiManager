/**
 * Render only the A3 document PDF, leaving every other tracked PDF untouched.
 *
 * `npm run render:pdf` rewrites all 44 target PDFs (a known churn: metadata
 * differs each run) and, on this machine, fails because Playwright 1.62 expects
 * Chromium build 1234 while 1248 is installed. This script reuses the same
 * technique as site/scripts/render-pdf.js — serve dist/, print the page in print
 * media — but with the installed Chromium passed in explicitly, and only for one
 * URL.
 *
 * Usage:
 *   node .run/a3_pdf.js <url-path> <out-pdf> <repo-root>
 */
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');

const args = process.argv.slice(2);
const urlPath = args[0];
const outPdf = args[1];
const root = path.resolve(args[2]);

const CHROMIUM = path.join(process.env.LOCALAPPDATA, 'ms-playwright',
  'chromium-1248', 'chrome-win64', 'chrome.exe');

const SITE_DIR = path.join(root, 'site');
const DIST = path.join(SITE_DIR, 'dist');

const { chromium } = require(path.join(SITE_DIR, 'node_modules', '@playwright', 'test'));

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.woff2': 'font/woff2',
  '.pdf': 'application/pdf',
  '.xml': 'application/xml',
  '.txt': 'text/plain; charset=utf-8',
};

function serve(dir) {
  return new Promise(function(resolve) {
    const server = http.createServer(function(req, res) {
      let p = decodeURIComponent(req.url.split('?')[0]);
      if (p.endsWith('/')) p += 'index.html';
      const file = path.join(dir, path.normalize(p));
      if (!file.startsWith(dir)) { res.statusCode = 403; return res.end('forbidden'); }
      fs.readFile(file, function(err, data) {
        if (err) { res.statusCode = 404; return res.end('not found'); }
        res.setHeader('Content-Type', MIME[path.extname(file).toLowerCase()] || 'application/octet-stream');
        res.end(data);
      });
    });
    server.listen(0, '127.0.0.1', function() { resolve(server); });
  });
}

async function main() {
  if (!fs.existsSync(CHROMIUM)) {
    throw new Error('Chromium not found at ' + CHROMIUM);
  }
  if (!fs.existsSync(DIST)) {
    throw new Error('dist/ not found — run the build first.');
  }
  const segments = decodeURIComponent(urlPath).replace(/^\/|\/$/g, '').split('/');
  const pagePath = path.join.apply(path, [DIST].concat(segments, ['index.html']));
  if (!fs.existsSync(pagePath)) {
    throw new Error('dist page missing: ' + pagePath);
  }

  const server = await serve(DIST);
  const port = server.address().port;
  const browser = await chromium.launch({ executablePath: CHROMIUM });
  try {
    const page = await browser.newPage();
    await page.goto('http://127.0.0.1:' + port + urlPath, { waitUntil: 'networkidle' });
    await page.emulateMedia({ media: 'print' });
    for (let attempt = 1; ; attempt++) {
      try {
        await page.pdf({
          path: outPdf,
          format: 'A4',
          printBackground: true,
          margin: { top: '16mm', bottom: '16mm', left: '14mm', right: '14mm' },
        });
        break;
      } catch (err) {
        if (attempt >= 3) throw err;
        await new Promise(function(r) { setTimeout(r, attempt * 1000); });
      }
    }
    console.log('OK pdf: ' + outPdf + ' (' + fs.statSync(outPdf).size + ' bytes)');
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch(function(err) { console.error(err); process.exit(1); });
