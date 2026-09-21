'use strict';

// Build integration regression test: a payload placed in data fields must come
// out escaped, and a traversal slug must fail the build instead of escaping the
// output directory. Uses the WEAPONS_FILE seam so tracked data is never mutated.

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

function writeFixture(name, data) {
  const file = path.join(os.tmpdir(), name + '-' + process.pid + '.json');
  fs.writeFileSync(file, JSON.stringify(data), 'utf-8');
  return file;
}

test('build escapes payload fields and rejects a traversal slug', function() {
  const payload = '<img src=x onerror="window.__xss=1">';
  const fixture = writeFixture('antimanager-weapons', [{
    id: '99',
    title: payload,
    subtitle: payload,
    slug: 'fixture-weapon',
    zone: 'crisis"',
    thinker: null,
    tags: [],
    status: 'published',
  }]);
  const badSlug = writeFixture('antimanager-bad-slug', [{
    id: '99', title: 'x', slug: '../../evil', status: 'draft',
  }]);

  try {
    runBuild({ WEAPONS_FILE: fixture });

    const page = fs.readFileSync(path.join(DIST, 'weapons', 'fixture-weapon', 'index.html'), 'utf-8');
    assert.ok(
      page.includes('&lt;img src=x onerror=&quot;window.__xss=1&quot;&gt;'),
      'payload text must be HTML-escaped in the output'
    );
    assert.ok(!page.includes('<img src=x onerror='), 'raw payload must not appear in the output');
    assert.ok(page.includes('badge-zone-crisis&quot;'), 'zone value must be escaped inside the class attribute');

    assert.throws(function() { runBuild({ WEAPONS_FILE: badSlug }); }, /Invalid weapons\.json slug/);
    assert.ok(!fs.existsSync(path.join(DIST, '..', 'evil')), 'traversal slug must not create files outside dist');
  } finally {
    fs.unlinkSync(fixture);
    fs.unlinkSync(badSlug);
    runBuild(); // restore dist/ from the real data so later tests/serving see a clean build
  }
});
