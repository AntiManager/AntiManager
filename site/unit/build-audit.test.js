'use strict';

// PS express audit regression: /genome/audit/ must ship the generated 40
// criteria, the fillable workbook, the request CTA and the discovery links,
// with no empty generation markers and no vault-only references.

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

test('audit page ships the generated checklist and the workbook', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });

    const html = readDist('genome', 'audit', 'index.html');

    assert.ok(html.includes('<h1>') && html.includes('Экспресс-аудит'), 'page must render its hero');

    // Generation markers must be filled in, never left empty.
    assert.ok(!/<!--AUDIT:[A-Z]+:START-->\s*<!--AUDIT:[A-Z]+:END-->/.test(html), 'no empty marker regions');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(html), 'no template tokens may remain');

    // 40 criteria in 6 blocks, each with six level rows.
    assert.strictEqual((html.match(/class="audit-criterion"/g) || []).length, 40, 'exactly 40 criteria');
    assert.strictEqual((html.match(/class="audit-block"/g) || []).length, 6, 'exactly 6 blocks');
    assert.strictEqual((html.match(/class="audit-chips"/g) || []).length, 1, 'one block jump-nav');
    for (let i = 1; i <= 40; i++) {
      const id = 'C' + String(i).padStart(2, '0');
      assert.ok(html.includes('id="c' + id.slice(1) + '"'), id + ' must be present');
    }
    const criteria = html.split('<details class="audit-criterion"').slice(1);
    criteria.forEach(function(part, index) {
      assert.strictEqual((part.match(/<td class="audit-level">/g) || []).length, 6,
        'criterion ' + (index + 1) + ' must show levels 0-5');
    });
    assert.strictEqual((html.match(/<tr class="is-target">/g) || []).length, 40, 'level 3 is marked on every criterion');

    // Authored reliability rule and the request offer.
    assert.ok(html.includes('Интервью — не выше 2'), 'reliability rule callout must be present');
    assert.ok((html.match(/120 критериев/g) || []).length >= 2, 'hero note and CTA must name 120 criteria');
    assert.ok((html.match(/по запросу/g) || []).length >= 2, 'hero note and CTA must say «по запросу»');
    assert.ok(html.includes('href="/contact/?pack=audit"'), 'CTA must open the audit pack');
    assert.ok(html.includes('href="/headquarters/"'), 'secondary CTA must point to the headquarters');

    // Download: real file, versioned href, honest filename.
    assert.ok(html.includes('/materials/ps-express-audit/express-audit-ps.xlsx?v=3.0'), 'download href must carry ?v=');
    assert.ok(html.includes('download="Экспресс-чек-лист-аудита-ПС-v3.0.xlsx"'), 'download must name the file');
    const xlsx = fs.statSync(path.join(DIST, 'materials', 'ps-express-audit', 'express-audit-ps.xlsx'));
    assert.ok(xlsx.size > 10240, 'workbook must ship non-empty');

    // Routing, SEO and discovery.
    assert.ok(html.includes('<link rel="canonical" href="https://antimanager.pro/genome/audit/">'), 'canonical must be set');
    assert.ok(html.includes('"BreadcrumbList"'), 'page needs breadcrumb structured data');
    assert.ok(html.includes('https://antimanager.pro/genome/audit/'), 'breadcrumb item must point at the page');
    assert.ok(/<meta name="robots" content="index, follow/.test(html), 'the page must be indexable');
    assert.ok(readDist('sitemap.xml').includes('https://antimanager.pro/genome/audit/'), 'sitemap must list the page');
    assert.ok(readDist('genome', 'index.html').includes('href="/genome/audit/"'), 'genome landing must link the page');
    assert.ok(readDist('index.html').includes('href="/genome/audit/"'), 'footer must link the page');

    // Vault-only references must never leak.
    assert.ok(!html.includes('[['), 'no wiki links may leak');
    assert.ok(!/href="[^"]*\.md/.test(html), 'no .md hrefs may leak');
  } finally {
    runBuild(); // restore dist/ for later tests/serving
  }
});
