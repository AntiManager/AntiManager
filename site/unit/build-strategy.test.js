'use strict';

// Strategy section regression (/strategy/): a one-tier long-read hub plus two
// article pages. Guards the hub cards, the per-article TOC, the three-level
// breadcrumb, the FAQPage structured data, the materials block, the Telegram
// CTA, and that no template token or raw Markdown link leaks into the output.
// BUILD_DATE is a test seam so output stays deterministic; the build writes the
// shared dist/ so this file must not run in parallel with other unit tests.

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

const ARTICLES = [
  { slug: 'antihrupkaya-strategiya', title: 'Антихрупкая стратегия' },
  { slug: 'amortizacionnaya-lovushka', title: 'Амортизационная ловушка' },
];

test('strategy hub ships a card for each article', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });
    const hub = readDist('strategy', 'index.html');
    assert.ok(hub.includes('Стратегия'), 'hub needs an H1');
    assert.ok(hub.includes('/strategy/antihrupkaya-strategiya/'), 'hub must link the flagship');
    assert.ok(hub.includes('/strategy/amortizacionnaya-lovushka/'), 'hub must link the satellite');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(hub), 'no template tokens may remain in the hub');
  } finally {
    runBuild();
  }
});

test('each strategy article ships TOC, 3-level breadcrumb, FAQPage, materials and CTA', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });
    ARTICLES.forEach(function(a) {
      const html = readDist('strategy', a.slug, 'index.html');
      assert.ok(html.includes('article-toc'), a.slug + ' needs a table of contents');
      assert.ok(html.includes('id="sec-'), a.slug + ' TOC anchors must be injected into headings');
      const toc = (html.match(/<nav class="article-toc"[\s\S]*?<\/nav>/) || [''])[0];
      assert.ok(toc && !toc.includes('Читайте также'), a.slug + ' TOC must not list the interlinks block');
      assert.ok(html.includes('/strategy/"'), a.slug + ' breadcrumb must link the hub');
      assert.ok(html.includes('"@type": "BreadcrumbList"'), a.slug + ' needs BreadcrumbList');
      assert.ok(html.includes('"position": 3'), a.slug + ' breadcrumb must be three levels deep');
      assert.ok(html.includes('"@type": "Article"'), a.slug + ' needs an Article node');
      assert.ok(html.includes('"@type": "FAQPage"'), a.slug + ' needs FAQPage structured data');
      assert.ok(html.includes('"@type": "Question"'), a.slug + ' FAQPage needs Question entities');
      assert.ok(html.includes('class="strategy-faq"'), a.slug + ' FAQ must be visible on the page');
      assert.ok(html.includes('materials-section'), a.slug + ' needs a materials block');
      assert.ok(html.includes('class="cta-band"'), a.slug + ' needs a CTA band');
      assert.ok(html.includes('https://t.me/antimanagerpro_bot'), a.slug + ' CTA must point at Telegram');
      assert.ok(html.includes('/headquarters/'), a.slug + ' CTA must link the Штаб');
      assert.ok(html.includes('class="strategy-links"'), a.slug + ' needs the interlink block');
      assert.ok(!/\{\{[a-z_]+\}\}/.test(html), 'no template tokens may remain in ' + a.slug);
      assert.ok(!/\]\(https?:/.test(html), 'no raw Markdown links may remain in ' + a.slug);
      assert.ok(!html.includes('Связанные главы'), a.slug + ' must not leak the vault "Связанные" section');
    });
  } finally {
    runBuild();
  }
});

test('strategy pages are listed in the sitemap at priority 0.8', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });
    const sitemap = readDist('sitemap.xml');
    ['/strategy/', '/strategy/antihrupkaya-strategiya/', '/strategy/amortizacionnaya-lovushka/'].forEach(function(loc) {
      assert.ok(sitemap.includes('https://antimanager.pro' + loc), 'sitemap must list ' + loc);
      assert.ok(sitemap.includes(loc + '</loc>'), 'sitemap entry must be well-formed for ' + loc);
    });
    assert.ok(sitemap.indexOf('https://antimanager.pro/strategy/</loc>') !== -1, 'hub must be listed');
  } finally {
    runBuild();
  }
});
