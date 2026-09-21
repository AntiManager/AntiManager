#!/usr/bin/env node
'use strict';

// Rasterize the OG card to PNG. Social networks (VK, Telegram, Facebook) do not
// render SVG og:image, so the raster version is preferred. Run after editing
// src/templates/og-image.svg: `npm run render:og`.
// Uses the already-present Playwright devDependency; no extra packages.

const fs = require('fs');
const os = require('os');
const path = require('path');
const { chromium } = require('@playwright/test');

function fileUrl(p) { return 'file:///' + p.replace(/\\/g, '/'); }

(async function () {
  const siteDir = path.join(__dirname, '..');
  const svgPath = path.join(siteDir, 'src', 'templates', 'og-image.svg');
  const outPath = path.join(siteDir, 'src', 'templates', 'og-image.png');

  const svg = fs.readFileSync(svgPath, 'utf-8');
  // fonts.css references /fonts/... (web-root absolute); rewrite to file:// so the
  // local preview document resolves the self-hosted woff2 files.
  const fontsDir = fileUrl(path.join(siteDir, 'fonts'));
  const fontCss = fs.readFileSync(path.join(siteDir, 'css', 'fonts.css'), 'utf-8')
    .replace(/url\('\/fonts\//g, "url('" + fontsDir + '/');

  const html = '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
    + 'html,body{margin:0;padding:0;background:#0A0A0A;}svg{display:block;width:1200px;height:630px;}'
    + fontCss + '</style></head><body>' + svg + '</body></html>';

  const tmp = path.join(os.tmpdir(), 'antimanager-og-' + process.pid + '.html');

  let browser;
  try {
    fs.writeFileSync(tmp, html, 'utf-8');
    browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
    await page.goto(fileUrl(tmp), { waitUntil: 'networkidle' });
    await page.evaluate(function () { return document.fonts.ready; });
    await page.screenshot({ path: outPath });
    console.log('✓ wrote ' + path.relative(siteDir, outPath));
  } finally {
    if (browser) await browser.close();
    if (fs.existsSync(tmp)) fs.unlinkSync(tmp);
  }
})().catch(function (e) { console.error(e); process.exit(1); });
