'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const SITE_DIR = path.join(__dirname, '..');
const DIST = path.join(SITE_DIR, 'dist');

function readData(name) {
  return JSON.parse(fs.readFileSync(path.join(SITE_DIR, 'src', 'data', name), 'utf-8'));
}

function readDist() {
  return fs.readFileSync(path.join(DIST, 'start', 'index.html'), 'utf-8');
}

function runBuild() {
  return execFileSync(process.execPath, ['build.js'], {
    cwd: SITE_DIR,
    env: Object.assign({}, process.env, { BUILD_DATE: '2026-01-02' }),
    encoding: 'utf-8',
    stdio: ['ignore', 'pipe', 'pipe']
  });
}

test('scenarios carry curated start content with real links', function() {
  const scenarios = readData('scenarios.json');
  const weapons = readData('weapons.json');
  const articles = readData('articles.json').filter(function(a) { return a.status === 'published'; });
  const documents = readData('documents.json');

  assert.deepStrictEqual(scenarios.map(function(s) { return s.id; }), ['crisis', 'team', 'changes', 'system']);

  const covered = new Set();
  scenarios.forEach(function(s) {
    assert.strictEqual(s.steps.length, 3, s.id + ' must have exactly 3 steps');
    s.steps.forEach(function(step) {
      const weapon = weapons.find(function(w) { return w.slug === step.chapter; });
      assert.ok(weapon, s.id + ': step chapter not found ' + step.chapter);
      assert.strictEqual(weapon.zone, s.id, s.id + ': step chapter in another situation ' + step.chapter);
      assert.ok(s.weapons.indexOf(weapon.id) !== -1, s.id + ': step chapter not in weapons list ' + step.chapter);
      assert.ok(step.text, s.id + ': step has no text');
    });
    assert.ok(Array.isArray(s.symptoms) && s.symptoms.length > 0, s.id + ': no symptoms');
    assert.ok(documents.some(function(d) { return d.slug === s.document; }), s.id + ': unknown document');
    assert.ok(articles.some(function(a) { return a.slug === s.article; }), s.id + ': unknown article');
    s.weapons.forEach(function(id) { covered.add(id); });
  });
  assert.strictEqual(covered.size, weapons.length, 'every chapter must appear in a situation');
});

test('build emits /start and /book with facets and card metadata', function() {
  runBuild();

  const start = readDist();
  ['crisis', 'team', 'changes', 'system'].forEach(function(id) {
    assert.ok(start.includes('id="' + id + '"'), 'missing situation anchor ' + id);
  });
  assert.strictEqual((start.match(/class="start-situation /g) || []).length, 4, 'four situation blocks');
  assert.strictEqual((start.match(/class="start-step-link"/g) || []).length, 12, 'three steps per situation');
  assert.strictEqual((start.match(/start-cta/g) || []).length, 4, 'one filtered-book CTA per situation');
  assert.strictEqual((start.match(/class="start-material"/g) || []).length, 8, 'one document and one article per situation');
  assert.ok(start.includes('href="/playbook/?situation=crisis"'), 'CTA must preserve the situation context');

  const startHrefs = Array.from(start.matchAll(/href="(\/(?:playbook|method\/documents|articles)\/[^"?]+)"/g)).map(function(m) { return m[1]; });
  assert.ok(startHrefs.length > 20, 'start links to chapters, documents and articles');
  startHrefs.forEach(function(href) {
    const target = path.join(DIST, href.replace(/^\//, ''), 'index.html');
    assert.ok(fs.existsSync(target), 'dead start link: ' + href);
  });

  const book = fs.readFileSync(path.join(DIST, 'playbook', 'index.html'), 'utf-8');
  assert.strictEqual((book.match(/class="weapon-card"/g) || []).length, 23, 'all chapters are listed');
  assert.strictEqual((book.match(/data-filter-type="situation"/g) || []).length, 5, 'all + 4 situations');
  assert.strictEqual((book.match(/data-filter-type="role"/g) || []).length, 4, 'all + 3 roles');
  assert.strictEqual((book.match(/class="weapon-readtime"/g) || []).length, 23, 'every card shows read time');
  assert.ok(book.includes('Все 23 главы с полным текстом.'), 'the hub states that every chapter has a full text');
  assert.ok(!book.includes('badge-full'), 'per-card full-text badges are removed');
  assert.ok(book.includes('data-filter="crisis" aria-pressed="false">КРИЗИС <span class="filter-count">4</span>'));
  assert.ok(book.includes('data-filter="director" aria-pressed="false">ДИРЕКТОР <span class="filter-count">21</span>'));
  assert.ok(book.includes('data-filter="shop-floor" aria-pressed="false">ЦЕХ <span class="filter-count">13</span>'));
  assert.ok(book.includes('data-filter="hr" aria-pressed="false">HR <span class="filter-count">7</span>'));

  const ids = Array.from(book.matchAll(/data-situation="([^"]+)"/g)).map(function(m) { return m[1]; });
  assert.strictEqual(ids.length, 23, 'every card carries its situation');
  const roles = Array.from(book.matchAll(/data-roles="([^"]*)"/g)).map(function(m) { return m[1]; });
  assert.strictEqual(roles.length, 23, 'every card carries its roles');
  roles.forEach(function(value) { assert.ok(value.length > 0, 'card roles must not be empty'); });
});
