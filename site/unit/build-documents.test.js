'use strict';

// Typical documents regression (/genome/documents/): the hub, one full-text page
// per document, honest download links, sitemap entries and the pinned six-card
// genome landing. Derived from src/data/documents.json so a new document is
// guarded as soon as it is published.

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const SITE_DIR = path.join(__dirname, '..');
const DIST = path.join(SITE_DIR, 'dist');
const DOCUMENTS = require('../src/data/documents.json');

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

test('documents hub lists every document and keeps the genome contract intact', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });
    const hub = readDist('genome', 'documents', 'index.html');
    assert.ok(hub.includes('<h1>'), 'hub needs an H1');
    assert.ok(hub.includes('class="breadcrumbs"'), 'hub needs a breadcrumb');
    assert.ok(hub.includes('href="/genome/"'), 'breadcrumb must link the genome section');
    assert.ok(!/<!--DOCS:LIST:START-->\s*<!--DOCS:LIST:END-->/.test(hub), 'card region must not be empty');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(hub), 'no template tokens may remain in the hub');
    assert.ok(hub.includes('"@type": "CollectionPage"'), 'hub needs CollectionPage JSON-LD');
    assert.ok(hub.includes('"position": 3'), 'hub breadcrumb must be three levels deep');
    assert.ok(hub.includes('href="/contact/?pack=documents"'), 'hub needs the documents CTA');
    DOCUMENTS.forEach(function(d) {
      assert.ok(hub.includes('href="/genome/documents/' + d.slug + '/"'),
        'hub must link ' + d.slug);
      assert.ok(hub.includes(d.title), 'hub card must show the title of ' + d.slug);
    });
    assert.strictEqual((hub.match(/class="doc-tile"/g) || []).length, DOCUMENTS.length,
      'one card per document');

    const landing = readDist('genome', 'index.html');
    assert.strictEqual((landing.match(/class="doc-card"/g) || []).length, 6,
      'the six role document cards must stay unchanged');
    assert.strictEqual((landing.match(/class="doc-full"/g) || []).length, 4,
      'the four full role documents must stay unchanged');
    assert.ok(landing.includes('href="/genome/documents/"'), 'genome landing must link the hub');
    assert.ok(!landing.includes('class="doc-card documents'), 'the entry must not be a seventh doc-card');
  } finally {
    runBuild();
  }
});

test('each document page ships title, version, license, TOC and resolving interlinks', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });
    DOCUMENTS.forEach(function(d) {
      const html = readDist('genome', 'documents', d.slug, 'index.html');
      assert.ok(/<h1[^>]*>/.test(html), d.slug + ' needs an H1');
      assert.strictEqual((html.match(/<h1[ >]/g) || []).length, 1, d.slug + ' must have one H1');
      assert.ok(html.includes('Версия ' + d.version), d.slug + ' must show the version');
      assert.ok(html.includes(d.license), d.slug + ' must show the license');
      assert.ok(html.includes('AntiManager'), d.slug + ' must carry attribution');
      assert.ok(html.includes('article-toc'), d.slug + ' needs a static table of contents');
      assert.ok(html.includes('"@type": "Article"'), d.slug + ' needs an Article node');
      assert.ok(html.includes('"articleSection": "Документы"'), d.slug + ' needs the documents section');
      assert.ok(html.includes('"position": 4'), d.slug + ' breadcrumb must be four levels deep');
      assert.ok(html.includes('href="/genome/documents/"'), d.slug + ' breadcrumb must link the hub');
      assert.ok(html.includes('href="/contact/?pack=documents"'), d.slug + ' needs the documents CTA');
      assert.ok(!html.includes('[организация-публикатор]'), d.slug + ' must not leak publication placeholders');
      assert.ok(!html.includes('{дата}'), d.slug + ' must not leak date placeholders');
      assert.ok(!/\b(TODO|TBD|FIXME)\b/.test(html), d.slug + ' must not ship draft tokens');
      assert.ok(!/\{\{[a-z_]+\}\}/.test(html), d.slug + ' must not ship template tokens');
      assert.ok(!/\]\(https?:/.test(html), d.slug + ' must not ship raw Markdown links');

      const linksBlock = (html.match(/<section class="article-links"[\s\S]*?<\/section>/) || [''])[0];
      const hrefs = (linksBlock.match(/href="(\/[^"]*)"/g) || []).map(function(m) { return m.slice(6, -1); });
      assert.ok(hrefs.length >= 2, d.slug + ' needs at least two interlinks');
      hrefs.forEach(function(href) {
        const segments = href.replace(/\/$/, '').split('/').slice(1);
        const target = path.join.apply(path, [DIST].concat(segments, ['index.html']));
        assert.ok(fs.existsSync(target), d.slug + ' interlink must exist: ' + href);
      });

      // Honest materials: link a PDF/DOCX only when the file exists.
      ['pdf', 'docx'].forEach(function(kind) {
        const exists = fs.existsSync(path.join(SITE_DIR, 'materials', d.slug + '.' + kind));
        const linked = html.includes('/materials/' + d.slug + '.' + kind);
        assert.strictEqual(linked, exists,
          d.slug + ': ' + kind + ' link must match file existence');
      });
    });
  } finally {
    runBuild();
  }
});

test('documents are listed in the sitemap', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });
    const sitemap = readDist('sitemap.xml');
    assert.ok(sitemap.includes('https://antimanager.pro/genome/documents/'),
      'sitemap must list the hub');
    DOCUMENTS.forEach(function(d) {
      const loc = '/genome/documents/' + d.slug + '/';
      assert.ok(sitemap.includes('https://antimanager.pro' + loc), 'sitemap must list ' + loc);
      assert.ok(sitemap.includes(loc + '</loc>'), 'sitemap entry must be well-formed for ' + loc);
    });
  } finally {
    runBuild();
  }
});
