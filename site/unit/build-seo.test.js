'use strict';

// SEO regression test: build output must carry fresh dates, a raster OG image,
// enriched article metadata, breadcrumbs on static pages, four featured weapons,
// related links for zone-less articles, and a corrected landing description.
// Runs the real build with a fixed BUILD_DATE so assertions are deterministic.

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
function distPath() {
  return path.join.apply(path, [DIST].concat(Array.prototype.slice.call(arguments)));
}

test('build emits SEO metadata', function() {
  const BUILD_DATE = '2026-01-02';
  try {
    runBuild({ BUILD_DATE: BUILD_DATE, YANDEX_VERIFICATION: '' });

    // 1. Dynamic build date in sitemap and JSON-LD / OG.
    const sitemap = readDist('sitemap.xml');
    assert.ok(sitemap.includes('<lastmod>' + BUILD_DATE + '</lastmod>'), 'sitemap lastmod must use BUILD_DATE');

    const weapon = readDist('playbook', 'sistemnaya-dinamika', 'index.html');
    assert.ok(weapon.includes('"dateModified": "' + BUILD_DATE + '"'), 'weapon dateModified must use BUILD_DATE');
    assert.ok(weapon.includes('<meta property="article:modified_time" content="' + BUILD_DATE + '">'), 'article:modified_time must be present');

    // 2. Zone-less weapon keeps an internal related block.
    assert.ok(weapon.includes('В том же окопе'), 'zone-less weapon must keep related links');

    // 3. article:tag count matches the weapon tags count.
    const weapons = JSON.parse(fs.readFileSync(path.join(SITE_DIR, 'src', 'data', 'weapons.json'), 'utf-8'));
    const w02 = weapons.find(function(w) { return w.slug === 'slozhnye-sistemy'; });
    const page02 = readDist('playbook', 'slozhnye-sistemy', 'index.html');
    const tagCount = (page02.match(/property="article:tag"/g) || []).length;
    assert.strictEqual(tagCount, w02.tags.length, 'article:tag metas must match weapon tags');

    // 4. Static page has a breadcrumb.
    assert.ok(readDist('playbook', 'index.html').includes('"BreadcrumbList"'), 'static pages need BreadcrumbList');

    // 5. Landing: six featured weapons; corrected meta description.
    const index = readDist('index.html');
    const sectionHtml = index.slice(index.indexOf('id="weapons-section"')).split('</section>')[0];
    const featured = (sectionHtml.match(/class="weapon-card"/g) || []).length;
    assert.strictEqual(featured, 6, 'landing must feature six weapons');
    assert.ok(index.includes('14 long-reads'), 'meta description must state the long-read count');
    assert.ok(index.includes('23 главы'), 'meta description must use the correct plural');
    assert.ok(!index.includes('Интерактивная карта'), 'the old card-map positioning must be gone');
    assert.ok(!index.includes('5 контуров'), 'stale "5 контуров" must be gone');

    // 6. Fabricated landing stats are gone (SEO Phase 2).
    assert.ok(!index.includes('stats-section'), 'stats-section must be removed');
    assert.ok(!index.includes('2 847'), 'fabricated "2 847" stat must be gone');
    assert.ok(!index.includes('>113<'), 'fabricated "113" stat must be gone');
    assert.ok(!index.includes('>47<'), 'fabricated "47" stat must be gone');

    // 7. All weapons published; no review badges/status on cards (SEO Phase 2).
    const arsenal = readDist('playbook', 'index.html');
    assert.ok(arsenal.includes('Все 23 главы с полным текстом.'), 'arsenal must state the full-text coverage');
    assert.ok(!arsenal.includes('badge-status-review'), 'no review badge on arsenal');

    // 8. Raster OG image is produced and referenced.
    assert.ok(fs.existsSync(distPath('og-image.png')), 'dist/og-image.png must exist');
    assert.ok(index.includes('content="https://antimanager.pro/og-image.png"'), 'og:image must point to the PNG');

    // 9. Full page carries a description distinct from its landing (no duplicate snippets).
    const landing02 = readDist('playbook', 'slozhnye-sistemy', 'index.html');
    const full02 = readDist('playbook', 'slozhnye-sistemy', 'full', 'index.html');
    const descOf = function(html) { return (html.match(/<meta name="description" content="([^"]*)"/) || [])[1]; };
    assert.ok(descOf(landing02), 'landing must have a description');
    assert.notStrictEqual(descOf(full02), descOf(landing02), 'full-page description must differ from the landing');

    // 10. Enriched JSON-LD: stable @id graph + organization logo.
    assert.ok(landing02.includes('"@id": "https://antimanager.pro/#organization"'), 'organization @id must be emitted');
    assert.ok(landing02.includes('"@id": "https://antimanager.pro/#website"'), 'website @id must be emitted');
    assert.ok(landing02.includes('"logo"'), 'organization logo must be emitted');

    // 11. Social-card alt text.
    assert.ok(index.includes('<meta property="og:image:alt"'), 'og:image:alt must be present');
    assert.ok(index.includes('<meta name="twitter:image:alt"'), 'twitter:image:alt must be present');

    // 12. datePublished uses the article's real date (weapons.json), dateModified the build date.
    assert.ok(landing02.includes('"datePublished": "2026-09-21"'), 'datePublished must use the article date');
    assert.ok(landing02.includes('"dateModified": "' + BUILD_DATE + '"'), 'dateModified must use the build date');

    // 13. The XXXX Yandex verification placeholder must never ship.
    assert.ok(!fs.existsSync(distPath('yandex_XXXXXXXXXXXXXXXX.html')), 'placeholder yandex verification file must not ship');

    // 14. Footer exposes about / about/manifesto / about/origins / privacy
    assert.ok(index.includes('class="footer-nav"'), 'footer nav must be present');
    assert.ok(index.includes('href="/about/"'), 'about must be linked from the footer');
    assert.ok(index.includes('href="/about/origins/"'), 'origins must be linked from the footer');
    assert.ok(index.includes('href="/privacy/"'), 'privacy must be linked from the footer');
  } finally {
    runBuild(); // restore dist/ from default settings for later tests/serving
  }
});
