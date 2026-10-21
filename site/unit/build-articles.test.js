'use strict';

// Articles library regression (/articles/): main hub, topic hubs, article pages.
// Guards the hub cards, topic chips, topic hubs, per-article TOC, the
// four-level breadcrumb, the FAQPage structured data, the materials block, the
// Telegram CTA, the interlinks block, and that no template token or raw Markdown
// link leaks into the output. BUILD_DATE is a test seam so output stays
// deterministic; the build writes the shared dist/ so this file must not run in
// parallel with other unit tests.

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

// Derived from the data so every published article is guarded as the library
// grows (Release B/C), not only the two migrated ones.
const ALL_ARTICLES = require('../src/data/articles.json');
const ARTICLES = ALL_ARTICLES
  .filter(function(a) { return a.status === 'published'; })
  .map(function(a) { return { slug: a.slug, title: a.title, topic: a.topic }; });

test('articles hub ships topic chips and a card for each article', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });
    const hub = readDist('articles', 'index.html');
    assert.ok(hub.includes('<h1>Статьи</h1>'), 'hub needs an H1');
    assert.ok(hub.includes('class="article-topic-chips"'), 'hub needs topic chips');
    assert.ok(hub.includes('href="#topic-strategy"'), 'topic chip must anchor the topic section');
    assert.ok(hub.includes('/articles/strategy/antihrupkaya-strategiya/'), 'hub must link the flagship');
    assert.ok(hub.includes('/articles/strategy/amortizacionnaya-lovushka/'), 'hub must link the satellite');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(hub), 'no template tokens may remain in the hub');
  } finally {
    runBuild();
  }
});

test('topic hub ships a three-level breadcrumb and its cards', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });
    const hub = readDist('articles', 'strategy', 'index.html');
    assert.ok(hub.includes('<h1>Стратегия</h1>'), 'topic hub needs its topic H1');
    assert.ok(hub.includes('class="breadcrumbs"'), 'topic hub needs a visible breadcrumb');
    assert.ok(hub.includes('href="/articles/"'), 'topic breadcrumb must link the library');
    assert.ok(hub.includes('"@type": "CollectionPage"'), 'topic hub needs CollectionPage JSON-LD');
    assert.ok(hub.includes('"@type": "BreadcrumbList"'), 'topic hub needs BreadcrumbList');
    assert.ok(hub.includes('"position": 3'), 'topic breadcrumb must be three levels deep');
    assert.ok(hub.includes('/articles/strategy/antihrupkaya-strategiya/'), 'topic hub must list its articles');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(hub), 'no template tokens may remain in the topic hub');
  } finally {
    runBuild();
  }
});

test('topics without published articles do not render a hub', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });
    // Derived from data, not a frozen list: a topic leaves this set as soon as
    // its first article ships (Release B/C), and the guard stays meaningful.
    const topics = require('../src/data/article-topics.json');
    const published = require('../src/data/articles.json').filter(function(a) { return a.status === 'published'; });
    const empty = topics.filter(function(t) {
      return !published.some(function(a) { return a.topic === t.slug; });
    });
    empty.forEach(function(t) {
      assert.ok(!fs.existsSync(path.join(DIST, 'articles', t.slug, 'index.html')), 'empty topic hub must not render: ' + t.slug);
    });
  } finally {
    runBuild();
  }
});

test('each article ships TOC, 4-level breadcrumb, FAQPage, materials and CTA', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });
    ARTICLES.forEach(function(a) {
      const html = readDist('articles', a.topic, a.slug, 'index.html');
      assert.ok(html.includes('article-toc'), a.slug + ' needs a table of contents');
      assert.ok(html.includes('id="sec-'), a.slug + ' TOC anchors must be injected into headings');
      const toc = (html.match(/<nav class="article-toc"[\s\S]*?<\/nav>/) || [''])[0];
      assert.ok(toc && !toc.includes('Читайте также'), a.slug + ' TOC must not list the interlinks block');
      assert.ok(html.includes('href="/articles/"'), a.slug + ' breadcrumb must link the library');
      assert.ok(html.includes('href="/articles/' + a.topic + '/"'), a.slug + ' breadcrumb must link the topic hub');
      assert.ok(html.includes('"@type": "BreadcrumbList"'), a.slug + ' needs BreadcrumbList');
      assert.ok(html.includes('"position": 4'), a.slug + ' breadcrumb must be four levels deep');
      assert.ok(html.includes('"@type": "Article"'), a.slug + ' needs an Article node');
      assert.ok(html.includes('"@type": "FAQPage"'), a.slug + ' needs FAQPage structured data');
      assert.ok(html.includes('"@type": "Question"'), a.slug + ' FAQPage needs Question entities');
      assert.ok(html.includes('class="article-faq"'), a.slug + ' FAQ must be visible on the page');
      assert.ok(html.includes('materials-section'), a.slug + ' needs a materials block');
      assert.ok(html.includes('class="cta-band"'), a.slug + ' needs a CTA band');
      assert.ok(html.includes('https://t.me/antimanagerpro_bot'), a.slug + ' CTA must point at Telegram');
      assert.ok(html.includes('/headquarters/'), a.slug + ' CTA must link the Штаб');
      assert.ok(html.includes('class="article-links"'), a.slug + ' needs the interlink block');
      // Every interlink must resolve to a built page (a stale slug in the
      // generator previously shipped /weapons/18-<slug>/ links that 404).
      const linksBlock = (html.match(/<section class="article-links">[\s\S]*?<\/section>/) || [''])[0];
      const hrefs = (linksBlock.match(/href="(\/[^"]*)"/g) || []).map(function(m) { return m.slice(6, -1); });
      assert.ok(hrefs.length >= 2, a.slug + ' needs at least two interlinks');
      hrefs.forEach(function(href) {
        const segments = href.replace(/\/$/, '').split('/').slice(1);
        const target = path.join.apply(path, [DIST].concat(segments, ['index.html']));
        assert.ok(fs.existsSync(target), a.slug + ' interlink must exist: ' + href);
      });
      assert.ok(!html.includes('href="/strategy/'), a.slug + ' must not link the legacy /strategy/ route');
      assert.ok(!/\{\{[a-z_]+\}\}/.test(html), 'no template tokens may remain in ' + a.slug);
      assert.ok(!/\]\(https?:/.test(html), 'no raw Markdown links may remain in ' + a.slug);
      assert.ok(!html.includes('Связанные главы'), a.slug + ' must not leak the vault "Связанные" section');
    });
  } finally {
    runBuild();
  }
});

test('articles are listed in the sitemap and legacy routes are gone', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });
    const sitemap = readDist('sitemap.xml');
    const published = ALL_ARTICLES.filter(function(a) { return a.status === 'published'; });
    const topics = require('../src/data/article-topics.json');
    const publishedTopics = topics.filter(function(t) {
      return published.some(function(a) { return a.topic === t.slug; });
    });
    const locs = ['/articles/']
      .concat(publishedTopics.map(function(t) { return '/articles/' + t.slug + '/'; }))
      .concat(published.map(function(a) { return '/articles/' + a.topic + '/' + a.slug + '/'; }));
    locs.forEach(function(loc) {
      assert.ok(sitemap.includes('https://antimanager.pro' + loc), 'sitemap must list ' + loc);
      assert.ok(sitemap.includes(loc + '</loc>'), 'sitemap entry must be well-formed for ' + loc);
    });
    assert.ok(!sitemap.includes('<loc>https://antimanager.pro/strategy/'), 'sitemap must not list legacy /strategy/');
  } finally {
    runBuild();
  }
});
