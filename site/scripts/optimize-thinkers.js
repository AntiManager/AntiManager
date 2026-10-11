#!/usr/bin/env node
'use strict';

// Generate .webp siblings for the thinker photos so the archive page can ship a
// lighter image via <picture> while keeping the original as a fallback.
// Uses the already-installed Playwright Chromium + canvas, so no native image
// dependency (sharp/imagemagick) is required.
//
//   node scripts/optimize-thinkers.js
//
// Originals stay untouched; only <name>.webp is (re)written next to them.

const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');

const SRC_DIR = path.join(__dirname, '..', '..', 'Фото_мыслителей');
const MAX_WIDTH = 640;
const QUALITY = 0.82;

async function main() {
  if (!fs.existsSync(SRC_DIR)) {
    console.error('Source dir not found: ' + SRC_DIR);
    process.exit(1);
  }
  const files = fs.readdirSync(SRC_DIR).filter(function(f) { return /\.(jpe?g|png)$/i.test(f); });
  if (!files.length) { console.log('No raster thinker photos to optimize.'); return; }

  const browser = await chromium.launch();
  const page = await browser.newPage();
  let saved = 0;

  for (const file of files) {
    const buf = fs.readFileSync(path.join(SRC_DIR, file));
    const mime = /\.png$/i.test(file) ? 'image/png' : 'image/jpeg';
    const dataUrl = 'data:' + mime + ';base64,' + buf.toString('base64');

    const out = await page.evaluate(async function(args) {
      const img = new Image();
      await new Promise(function(res, rej) {
        img.onload = res;
        img.onerror = rej;
        img.src = args.dataUrl;
      });
      const scale = Math.min(1, args.maxWidth / img.naturalWidth);
      const w = Math.round(img.naturalWidth * scale);
      const h = Math.round(img.naturalHeight * scale);
      const canvas = document.createElement('canvas');
      canvas.width = w;
      canvas.height = h;
      canvas.getContext('2d').drawImage(img, 0, 0, w, h);
      return { data: canvas.toDataURL('image/webp', args.quality), w: w, h: h };
    }, { dataUrl: dataUrl, maxWidth: MAX_WIDTH, quality: QUALITY });

    const base64 = out.data.replace(/^data:image\/webp;base64,/, '');
    const webp = Buffer.from(base64, 'base64');
    const dest = path.join(SRC_DIR, file.replace(/\.(jpe?g|png)$/i, '.webp'));

    if (webp.length >= buf.length) {
      console.log('  = ' + file + ' (webp not smaller: ' + webp.length + ' vs ' + buf.length + ', skipped)');
      continue;
    }
    fs.writeFileSync(dest, webp);
    saved += buf.length - webp.length;
    console.log('  ✓ ' + file + ' → ' + path.basename(dest) + '  ' + out.w + 'x' + out.h +
      '  ' + Math.round(buf.length / 1024) + 'KB → ' + Math.round(webp.length / 1024) + 'KB');
  }

  await browser.close();
  console.log('\nSaved ~' + Math.round(saved / 1024) + 'KB total.');
}

main().catch(function(err) { console.error(err); process.exit(1); });
