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
    zone: 'crisis',
    thinker: null,
    tags: [],
    status: 'published',
  }]);
  const chaptersFixture = writeFixture('antimanager-chapters', [{
    id: '99', part: 0, title: payload, slug: 'fixture-weapon', subtitle: payload,
    ray: 'strategy', roles: [], tools: [], cases: [], tags: [],
  }]);
  const scenariosFixture = writeFixture('antimanager-scenarios', [{
    id: 'crisis', title: 'КРИЗИС', subtitle: 'test', icon: 'fire', weapons: ['99'],
    symptoms: ['test symptom'],
    steps: [
      { text: 'step one', chapter: 'fixture-weapon' },
      { text: 'step two', chapter: 'fixture-weapon' },
      { text: 'step three', chapter: 'fixture-weapon' },
    ],
    document: 'a3-reshenie-problem',
    article: 'optimizaciya-razvitie-antikrizis',
  }]);
  const badSlug = writeFixture('antimanager-bad-slug', [{
    id: '99', title: 'x', slug: '../../evil', status: 'draft',
  }]);

  try {
    runBuild({ WEAPONS_FILE: fixture, CHAPTERS_FILE: chaptersFixture, SCENARIOS_FILE: scenariosFixture });

    const page = fs.readFileSync(path.join(DIST, 'playbook', 'fixture-weapon', 'index.html'), 'utf-8');
    assert.ok(
      page.includes('&lt;img src=x onerror=&quot;window.__xss=1&quot;&gt;'),
      'payload text must be HTML-escaped in the output'
    );
    assert.ok(!page.includes('<img src=x onerror='), 'raw payload must not appear in the output');
    assert.ok(page.includes('badge-zone-crisis'), 'zone value must drive the badge class');

    assert.throws(function() { runBuild({ WEAPONS_FILE: badSlug }); }, /Invalid weapons\.json slug/);
    assert.ok(!fs.existsSync(path.join(DIST, '..', 'evil')), 'traversal slug must not create files outside dist');
  } finally {
    fs.unlinkSync(fixture);
    fs.unlinkSync(chaptersFixture);
    fs.unlinkSync(scenariosFixture);
    fs.unlinkSync(badSlug);
    runBuild(); // restore dist/ from the real data so later tests/serving see a clean build
  }
});
