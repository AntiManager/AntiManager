'use strict';

// Genome section regression: build must emit /genome/ (model + free PLAN sample
// + six doc cards) and /genome/role/ (full КУ + recruiter profile) as indexable
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

    const landing = readDist('genome', 'index.html');

    // Structure of the accepted prototype.
    assert.ok(landing.includes('class="hero-gen"'), 'landing must render the hero');
    ['PLAN-01', 'PLAN-02', 'PLAN-03'].forEach(function(code) {
      assert.ok(landing.includes(code), code + ' free sample must be present');
    });
    assert.strictEqual((landing.match(/class="doc-card"/g) || []).length, 6, 'landing must show six document cards');
    assert.strictEqual((landing.match(/class="doc-full"/g) || []).length, 4, 'cards 01–04 carry the full doc inline');

    // Cards 05/06 link to the role page anchors.
    assert.ok(landing.includes('/genome/role/#ku'), 'КУ card must link to the role page #ku');
    assert.ok(landing.includes('/genome/role/#profile'), 'profile card must link to the role page #profile');

    // CTA targets resolved (no dead "#" links).
    assert.ok(landing.includes('/contact/?pack=process'), 'offer CTAs must open the feedback form');
    assert.ok(landing.includes('href="/contact/"'), 'the request CTA must point to /contact/');
    assert.ok(landing.includes('href="/headquarters/"'), 'the question CTA must point to /headquarters/');
    assert.ok(!landing.includes('href="#"'), 'no dead "#" links may remain');

    // No prototype-only chrome or leftover tokens.
    assert.ok(!landing.includes('proto-banner'), 'prototype banner must be dropped');
    assert.ok(!landing.includes('nav-pending'), 'prototype nav marker must be dropped');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(landing), 'no template tokens may remain in the landing');
    assert.ok(/<meta name="robots" content="index, follow/.test(landing), 'the landing must be indexable');

    const role = readDist('genome', 'role', 'index.html');
    assert.ok(role.includes('id="ku"'), 'role page needs the #ku anchor');
    assert.ok(role.includes('id="profile"'), 'role page needs the #profile anchor');
    assert.ok(role.includes('class="doc-doc"'), 'role page must render the converted documents');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(role), 'no template tokens may remain in the role page');
    assert.ok(/<meta name="robots" content="index, follow/.test(role), 'the role page must be indexable');

    // Discovery + routing.
    assert.ok(readDist('index.html').includes('href="/genome/"'), 'header nav must link to /genome/');
    assert.ok(readDist('index.html').includes('class="footer-nav"'), 'footer nav must be present');
    var sitemap = readDist('sitemap.xml');
    assert.ok(sitemap.includes('https://antimanager.pro/genome/'), 'sitemap must list /genome/');
    assert.ok(sitemap.includes('https://antimanager.pro/genome/role/'), 'sitemap must list /genome/role/');
    assert.ok(landing.includes('"BreadcrumbList"'), 'genome landing needs a breadcrumb');
  } finally {
    runBuild(); // restore dist/ from default settings for later tests/serving
  }
});
