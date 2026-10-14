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

    [['slozhnye-sistemy', '02'], ['sistemnaya-dinamika', '03'], ['upravlenie-eksperiment', '04'], ['kaskadirovanie-celey', '05'], ['processy', '06'], ['dengi-v-dvizhenii', '07'], ['nervnaya-sistema', '08'], ['bey-begi-zamri', '09'], ['situacionnoe-razvitie', '10'], ['kulturnyy-kod', '11'], ['anti-time-management', '12'], ['neizbezhnoe-ispolnenie', '13'], ['zhivaya-sistema', '14'], ['zhivoy-zavod', '15'], ['haos', '16'], ['lestnitsa-oshibok', '17'], ['antikrizis', '18'], ['cifrovoy-dvoynik', '19'], ['vyuchennaya-bespomoshchnost', '20'], ['dva-tipa-upravleniya', '21'], ['udarit-po-traektorii', '22'], ['kommunikacionnyy-konstruktor', '23']].forEach(function(pair) {
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

test('article 07 ships eight monsters and the inline loss map; ch.06 canonises eight', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });

    const full = readDist('weapons', 'dengi-v-dvizhenii', 'full', 'index.html');
    assert.ok(full.includes('class="loss-map"'), '07 full page must embed the loss map');
    assert.ok(full.includes('role="img"'), 'loss map must expose an accessible role');
    assert.ok(full.includes('aria-labelledby="lossmap-title"'), 'loss map must reference its accessible title');
    assert.ok(full.includes('id="lossmap-title"'), 'loss map must ship a <title>');
    assert.ok(full.includes('8. Монстр Нереализованный потенциал'), '07 must list the eighth monster');
    assert.ok(full.includes('Взаимосвязь монстров'), '07 must ship the interconnection section');
    assert.ok(!full.includes('Семь пожирател'), '07 must no longer say "Семь пожирателей"');
    assert.ok(!full.includes('неиспользованный потенциал сотрудников'), 'old 8th-waste wording must be gone from 07');

    const lite = readDist('weapons', 'dengi-v-dvizhenii', 'index.html');
    assert.ok(lite.includes('Восемь пожирателей прибыли'), '07 landing heading must read "Восемь"');
    assert.ok(lite.includes('Нереализованный потенциал'), '07 landing table must include the eighth monster');

    const p = readDist('weapons', 'processy', 'full', 'index.html');
    assert.ok(p.includes('Классические 7 видов «муда» плюс добавленный позже восьмой'), 'ch.06 must frame the eight as 7 classic + 1 later');
    assert.ok(p.includes('<li>Нереализованный потенциал сотрудников</li>'), 'ch.06 must list the 8th waste item');
    assert.ok(!p.includes('А я добавлю девятый'), 'ch.06 must not offer a ninth waste');
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
