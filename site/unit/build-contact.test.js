'use strict';

// Contact page regression: build must emit an indexable /contact/ page carrying
// the feedback form (posting same-origin to /api/feedback), link it from the
// footer, list it in the sitemap, and ship the rewritten privacy page.
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

test('contact page ships the feedback form and is reachable', function () {
  try {
    runBuild({ BUILD_DATE: '2026-01-02' });

    const contact = readDist('contact', 'index.html');
    assert.ok(contact.includes('id="feedbackForm"'), 'contact page needs the form');
    assert.ok(contact.includes('action="/api/feedback"'), 'form must post to /api/feedback');
    ['cf-name', 'cf-contact', 'cf-message', 'cf-consent', 'cf-website', 'cf-pack'].forEach(function(id) {
      assert.ok(contact.includes('id="' + id + '"'), 'field #' + id + ' missing');
    });
    assert.ok(contact.includes('name="website"'), 'honeypot field must be present');
    assert.ok(contact.includes('/js/contact.js'), 'contact.js must be loaded');
    assert.ok(contact.includes('href="/privacy/"'), 'consent must link to /privacy/');
    assert.ok(/<meta name="robots" content="index, follow/.test(contact), 'contact page must be indexable');
    assert.ok(!/\{\{[a-z_]+\}\}/.test(contact), 'no template tokens may remain');

    // Discovery.
    assert.ok(readDist('sitemap.xml').includes('https://antimanager.pro/contact/'), 'sitemap must list /contact/');
    assert.ok(readDist('index.html').includes('href="/contact/"'), 'footer must link to /contact/');

    // Privacy rewritten: no longer denies collecting personal data.
    const privacy = readDist('privacy', 'index.html');
    assert.ok(privacy.includes('форм'), 'privacy must describe the feedback form');
    assert.ok(!privacy.includes('Мы не собираем персональные данные пользователей'), 'old privacy claim must be gone');
  } finally {
    runBuild(); // restore dist/ from default settings for later tests/serving
  }
});
