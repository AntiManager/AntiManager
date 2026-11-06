'use strict';

// Genome section regression: build must emit /method/ (model + free PLAN sample
// + six doc cards) and /method/role/ (full КУ + recruiter profile) as indexable
// static pages, with no prototype chrome and no leftover template tokens.
// Uses the BUILD_DATE seam so the output is deterministic.

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

test('genome pages ship, are indexable, and carry no prototype chrome', function() {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });

    const landing = readDist('method', 'index.html');

    // Structure of the accepted prototype.
    assert.ok(landing.includes('class="hero-gen'), 'landing must render the hero');
    assert.ok(landing.includes('<h1>Методология'), 'hero H1 must name the methodology, not the metaphor');
    assert.ok(landing.includes('Модель «Геном завода»'), 'the «Геном завода» model name must stay visible');
    assert.ok(landing.indexOf('id="offer"') < landing.indexOf('id="problem"'), 'the offer must precede the long explanation');
    assert.ok(landing.indexOf('href="#offer"') < landing.indexOf('href="#problem"'), 'TOC order must match the page order');
    assert.ok(landing.includes('class="method-tools"'), 'the four tool entry points must sit in the hero');
    ['/method/audit/', '/method/systems/', '/method/documents/', '/method/role/'].forEach(function(href) {
      assert.ok(landing.includes('class="method-tool" href="' + href + '"'), 'tool card must link to ' + href);
    });
    assert.ok(landing.includes('class="method-toc"'), 'the hub needs a sticky section TOC');
    ['#problem', '#model', '#compare', '#chain', '#sample', '#documents', '#offer'].forEach(function(anchor) {
      assert.ok(landing.includes('href="' + anchor + '"'), 'TOC must link to ' + anchor);
    });
    assert.ok(landing.includes('<nav class="breadcrumbs"'), 'the hub needs visible breadcrumbs');
    ['PLAN-01', 'PLAN-02', 'PLAN-03'].forEach(function(code) {
      assert.ok(landing.includes(code), code + ' free sample must be present');
    });
    assert.strictEqual((landing.match(/class="doc-card"/g) || []).length, 6, 'landing must show six document cards');
    assert.strictEqual((landing.match(/class="doc-full"/g) || []).length, 4, 'cards 01–04 carry the full doc inline');

    // Cards 05/06 link to the role page anchors.
    assert.ok(landing.includes('/method/role/#ku'), 'КУ card must link to the role page #ku');
    assert.ok(landing.includes('/method/role/#profile'), 'profile card must link to the role page #profile');

    // CTA targets resolved (no dead "#" links).
    assert.ok(landing.includes('/contact/?pack=process'), 'offer CTAs must open the feedback form');
    assert.ok(landing.includes('href="/contact/"'), 'the request CTA must point to /contact/');
    assert.ok(landing.includes('href="/contact/"'), 'the question CTA must point to /contact/');
    assert.ok(!landing.includes('href="#"'), 'no dead "#" links may remain');

    // No prototype-only chrome or leftover tokens.
    assert.ok(!landing.includes('proto-banner'), 'prototype banner must be dropped');
    assert.ok(!landing.includes('nav-pending'), 'prototype nav marker must be dropped');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(landing), 'no template tokens may remain in the landing');
    assert.ok(/<meta name="robots" content="index, follow/.test(landing), 'the landing must be indexable');

    const role = readDist('method', 'role', 'index.html');
    assert.ok(role.includes('id="ku"'), 'role page needs the #ku anchor');
    assert.ok(role.includes('id="profile"'), 'role page needs the #profile anchor');
    assert.ok(role.includes('class="role-toc"'), 'role page needs a sticky document TOC');
    assert.ok(role.includes('class="reading-progress"'), 'role page needs a reading-progress bar');
    assert.ok(role.includes('<nav class="breadcrumbs"'), 'role page needs visible breadcrumbs');
    assert.ok(role.includes('class="doc-doc"'), 'role page must render the converted documents');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(role), 'no template tokens may remain in the role page');
    assert.ok(/<meta name="robots" content="index, follow/.test(role), 'the role page must be indexable');

    // Discovery + routing.
    assert.ok(readDist('index.html').includes('href="/method/"'), 'header nav must link to /method/');
    assert.ok(readDist('index.html').includes('class="footer-nav"'), 'footer nav must be present');
    var sitemap = readDist('sitemap.xml');
    assert.ok(sitemap.includes('https://antimanager.pro/method/'), 'sitemap must list /method/');
    assert.ok(sitemap.includes('https://antimanager.pro/method/role/'), 'sitemap must list /method/role/');
    assert.ok(landing.includes('"BreadcrumbList"'), 'genome landing needs a breadcrumb');
  } finally {
    runBuild(); // restore dist/ from default settings for later tests/serving
  }
});
