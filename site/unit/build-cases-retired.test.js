'use strict';

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
    stdio: ['ignore', 'pipe', 'pipe']
  });
}

function readData(name) {
  return JSON.parse(fs.readFileSync(path.join(SITE_DIR, 'src', 'data', name), 'utf-8'));
}

function walkHtml(dir, acc) {
  fs.readdirSync(dir, { withFileTypes: true }).forEach(function(entry) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walkHtml(full, acc);
    else if (entry.name.endsWith('.html')) acc.push(full);
  });
  return acc;
}

// Cases were retired on 2026-11-06 (plan 1793969494727). The data stays for a
// possible restore, but no page, nav or sitemap entry may reference /cases/.
test('cases are retired from output, sitemap and links', function() {
  runBuild();

  assert.ok(!fs.existsSync(path.join(DIST, 'cases')), '/cases/ output must not exist');

  const sitemap = fs.readFileSync(path.join(DIST, 'sitemap.xml'), 'utf-8');
  assert.ok(!sitemap.includes('/cases/'), 'sitemap must not list /cases/');

  const pages = walkHtml(DIST, []);
  assert.ok(pages.length > 0, 'build produced pages');
  pages.forEach(function(file) {
    const html = fs.readFileSync(file, 'utf-8');
    assert.ok(!/href="[^"]*\/cases\//.test(html), 'legacy /cases/ href in ' + path.relative(DIST, file));
  });
});

test('cases data and chapter case fields are preserved', function() {
  const cases = readData('cases.json');
  assert.ok(Array.isArray(cases));
  assert.ok(cases.length > 0, 'cases.json must be preserved');

  const chapters = readData('chapters.json');
  assert.ok(chapters.some(function(c) { return Array.isArray(c.cases) && c.cases.length > 0; }),
    'chapter case references must be preserved');
});
