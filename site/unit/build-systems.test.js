'use strict';

// Systems map regression: /genome/systems/ is generated offline from the vault
// cards (14 systems × 12 fields) and must ship filled, indexable and discoverable.

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

test('systems map ships 14 templated cards and is discoverable', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });

    const page = readDist('genome', 'systems', 'index.html');
    assert.strictEqual((page.match(/class="doc-card sys-card"/g) || []).length, 14,
      'one card per system');
    assert.strictEqual((page.match(/class="sys-artifacts"/g) || []).length, 14,
      'every card renders its P1 artifact list');
    assert.strictEqual((page.match(/Открыть карточку · 12 полей/g) || []).length, 14,
      'every card carries the 12-field template');
    assert.ok(page.includes('href="#s01"'), 'summary table links to the first card');
    assert.ok(page.includes('<link rel="canonical" href="https://antimanager.pro/genome/systems/">'),
      'canonical must be set');
    assert.ok(!/<!--SYSTEMS:[A-Z]+:START-->\s*<!--SYSTEMS:[A-Z]+:END-->/.test(page),
      'generated regions must not be empty');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(page), 'no template tokens may remain');
    assert.ok(/<meta name="robots" content="index, follow/.test(page), 'page must be indexable');
    assert.ok(page.includes('"BreadcrumbList"'), 'page needs a breadcrumb');

    const landing = readDist('genome', 'index.html');
    assert.ok(landing.includes('href="/genome/systems/"'), 'genome landing must link to the map');
    assert.strictEqual((landing.match(/class="doc-card"/g) || []).length, 6,
      'the six role document cards must stay unchanged');

    assert.ok(readDist('sitemap.xml').includes('https://antimanager.pro/genome/systems/'),
      'sitemap must list the map');

    const tpl = path.join(DIST, 'materials', 'ps-systems-map', 'system-card-template.docx');
    assert.ok(fs.statSync(tpl).size > 5000, 'template DOCX must ship in materials');
  } finally {
    runBuild(); // restore dist/ from default settings for later tests/serving
  }
});
