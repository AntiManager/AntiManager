'use strict';

// /about/ is a real page, not a stub: it must answer what the project is, who
// it is for and how to use the site (>300 words of verifiable copy), and every
// /about/* subpage must carry visible breadcrumbs back to it. The author block
// is deliberately absent until the user supplies verifiable copy (plan 9.1).

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

function mainText(html) {
  const main = (html.match(/<main[\s\S]*<\/main>/) || [''])[0];
  return main.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

test('/about/ answers what, who and how, and subpages carry breadcrumbs', function() {
  try {
    runBuild();

    const about = readDist('about', 'index.html');
    assert.ok(about.includes('<nav class="breadcrumbs"'), 'about page needs visible breadcrumbs');
    assert.ok(about.includes('href="/start/"'), 'about page must link to /start/');
    assert.ok(about.includes('href="/playbook/"'), 'about page must link to /playbook/');
    assert.ok(about.includes('href="/method/audit/"'), 'about page must link to the audit tool');
    assert.ok(about.includes('href="/about/manifesto/"'), 'about page must link to the manifesto');
    assert.ok(about.includes('href="/about/origins/"'), 'about page must link to the archive');
    assert.ok(about.includes('href="/contact/"'), 'about page must offer a working contact route');
    assert.ok(about.includes('Как мы работаем'), 'about page must explain the working process');
    assert.ok(about.includes('href="/method/#offer"'), 'about process must link the offer');

    const words = mainText(about).split(' ').filter(Boolean).length;
    assert.ok(words > 300, '/about/ must ship more than 300 words of copy, got ' + words);

    var subpages = ['manifesto', 'origins'];
    subpages.forEach(function(slug) {
      var html = readDist('about', slug, 'index.html');
      assert.ok(html.includes('<nav class="breadcrumbs"'), '/about/' + slug + '/ needs visible breadcrumbs');
      assert.ok(html.includes('href="/about/"'), '/about/' + slug + '/ must link back to /about/');
      assert.ok(/<meta name="robots" content="index, follow/.test(html), '/about/' + slug + '/ must be indexable');
      assert.ok(html.includes('"BreadcrumbList"'), '/about/' + slug + '/ needs BreadcrumbList JSON-LD');
    });

    // Footer points at all four about pages.
    const home = readDist('index.html');
    ['/about/', '/about/manifesto/', '/about/origins/'].forEach(function(href) {
      assert.ok(home.includes('href="' + href + '"'), 'footer must link to ' + href);
    });
  } finally {
    runBuild(); // restore dist/ from default settings for later tests/serving
  }
});
