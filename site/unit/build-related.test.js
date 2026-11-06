'use strict';

// Release B regression: prev/next chapter links, cross-type related blocks,
// origins destinations and the next-step CTA. Runs the real build with a fixed
// BUILD_DATE so assertions are deterministic.

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const SITE_DIR = path.join(__dirname, '..');
const DIST = path.join(SITE_DIR, 'dist');

function runBuild() {
  return execFileSync(process.execPath, ['build.js'], {
    cwd: SITE_DIR,
    env: Object.assign({}, process.env, { BUILD_DATE: '2026-01-02' }),
    encoding: 'utf-8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
}

function readDist() {
  return fs.readFileSync(path.join.apply(path, [DIST].concat(Array.prototype.slice.call(arguments))), 'utf-8');
}

function section(html, className) {
  var start = html.indexOf('<section class="' + className + '"');
  if (start === -1) return '';
  return html.slice(start, html.indexOf('</section>', start));
}

function navLinks(html) {
  const start = html.indexOf('<nav class="chapter-nav"');
  if (start === -1) return [];
  const block = html.slice(start, html.indexOf('</nav>', start));
  return (block.match(/<a [^>]+href="([^"]+)"[^>]*rel="(prev|next)"/g) || []).map(function(anchor) {
    const href = anchor.match(/href="([^"]+)"/)[1];
    const rel = anchor.match(/rel="(prev|next)"/)[1];
    return { href: href, rel: rel };
  });
}

test('chapter pages carry ordered prev/next, cross-type related and a next-step CTA', function() {
  try {
    runBuild();

    ['index.html', path.join('full', 'index.html')].forEach(function(file) {
      const html = readDist.apply(null, ['playbook', 'processy'].concat(file.split(path.sep)));
      const links = navLinks(html);
      assert.deepStrictEqual(links, [
        { href: '/playbook/kaskadirovanie-celey/', rel: 'prev' },
        { href: '/playbook/dengi-v-dvizhenii/', rel: 'next' },
      ], 'chapter ' + file + ' must keep id order in prev/next');

      const related = section(html, 'related-block');
      assert.ok(related.includes('Связанные материалы'), 'chapter ' + file + ' needs a cross-type related block');
      assert.ok(related.includes('related-type">Статья<'), 'related block must include a long-read');
      assert.ok(related.includes('related-type">Документ<'), 'related block must include a document');
      assert.ok(related.includes('/articles/practice/vnedrenie-berezhlivogo-proizvodstva/'), 'changes chapter must link its situation article');
      assert.ok(related.includes('/method/documents/snu-kontur-uluchsheniy/'), 'changes chapter must link its situation document');

      assert.ok(html.includes('class="cta-band next-step"'), 'chapter ' + file + ' needs a next-step CTA');
      assert.ok(html.includes('href="/start/#changes"'), 'next-step CTA must deep-link the chapter situation');
      assert.ok(!/\{\{[a-z_]+\}\}/.test(html), 'no template tokens may remain on ' + file);
    });
  } finally {
    runBuild();
  }
});

test('prev/next edges match the catalog order', function() {
  try {
    runBuild();

    const first = readDist('playbook', 'mayatnik-upravleniya', 'index.html');
    assert.deepStrictEqual(navLinks(first), [{ href: '/playbook/slozhnye-sistemy/', rel: 'next' }], 'first chapter has no prev link');

    const last = readDist('playbook', 'kommunikacionnyy-konstruktor', 'index.html');
    assert.deepStrictEqual(navLinks(last), [{ href: '/playbook/udarit-po-traektorii/', rel: 'prev' }], 'last chapter has no next link');
  } finally {
    runBuild();
  }
});

test('origins cards lead to 2–3 real chapters/articles', function() {
  try {
    runBuild();

    const html = readDist('about', 'origins', 'index.html');
    const cards = html.match(/<div class="thinker-card">/g) || [];
    assert.strictEqual(cards.length, 9, 'origins must render all nine thinkers');

    const blocks = html.match(/<div class="thinker-links">[\s\S]*?<\/div>/g) || [];
    assert.strictEqual(blocks.length, 9, 'every thinker card needs a links block');

    blocks.forEach(function(block) {
      const hrefs = (block.match(/href="([^"]+)"/g) || []).map(function(href) { return href.slice(6, -1); });
      assert.ok(hrefs.length >= 2 && hrefs.length <= 3, 'each thinker needs 2–3 destinations, got ' + hrefs.length);
      hrefs.forEach(function(href) {
        const target = href.split('#')[0];
        const file = target === '/' ? 'index.html' : path.join(target.replace(/^\//, ''), 'index.html');
        assert.ok(fs.existsSync(path.join(DIST, file)), 'origin link must resolve: ' + href);
      });
    });
  } finally {
    runBuild();
  }
});

test('articles keep a cross-type related block before their CTA', function() {
  try {
    runBuild();

    const html = readDist('articles', 'practice', 'raschet-oee', 'index.html');
    const related = section(html, 'related-block');
    assert.ok(related.includes('Из плейбука и методологии'), 'article needs a method/book related block');
    assert.ok(related.includes('related-type">Глава<'), 'OEE article must link the money chapter');
    assert.ok(html.indexOf('related-block') < html.indexOf('class="cta-band"'), 'related block must precede the CTA');
  } finally {
    runBuild();
  }
});
