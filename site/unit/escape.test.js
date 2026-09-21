'use strict';

// Build-time escaping regression tests (F: build.js escaping had no automated
// guard). Run with `npm run test:unit` (`node --test unit`).

const test = require('node:test');
const assert = require('node:assert');
const { escapeHtml, sanitize, assertSlug } = require('../src/lib/escape');

test('escapeHtml neutralises markup-significant characters', function() {
  assert.strictEqual(
    escapeHtml('<img src=x onerror="window.__xss=1">'),
    '&lt;img src=x onerror=&quot;window.__xss=1&quot;&gt;'
  );
  assert.strictEqual(escapeHtml("a & b 'c'"), 'a &amp; b &#39;c&#39;');
  assert.strictEqual(escapeHtml('</script>'), '&lt;/script&gt;');
  assert.strictEqual(escapeHtml(''), '');
  assert.strictEqual(escapeHtml(undefined), '');
});

test('sanitize escapes only the listed string fields', function() {
  var out = sanitize([{ id: 'x', slug: 'a-b', title: '<b>t</b>', subtitle: null }], ['title', 'subtitle']);
  assert.strictEqual(out[0].title, '&lt;b&gt;t&lt;/b&gt;');
  assert.strictEqual(out[0].slug, 'a-b'); // slug is not in the key list: stays raw for lookups
  assert.strictEqual(out[0].id, 'x');
  assert.strictEqual(out[0].subtitle, null);
});

test('assertSlug rejects traversal and markup, accepts real slugs', function() {
  var bad = ['../etc/passwd', 'a/b', 'a.b', 'a b', '<x>', 'a"b', '', null, undefined];
  for (var i = 0; i < bad.length; i++) {
    assert.throws(function() { assertSlug(bad[i], 'slug'); }, /Invalid slug/);
  }
  assert.strictEqual(assertSlug('upravlenie-eksperiment', 'slug'), 'upravlenie-eksperiment');
  assert.strictEqual(assertSlug('00', 'id'), '00');
});
