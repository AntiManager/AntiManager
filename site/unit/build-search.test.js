'use strict';

// Search-engine plumbing regression: verification meta tags (env-gated), the
// IndexNow key file, and the absence of a verification placeholder.

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

test('verification codes are emitted only when provided', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02', YANDEX_VERIFICATION: '', GOOGLE_VERIFICATION: '' });
    const plain = readDist('index.html');
    assert.ok(!/yandex-verification/.test(plain), 'no Yandex meta without a code');
    assert.ok(!/google-site-verification/.test(plain), 'no Google meta without a code');
    assert.ok(!/XXXXX/.test(plain), 'the placeholder must never reach production');

    runBuild({
      BUILD_DATE: '2026-01-02',
      YANDEX_VERIFICATION: 'abc12345',
      GOOGLE_VERIFICATION: 'gcode-xyz_123',
    });
    const verified = readDist('index.html');
    assert.ok(verified.includes('<meta name="yandex-verification" content="abc12345">'),
      'Yandex meta must carry the env code');
    assert.ok(verified.includes('<meta name="google-site-verification" content="gcode-xyz_123">'),
      'Google meta must carry the env code');
    assert.ok(fs.existsSync(path.join(DIST, 'yandex_abc12345.html')),
      'the Yandex HTML-file method must still ship');
  } finally {
    runBuild();
  }
});

test('IndexNow key file ships at the site root', function() {
  const key = fs.readFileSync(path.join(SITE_DIR, 'src', 'indexnow-key.txt'), 'utf-8').trim();
  assert.match(key, /^[a-f0-9]{32}$/, 'key must be 32 lowercase hex characters');
  assert.strictEqual(readDist(key + '.txt'), key, 'dist must expose /<key>.txt with the key');
});

test('IndexNow dry run reads every sitemap URL', function() {
  const output = execFileSync(process.execPath, ['scripts/indexnow.js', '--dry-run'], {
    cwd: SITE_DIR,
    encoding: 'utf-8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  const sitemap = readDist('sitemap.xml');
  const count = (sitemap.match(/<loc>/g) || []).length;
  assert.ok(count > 0, 'sitemap must have URLs');
  assert.ok(output.includes(String(count) + ' URLs'), 'dry run must report the sitemap URL count');
});

test('arsenal description derives its count from weapons.json', function() {
  const weapons = require('../src/data/weapons.json');
  const html = readDist('arsenal', 'index.html');
  assert.ok(html.includes('Арсенал Антименеджера: ' + weapons.length + ' '),
    'the arsenal description must count the real weapons list');
  assert.ok(!/\d+ \d+ инструмент/.test(html), 'the count must not be duplicated');
});
