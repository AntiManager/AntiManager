'use strict';

// Full-text page regression: the topic landing must link to /full/ instead of
// the old lite "Тезисный отрывок" excerpt, the full page must ship a TOC and a
// materials block, and materials.json must reject unsafe hrefs.
// Uses BUILD_DATE + MATERIALS_FILE seams so tracked data is deterministic/clean.

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
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

function writeFixture(name, data) {
  const file = path.join(os.tmpdir(), name + '-' + process.pid + '.json');
  fs.writeFileSync(file, JSON.stringify(data), 'utf-8');
  return file;
}

test('full-text page ships read-more path, TOC, materials and sitemap entry', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });

    const landing = readDist('weapons', 'mayatnik-upravleniya', 'index.html');
    assert.ok(landing.includes('class="read-more-card"'), 'landing must offer a read-more path');
    assert.ok(landing.includes('/weapons/mayatnik-upravleniya/full/'), 'read-more must link to the full text');
    assert.ok(!landing.includes('Тезисный отрывок'), 'the lite thesis excerpt must be gone');
    assert.ok(!landing.includes('download-section'), 'the fake download section must be gone');

    const full = readDist('weapons', 'mayatnik-upravleniya', 'full', 'index.html');
    assert.ok(full.includes('article-toc'), 'full page needs a table of contents');
    assert.ok(full.includes('materials-section'), 'full page needs a materials block');
    assert.ok(full.includes('"position": 4'), 'full page breadcrumb must be four levels deep');
    assert.ok(full.includes('/materials/mayatnik-upravleniya.pdf'), 'article PDF must be linked');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(full), 'no template tokens may remain in the full page');

    assert.ok(readDist('sitemap.xml').includes('/weapons/mayatnik-upravleniya/full/'), 'sitemap must list the full page');
  } finally {
    runBuild();
  }
});

test('rollout: migrated landings link to their full text pages', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });

    [['slozhnye-sistemy', '02'], ['sistemnaya-dinamika', '03'], ['upravlenie-eksperiment', '04']].forEach(function(pair) {
      const slug = pair[0];
      const label = pair[1];

      const landing = readDist('weapons', slug, 'index.html');
      assert.ok(landing.includes('class="read-more-card"'), label + ' landing must offer a read-more path');
      assert.ok(landing.includes('/weapons/' + slug + '/full/'), label + ' read-more must link to the full text');
      assert.ok(!landing.includes('Тезисный отрывок'), label + ' lite thesis excerpt must be gone');

      const full = readDist('weapons', slug, 'full', 'index.html');
      assert.ok(full.includes('article-toc'), label + ' full page needs a table of contents');
      assert.ok(full.includes('materials-section'), label + ' full page needs a materials block');
      assert.ok(full.includes('/materials/' + slug + '.pdf'), label + ' article PDF must be linked');
      assert.ok(!/\{\{[a-z_]+\}\}/.test(full), 'no template tokens may remain in the ' + label + ' full page');
    });
  } finally {
    runBuild();
  }
});

test('materials.json rejects unsafe hrefs and escapes titles', function() {
  const payload = '<img src=x onerror="window.__xss=1">';
  const good = writeFixture('antimanager-materials', [{
    slug: 'mayatnik-upravleniya',
    items: [{ kind: 'checklist', title: payload, href: '/materials/mayatnik-upravleniya/checklist.pdf', meta: 'PDF' }],
  }]);
  const jsHref = writeFixture('antimanager-materials-js', [
    { slug: 'mayatnik-upravleniya', items: [{ title: 'x', href: 'javascript:alert(1)' }] },
  ]);
  const traversal = writeFixture('antimanager-materials-traversal', [
    { slug: 'mayatnik-upravleniya', items: [{ title: 'x', href: '/materials/../evil.pdf' }] },
  ]);

  try {
    runBuild({ MATERIALS_FILE: good });
    const full = readDist('weapons', 'mayatnik-upravleniya', 'full', 'index.html');
    assert.ok(
      full.includes('&lt;img src=x onerror=&quot;window.__xss=1&quot;&gt;'),
      'material title must be HTML-escaped'
    );
    assert.ok(!full.includes('<img src=x onerror='), 'raw payload must not appear in the output');

    assert.throws(function() { runBuild({ MATERIALS_FILE: jsHref }); }, /Invalid materials\.json href/);
    assert.throws(function() { runBuild({ MATERIALS_FILE: traversal }); }, /Invalid materials\.json href/);
  } finally {
    fs.unlinkSync(good);
    fs.unlinkSync(jsHref);
    fs.unlinkSync(traversal);
    runBuild();
  }
});
