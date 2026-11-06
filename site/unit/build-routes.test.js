'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const { routes, legacyRoutes, outFile, RESERVED_SLUGS } = require('../src/routes');
const { rewriteLegacyUrl, rewriteLegacyHrefs, assertNoLegacyHrefs } = require('../src/lib/legacy-routes');
const { buildCatalog } = require('../src/lib/catalog');

const SITE_DIR = path.join(__dirname, '..');
const DIST = path.join(SITE_DIR, 'dist');

function readData(name) {
  return JSON.parse(fs.readFileSync(path.join(SITE_DIR, 'src', 'data', name), 'utf-8'));
}

function runBuild() {
  return execFileSync(process.execPath, ['build.js'], {
    cwd: SITE_DIR,
    env: Object.assign({}, process.env, { BUILD_DATE: '2026-01-02' }),
    encoding: 'utf-8',
    stdio: ['ignore', 'pipe', 'pipe']
  });
}

test('route registry covers the target IA', function() {
  assert.strictEqual(routes.home(), '/');
  assert.strictEqual(routes.book(), '/playbook/');
  assert.strictEqual(routes.chapter('antikrizis'), '/playbook/antikrizis/');
  assert.strictEqual(routes.chapterFull('antikrizis'), '/playbook/antikrizis/full/');
  assert.strictEqual(routes.start(), '/start/');
  assert.strictEqual(routes.method(), '/method/');
  assert.strictEqual(routes.audit(), '/method/audit/');
  assert.strictEqual(routes.systems(), '/method/systems/');
  assert.strictEqual(routes.documents(), '/method/documents/');
  assert.strictEqual(routes.document('gemba-obhod'), '/method/documents/gemba-obhod/');
  assert.strictEqual(routes.role(), '/method/role/');
  assert.strictEqual(routes.about(), '/about/');
  assert.strictEqual(routes.manifesto(), '/about/manifesto/');
  assert.strictEqual(routes.origins(), '/about/origins/');
  assert.strictEqual(routes.search(), '/search/');
  assert.strictEqual(outFile('/playbook/antikrizis/'), 'playbook/antikrizis/index.html');
  assert.strictEqual(outFile('/'), 'index.html');
  ['start', 'search', 'full', 'book', 'playbook'].forEach(function(slug) { assert.ok(RESERVED_SLUGS.has(slug)); });
});

test('legacy map rewrites old paths and keeps /strategy/ alone', function() {
  assert.strictEqual(rewriteLegacyUrl('/arsenal/'), '/playbook/');
  assert.strictEqual(rewriteLegacyUrl('/arsenal'), '/playbook/');
  assert.strictEqual(rewriteLegacyUrl('/weapons/antikrizis/'), '/playbook/antikrizis/');
  assert.strictEqual(rewriteLegacyUrl('/weapons/antikrizis/full/'), '/playbook/antikrizis/full/');
  assert.strictEqual(rewriteLegacyUrl('/book/'), '/playbook/');
  assert.strictEqual(rewriteLegacyUrl('/book/antikrizis/'), '/playbook/antikrizis/');
  assert.strictEqual(rewriteLegacyUrl('/book/antikrizis/full/'), '/playbook/antikrizis/full/');
  assert.strictEqual(rewriteLegacyUrl('/genome/documents/gemba-obhod/'), '/method/documents/gemba-obhod/');
  assert.strictEqual(rewriteLegacyUrl('/cases/'), '/');
  assert.strictEqual(rewriteLegacyUrl('/strategy/foo/'), '/strategy/foo/');
  assert.strictEqual(rewriteLegacyUrl('https://antimanager.pro/genome/'), 'https://antimanager.pro/method/');
  assert.strictEqual(rewriteLegacyUrl('/weapons/antikrizis/?ref=x#top'), '/playbook/antikrizis/?ref=x#top');
  assert.strictEqual(rewriteLegacyHrefs('<a href="/scenarios/">x</a>'), '<a href="/start/">x</a>');
  assert.strictEqual(rewriteLegacyUrl('/about/headquarters/'), '/contact/');
  assert.strictEqual(rewriteLegacyUrl('/headquarters/'), '/contact/');
  assert.strictEqual(rewriteLegacyHrefs('<a href="/about/headquarters/">x</a>'), '<a href="/contact/">x</a>');
  assert.throws(function() { assertNoLegacyHrefs('<a href="/weapons/haos/">x</a>', 'test'); }, /Legacy href/);
  assert.throws(function() { assertNoLegacyHrefs('<a href="/book/haos/">x</a>', 'test'); }, /Legacy href/);
  assert.doesNotThrow(function() { assertNoLegacyHrefs('<a href="/strategy/x/">x</a>', 'test'); });
  assert.doesNotThrow(function() { assertNoLegacyHrefs('<a href="/playbook/haos/">x</a>', 'test'); });
});

