'use strict';

// Escaping helpers shared by build.js and the build-time regression tests.
// Kept dependency-free so `node --test` can load this module in isolation.

function escapeHtml(s) {
  return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function sanitize(list, keys) {
  return list.map(function(obj) {
    var out = Object.assign({}, obj);
    keys.forEach(function(k) { if (typeof out[k] === 'string') out[k] = escapeHtml(out[k]); });
    return out;
  });
}

// A slug/id ends up in an output filesystem path and in HTML attributes, so
// reject anything that could traverse directories or break out of markup.
function assertSlug(value, label) {
  if (typeof value !== 'string' || !/^[a-z0-9][a-z0-9-]*$/.test(value)) {
    throw new Error('Invalid ' + (label || 'slug') + ': ' + JSON.stringify(value));
  }
  return value;
}

module.exports = { escapeHtml: escapeHtml, sanitize: sanitize, assertSlug: assertSlug };
