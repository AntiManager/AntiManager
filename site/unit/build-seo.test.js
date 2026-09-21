'use strict';

// SEO regression test: build output must carry fresh dates, a raster OG image,
// enriched article metadata, breadcrumbs on static pages, four featured weapons,
// related links for zone-less articles, and a corrected landing description.
// Runs the real build with a fixed BUILD_DATE so assertions are deterministic.

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const SITE_DIR = path.join(__dirname, '..');
const DIST = path.join(SITE_DIR, 'dist');

function runBuild(extraEnv) {
  return execFileSync(process.execPath, ['build.js'], {
    cwd: SITE_DIR,
    env: Object.assign({}, process.env, extraEnv || {}),
    encoding: 'utf-8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
}

function readDist() {
  return fs.readFileSync(path.join.apply(path, [DIST].concat(Array.prototype.slice.call(arguments))), 'utf-8');
}
function distPath() {
  return path.join.apply(path, [DIST].concat(Array.prototype.slice.call(arguments)));
}

test('build emits SEO metadata', function() {
  const BUILD_DATE = '2026-01-02';
  try {
    runBuild({ BUILD_DATE: BUILD_DATE });

    // 1. Dynamic build date in sitemap and JSON-LD / OG.
    const sitemap = readDist('sitemap.xml');
    assert.ok(sitemap.includes('<lastmod>' + BUILD_DATE + '</lastmod>'), 'sitemap lastmod must use BUILD_DATE');

    const weapon = readDist('weapons', 'sistemnaya-dinamika', 'index.html');
    assert.ok(weapon.includes('"dateModified": "' + BUILD_DATE + '"'), 'weapon dateModified must use BUILD_DATE');
    assert.ok(weapon.includes('<meta property="article:modified_time" content="' + BUILD_DATE + '">'), 'article:modified_time must be present');

    // 2. Zone-less weapon keeps an internal related block.
    assert.ok(weapon.includes('В том же окопе'), 'zone-less weapon must keep related links');

    // 3. article:tag count matches the weapon tags count.
    const weapons = JSON.parse(fs.readFileSync(path.join(SITE_DIR, 'src', 'data', 'weapons.json'), 'utf-8'));
    const w02 = weapons.find(function(w) { return w.slug === 'slozhnye-sistemy'; });
    const page02 = readDist('weapons', 'slozhnye-sistemy', 'index.html');
    const tagCount = (page02.match(/property="article:tag"/g) || []).length;
    assert.strictEqual(tagCount, w02.tags.length, 'article:tag metas must match weapon tags');

    // 4. Static page has a breadcrumb.
    assert.ok(readDist('arsenal', 'index.html').includes('"BreadcrumbList"'), 'static pages need BreadcrumbList');

    // 5. Landing: four featured weapons; corrected meta description.
    const index = readDist('index.html');
    const sectionHtml = index.slice(index.indexOf('id="weapons-section"')).split('</section>')[0];
    const featured = (sectionHtml.match(/class="weapon-card"/g) || []).length;
    assert.strictEqual(featured, 4, 'landing must feature four weapons');
    assert.ok(index.includes('4 контура'), 'meta description must state 4 zones');
    assert.ok(index.includes('22 главы'), 'meta description must use the correct plural');
    assert.ok(!index.includes('5 контуров'), 'stale "5 контуров" must be gone');

    // 6. Raster OG image is produced and referenced.
    assert.ok(fs.existsSync(distPath('og-image.png')), 'dist/og-image.png must exist');
    assert.ok(index.includes('content="https://antimanager.pro/og-image.png"'), 'og:image must point to the PNG');
  } finally {
    runBuild(); // restore dist/ from default settings for later tests/serving
  }
});
