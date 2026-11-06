'use strict';

const { SITE_URL, legacyRoutes } = require('../routes');

function splitSuffix(url) {
  var hash = '';
  var query = '';
  var cut = url.length;
  var h = url.indexOf('#');
  if (h !== -1) { hash = url.slice(h); cut = h; }
  var q = url.indexOf('?');
  if (q !== -1 && q < cut) { query = url.slice(q, cut); cut = q; }
  return { path: url.slice(0, cut), suffix: query + hash };
}

function rewriteLegacyUrl(url) {
  if (!url) return url;
  var isAbsolute = url === SITE_URL || url.indexOf(SITE_URL + '/') === 0;
  if (!isAbsolute && url[0] !== '/') return url;
  var local = isAbsolute ? (url.slice(SITE_URL.length) || '/') : url;
  var parts = splitSuffix(local);
  for (var i = 0; i < legacyRoutes.length; i++) {
    var m = parts.path.match(legacyRoutes[i].re);
    if (m) return (isAbsolute ? SITE_URL : '') + legacyRoutes[i].to(m) + parts.suffix;
  }
  return url;
}

function rewriteLegacyHrefs(html) {
  return String(html || '').replace(/href="([^"]*)"/g, function(all, url) {
    return 'href="' + rewriteLegacyUrl(url) + '"';
  });
}

function assertNoLegacyHrefs(html, page) {
  var re = /href="([^"]*)"/g;
  var m;
  while ((m = re.exec(String(html || ''))) !== null) {
    var url = m[1];
    var isAbsolute = url === SITE_URL || url.indexOf(SITE_URL + '/') === 0;
    if (!isAbsolute && url[0] !== '/') continue;
    var local = isAbsolute ? (url.slice(SITE_URL.length) || '/') : url;
    var path = splitSuffix(local).path;
    for (var i = 0; i < legacyRoutes.length; i++) {
      if (legacyRoutes[i].re.test(path)) {
        throw new Error('Legacy href on ' + page + ': ' + url);
      }
    }
  }
}

module.exports = {
  rewriteLegacyUrl: rewriteLegacyUrl,
  rewriteLegacyHrefs: rewriteLegacyHrefs,
  assertNoLegacyHrefs: assertNoLegacyHrefs
};
