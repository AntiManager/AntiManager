'use strict';

// Products page regression: /products/ is one static commercial page built from
// an authored partial. It must ship seven owner questions, the order ladder, the
// two formats and the pack-aware CTAs — with no prices and no client claims.

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const SITE_DIR = path.join(__dirname, '..');
const DIST = path.join(SITE_DIR, 'dist');

const PACKS = ['dengi', 'operacionka', 'moshnost', 'standart', 'komanda', 'dannye', 'peredacha'];

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

test('products page ships seven offers, order, formats and pack CTAs', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });

    const page = readDist('products', 'index.html');

    assert.strictEqual((page.match(/class="section product"/g) || []).length, 7,
      'one section per product');
    assert.strictEqual((page.match(/class="product-spec"/g) || []).length, 7,
      'every product renders its spec list');
    assert.strictEqual((page.match(/class="product-q"/g) || []).length, 7,
      'every product carries the owner question');
    assert.strictEqual((page.match(/class="offer-box"/g) || []).length, 7,
      'every product carries an offer');

    PACKS.forEach(function(pack) {
      assert.ok(page.includes('href="/contact/?pack=' + pack + '"'),
        'missing pack CTA for ' + pack);
    });
    assert.strictEqual((page.match(/href="\/contact\/\?pack=/g) || []).length, 7,
      'exactly one pack CTA per product');

    assert.strictEqual((page.match(/class="order-step"/g) || []).length, 8,
      'the ladder must list steps 0-7');
    assert.strictEqual((page.match(/<tr><td>/g) || []).length, 8,
      'the formats table must list eight parameters');

    // Every sticky-TOC anchor must resolve on the same page.
    const toc = page.match(/<nav class="method-toc"[\s\S]*?<\/nav>/);
    assert.ok(toc, 'sticky TOC must ship');
    const anchors = toc[0].match(/href="#([^"]+)"/g) || [];
    assert.ok(anchors.length >= 9, 'TOC must carry all sections');
    anchors.forEach(function(a) {
      const id = a.replace(/.*#/, '').replace(/"$/, '');
      assert.ok(page.includes('id="' + id + '"'), 'TOC anchor without target: #' + id);
    });

    // Commercial guardrails: no prices and no client names/claims.
    assert.ok(page.indexOf('\u20BD') === -1, 'prices must not appear');
    ['КАБЭКС', 'Европласт', 'Линейные системы', 'Орловский'].forEach(function(name) {
      assert.ok(page.indexOf(name) === -1, 'client name must not appear: ' + name);
    });

    assert.ok(page.includes('<link rel="canonical" href="https://antimanager.pro/products/">'),
      'canonical must be set');
    assert.ok(!/data-nav="[a-z]+" aria-current="page"/.test(page),
      '/products/ has no header nav entry, so no nav item may be marked current');
    assert.ok(/<meta name="robots" content="index, follow/.test(page), 'page must be indexable');
    assert.ok(page.includes('"BreadcrumbList"'), 'page needs a breadcrumb');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(page), 'no template tokens may remain');

    assert.ok(readDist('sitemap.xml').includes('https://antimanager.pro/products/'),
      'sitemap must list /products/');

    const footer = readDist('contact', 'index.html');
    assert.ok(footer.includes('href="/products/"'), 'footer must link to the products page');

    const home = readDist('index.html');
    assert.ok(home.includes('href="/products/"'), 'home must surface the products page');
  } finally {
    runBuild(); // restore dist/ from default settings for later tests/serving
  }
});

// The form's ?pack= slugs are duplicated in client JS and service Python on
// purpose (no shared build step). Guard against the two drifting apart: an
// unknown server slug is silently dropped, losing the lead's context.
test('pack slugs stay in sync between contact.js and feedback/server.py', function() {
  const jsSrc = fs.readFileSync(path.join(SITE_DIR, 'js', 'contact.js'), 'utf-8');
  const pySrc = fs.readFileSync(path.join(SITE_DIR, 'feedback', 'server.py'), 'utf-8');

  const jsBlock = jsSrc.match(/var PACK_LABELS = \{([\s\S]*?)\n\s*\};/);
  const pyBlock = pySrc.match(/PACK_LABELS = \{([\s\S]*?)\n\}/);
  assert.ok(jsBlock, 'contact.js must define PACK_LABELS');
  assert.ok(pyBlock, 'server.py must define PACK_LABELS');

  const jsPacks = Array.from(jsBlock[1].matchAll(/^\s*([a-z0-9]+):/gm), function(m) { return m[1]; }).sort();
  const pyPacks = Array.from(pyBlock[1].matchAll(/^\s*"([a-z0-9]+)":/gm), function(m) { return m[1]; }).sort();

  assert.deepStrictEqual(jsPacks, pyPacks, 'contact.js and server.py pack slugs must match');
  PACKS.forEach(function(pack) {
    assert.ok(jsPacks.includes(pack), 'products pack missing from contact.js: ' + pack);
    assert.ok(pyPacks.includes(pack), 'products pack missing from server.py: ' + pack);
  });
});