test('catalog joins chapters and chapters.json carries no stale status', function() {
  const weapons = readData('weapons.json');
  const chapters = readData('chapters.json');
  const articles = readData('articles.json').filter(function(a) { return a.status === 'published'; });
  const documents = readData('documents.json');
  const catalog = buildCatalog({ weapons: weapons, chapters: chapters, articles: articles, documents: documents });

  assert.strictEqual(catalog.chapters.length, 23);
  assert.strictEqual(catalog.articles.length, 14);
  assert.strictEqual(catalog.documents.length, 4);
  assert.ok(catalog.chapters.some(function(e) { return e.slug === 'kommunikacionnyy-konstruktor'; }));
  chapters.forEach(function(c) {
    assert.ok(!Object.prototype.hasOwnProperty.call(c, 'status'), 'chapters.json status must be dropped: ' + c.slug);
  });
  assert.deepStrictEqual(catalog.situationCounts, { crisis: 4, team: 3, changes: 8, system: 8 });

  const scenarioIds = readData('scenarios.json').reduce(function(acc, s) { return acc.concat(s.weapons); }, []);
  assert.strictEqual(new Set(scenarioIds).size, 23);
  weapons.forEach(function(w) { assert.ok(scenarioIds.indexOf(w.id) !== -1, 'chapter in no situation: ' + w.id); });
});

test('redirects.conf covers every legacy route and stays single-hop', function() {
  const conf = fs.readFileSync(path.join(SITE_DIR, 'deploy', 'redirects.conf'), 'utf-8');
  const lines = conf.split('\n').filter(function(l) { return l.indexOf('rewrite ') === 0; });
  assert.strictEqual(lines.length, legacyRoutes.length, 'every legacy route needs exactly one rewrite');
  legacyRoutes.forEach(function(r) {
    assert.ok(conf.indexOf('rewrite ' + r.source + ' ' + r.target + ' permanent;') !== -1,
      'missing rewrite for ' + r.source);
  });
  assert.ok(conf.indexOf('/strategy') === -1, '/strategy stays in nginx.conf');
});

test('build emits the new routes and no legacy href', function() {
  runBuild();

  assert.ok(fs.existsSync(path.join(DIST, 'playbook', 'antikrizis', 'index.html')));
  assert.ok(fs.existsSync(path.join(DIST, 'playbook', 'antikrizis', 'full', 'index.html')));
  assert.ok(fs.existsSync(path.join(DIST, 'method', 'audit', 'index.html')));
  assert.ok(fs.existsSync(path.join(DIST, 'method', 'role', 'index.html')));
  assert.ok(fs.existsSync(path.join(DIST, 'method', 'documents', 'gemba-obhod', 'index.html')));
  assert.ok(fs.existsSync(path.join(DIST, 'about', 'manifesto', 'index.html')));
  assert.ok(fs.existsSync(path.join(DIST, 'about', 'origins', 'index.html')));
  assert.ok(!fs.existsSync(path.join(DIST, 'about', 'headquarters', 'index.html')), 'retired HQ page must be gone');
  assert.ok(fs.existsSync(path.join(DIST, 'start', 'index.html')));
  assert.ok(!fs.existsSync(path.join(DIST, 'weapons')), 'old /weapons/ output must be gone');
  assert.ok(!fs.existsSync(path.join(DIST, 'genome')), 'old /genome/ output must be gone');
  assert.ok(!fs.existsSync(path.join(DIST, 'arsenal')), 'old /arsenal/ output must be gone');
  assert.ok(!fs.existsSync(path.join(DIST, 'cases')), 'retired /cases/ output must be gone');

  const sitemap = fs.readFileSync(path.join(DIST, 'sitemap.xml'), 'utf-8');
  assert.ok(sitemap.includes('https://antimanager.pro/playbook/antikrizis/'));
  assert.ok(sitemap.includes('https://antimanager.pro/method/documents/gemba-obhod/'));
  assert.ok(!sitemap.includes('/weapons/'));
  assert.ok(!sitemap.includes('/genome/'));
  assert.ok(!sitemap.includes('/arsenal/'));
  assert.ok(!sitemap.includes('/cases/'));

  const home = fs.readFileSync(path.join(DIST, 'index.html'), 'utf-8');
  assert.ok(home.includes('aria-current="page"') === false, 'home is not a nav section');
  assert.ok(home.includes('href="/playbook/"'));
  assert.ok(!home.includes('href="/cases/"'));

  const chapter = fs.readFileSync(path.join(DIST, 'playbook', 'antikrizis', 'index.html'), 'utf-8');
  assert.ok(chapter.includes('data-nav="book" aria-current="page"'));
  assert.ok(chapter.includes('<link rel="canonical" href="https://antimanager.pro/playbook/antikrizis/">'));
});
