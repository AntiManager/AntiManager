'use strict';

// Home is a six-section book landing (plan 5.x): hero positioning, one
// situation chooser, six featured chapters, three featured articles, three
// methodology tools and a project/archive block. The old manifesto wall, the
// duplicate map/situation sections and the cases block must not come back.

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const SITE_DIR = path.join(__dirname, '..');

function runBuild() {
  return execFileSync(process.execPath, ['build.js'], {
    cwd: SITE_DIR,
    env: Object.assign({}, process.env, { BUILD_DATE: '2026-01-02' }),
    encoding: 'utf-8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
}

function mainHtml() {
  const html = fs.readFileSync(path.join(SITE_DIR, 'dist', 'index.html'), 'utf-8');
  return (html.match(/<main[\s\S]*<\/main>/) || [''])[0];
}

function count(html, pattern) {
  return (html.match(pattern) || []).length;
}

function region(html, start) {
  const i = html.indexOf(start);
  const j = html.indexOf('</section>', i + 1);
  return i === -1 || j === -1 ? '' : html.slice(i, j);
}

test('home is a six-section book landing without duplicated blocks', function() {
  try {
    runBuild();
    const main = mainHtml();

    assert.strictEqual(count(main, /<section\b/g), 6, 'home must have six sections');
    assert.ok(main.includes('ПЛЕЙБУК: КАК НА САМОМ ДЕЛЕ РАБОТАЕТ ЗАВОД'), 'hero states what the site is');
    assert.ok(main.includes('class="hero-lead"'), 'hero carries the audience/subline');
    assert.ok(main.includes('href="/start/"'), 'primary CTA opens /start/');
    assert.ok(main.includes('href="/playbook/"'), 'secondary CTA opens /playbook/');
    assert.ok(main.includes('href="/method/audit/"'), 'tertiary CTA opens the audit');
    assert.ok(main.includes('Ты пришёл за таблеткой? Её нет.'), 'manifesto challenge stays below the fold');

    assert.strictEqual(count(main, /class="zone-grid"/g), 1, 'one situation chooser');
    assert.strictEqual(count(main, /class="map-container/g), 1, 'the star map is a secondary visual');
    assert.strictEqual(count(region(main, 'id="weapons-section"'), /class="weapon-card"/g), 6, 'six featured chapters');
    assert.strictEqual(count(region(main, 'home-articles'), /class="article-card"/g), 3, 'three featured articles');
    assert.strictEqual(count(region(main, 'home-method-tools'), /class="method-tool"/g), 3, 'three methodology tools');
    assert.strictEqual(count(region(main, 'home-project-links'), /class="method-tool"/g), 3, 'three project links');

    assert.ok(!main.includes('manifesto-teaser'), 'manifesto wall must not ship on home');
    assert.ok(!main.includes('hq-section'), 'HQ block must not ship on home');
    assert.strictEqual(count(main, /id="system-map"/g), 1, 'the star map stays on home once');
    assert.strictEqual(count(main, /<section[^>]*id="system-map"/g), 0, 'the map is a secondary visual, not its own section');
    assert.ok(!main.includes('/cases/'), 'cases stay retired');
  } finally {
    runBuild();
  }
});

test('home surfaces the free lead magnet and the analytics module', function() {
  try {
    runBuild();
    const html = fs.readFileSync(path.join(SITE_DIR, 'dist', 'index.html'), 'utf-8');
    assert.ok(html.includes('class="lead-magnet"'), 'home must surface the free lead magnet');
    assert.ok(html.includes('express-audit-ps.xlsx'), 'lead magnet must link the free XLSX');
    assert.ok(html.includes('data-cta="lead_magnet_plan"'), 'lead magnet must link the PLAN sample');
    assert.ok(html.includes('data-cta="hero_start"'), 'hero CTAs must carry goal hooks');
    assert.ok(html.includes('/js/analytics.js?v='), 'the Metrika goals module must load');
  } finally {
    runBuild();
  }
});

test('home section headings stay in document order', function() {
  try {
    runBuild();
    const main = mainHtml();
    const levels = (main.match(/<h([1-6])\b/g) || []).map(function(tag) {
      return Number(tag.slice(2));
    });
    assert.strictEqual(levels[0], 1, 'home starts with an h1');
    assert.strictEqual(levels.filter(function(l) { return l === 1; }).length, 1, 'one h1 per page');
    let maxSeen = 1;
    levels.forEach(function(level) {
      assert.ok(level <= maxSeen + 1, 'heading order skips from h' + maxSeen + ' to h' + level);
      if (level > maxSeen) maxSeen = level;
    });
  } finally {
    runBuild();
  }
});
