#!/usr/bin/env node
'use strict';

// Render every full-text page to a downloadable PDF artifact.
// Serves dist/ locally, prints /weapons/<slug>/full/ in print media, and writes
// site/materials/<slug>.pdf. Run after the build: `npm run render:pdf`.
// No new dependency: @playwright/test already ships Chromium for the e2e suite.

const fs = require('fs');
const path = require('path');
const http = require('http');
const { chromium } = require('@playwright/test');

const SITE_DIR = path.join(__dirname, '..');
const DIST = path.join(SITE_DIR, 'dist');
const OUT = path.join(SITE_DIR, 'materials');
const FULL_DIR = path.join(SITE_DIR, 'src', 'content', 'full');

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

function serve(root) {
  return new Promise(function(resolve) {
    const server = http.createServer(function(req, res) {
      let urlPath = decodeURIComponent(req.url.split('?')[0]);
      if (urlPath.endsWith('/')) urlPath += 'index.html';
      const file = path.join(root, path.normalize(urlPath));
      if (!file.startsWith(root)) { res.statusCode = 403; return res.end('forbidden'); }
      fs.readFile(file, function(err, data) {
        if (err) { res.statusCode = 404; return res.end('not found'); }
        res.setHeader('Content-Type', MIME[path.extname(file).toLowerCase()] || 'application/octet-stream');
        res.end(data);
      });
    });
    server.listen(0, '127.0.0.1', function() { resolve(server); });
  });
}

function fullSlugs() {
  if (!fs.existsSync(FULL_DIR)) return [];
  return fs.readdirSync(FULL_DIR)
    .filter(function(f) { return f.endsWith('.html'); })
    .map(function(f) { return f.replace(/^\d+-(.+)\.html$/, '$1'); })
    .filter(Boolean)
    .sort();
}

async function main() {
  if (!fs.existsSync(DIST)) {
    console.error('dist/ not found — run `npm run build` first.');
    process.exit(1);
  }
  const slugs = fullSlugs();
  if (!slugs.length) {
    console.log('No full-text articles found; nothing to render.');
    return;
  }
  fs.mkdirSync(OUT, { recursive: true });

  const server = await serve(DIST);
  const port = server.address().port;
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    for (const slug of slugs) {
      await page.goto('http://127.0.0.1:' + port + '/weapons/' + slug + '/full/', { waitUntil: 'networkidle' });
      await page.emulateMedia({ media: 'print' });
      const out = path.join(OUT, slug + '.pdf');
      await page.pdf({
        path: out,
        format: 'A4',
        printBackground: true,
        margin: { top: '16mm', bottom: '16mm', left: '14mm', right: '14mm' },
      });
      console.log('  ✓ ' + path.relative(SITE_DIR, out));
    }
  } finally {
    await browser.close();
    server.close();
  }
  console.log('\n✅ PDF materials rendered: ' + slugs.length + '\n');
}

main().catch(function(err) { console.error(err); process.exit(1); });
