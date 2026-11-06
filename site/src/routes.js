'use strict';

const SITE_URL = 'https://antimanager.pro';

const routes = {
  home: function() { return '/'; },
  book: function() { return '/playbook/'; },
  chapter: function(slug) { return '/playbook/' + slug + '/'; },
  chapterFull: function(slug) { return '/playbook/' + slug + '/full/'; },
  start: function() { return '/start/'; },
  articles: function() { return '/articles/'; },
  articleTopic: function(topic) { return '/articles/' + topic + '/'; },
  article: function(topic, slug) { return '/articles/' + topic + '/' + slug + '/'; },
  method: function() { return '/method/'; },
  audit: function() { return '/method/audit/'; },
  systems: function() { return '/method/systems/'; },
  documents: function() { return '/method/documents/'; },
  document: function(slug) { return '/method/documents/' + slug + '/'; },
  role: function() { return '/method/role/'; },
  about: function() { return '/about/'; },
  manifesto: function() { return '/about/manifesto/'; },
  origins: function() { return '/about/origins/'; },
  contact: function() { return '/contact/'; },
  privacy: function() { return '/privacy/'; },
  search: function() { return '/search/'; },
  notFound: function() { return '/404/'; }
};

const RESERVED_SLUGS = new Set(['start', 'search', 'full', 'book', 'playbook', 'method', 'about', 'articles', 'contact', 'privacy']);

function absolute(pathname) {
  return SITE_URL + pathname;
}

function outFile(pathname) {
  var p = String(pathname || '/').replace(/^\/+/, '').replace(/\/+$/, '');
  return p ? p + '/index.html' : 'index.html';
}

function assertNotReservedSlug(slug, label) {
  if (RESERVED_SLUGS.has(slug)) {
    throw new Error('Reserved ' + (label || 'slug') + ': ' + slug);
  }
  return slug;
}

// Old -> new. Ordered longest-first so /weapons/<slug>/full/ matches before
// /weapons/<slug>/. /strategy/** is deliberately absent: nginx keeps that
// redirect, so the build must not rewrite or duplicate it.
// `re` (build rewrite/assert) is strict kebab-case; `source` (nginx) is looser
// on purpose: an unexpected legacy slug must still 301 into the new namespace
// (and then 404 normally) instead of falling through to the trailing-slash rule.
var legacyRoutes = [
  { re: /^\/book\/([a-z0-9][a-z0-9-]*)\/full\/?$/, source: '^/book/([^/]+)/full/?$', target: '/playbook/$1/full/', to: function(m) { return routes.chapterFull(m[1]); } },
  { re: /^\/book\/([a-z0-9][a-z0-9-]*)\/?$/, source: '^/book/([^/]+)/?$', target: '/playbook/$1/', to: function(m) { return routes.chapter(m[1]); } },
  { re: /^\/book\/?$/, source: '^/book/?$', target: '/playbook/', to: function() { return routes.book(); } },
  { re: /^\/weapons\/([a-z0-9][a-z0-9-]*)\/full\/?$/, source: '^/weapons/([^/]+)/full/?$', target: '/playbook/$1/full/', to: function(m) { return routes.chapterFull(m[1]); } },
  { re: /^\/weapons\/([a-z0-9][a-z0-9-]*)\/?$/, source: '^/weapons/([^/]+)/?$', target: '/playbook/$1/', to: function(m) { return routes.chapter(m[1]); } },
  { re: /^\/genome\/documents\/([a-z0-9][a-z0-9-]*)\/?$/, source: '^/genome/documents/([^/]+)/?$', target: '/method/documents/$1/', to: function(m) { return routes.document(m[1]); } },
  { re: /^\/genome\/audit\/?$/, source: '^/genome/audit/?$', target: '/method/audit/', to: function() { return routes.audit(); } },
  { re: /^\/genome\/systems\/?$/, source: '^/genome/systems/?$', target: '/method/systems/', to: function() { return routes.systems(); } },
  { re: /^\/genome\/documents\/?$/, source: '^/genome/documents/?$', target: '/method/documents/', to: function() { return routes.documents(); } },
  { re: /^\/genome\/role\/?$/, source: '^/genome/role/?$', target: '/method/role/', to: function() { return routes.role(); } },
  { re: /^\/genome\/?$/, source: '^/genome/?$', target: '/method/', to: function() { return routes.method(); } },
  { re: /^\/arsenal\/?$/, source: '^/arsenal/?$', target: '/playbook/', to: function() { return routes.book(); } },
  { re: /^\/scenarios\/?$/, source: '^/scenarios/?$', target: '/start/', to: function() { return routes.start(); } },
  { re: /^\/manifesto\/?$/, source: '^/manifesto/?$', target: '/about/manifesto/', to: function() { return routes.manifesto(); } },
  { re: /^\/archive\/?$/, source: '^/archive/?$', target: '/about/origins/', to: function() { return routes.origins(); } },
  { re: /^\/about\/headquarters\/?$/, source: '^/about/headquarters/?$', target: '/contact/', to: function() { return routes.contact(); } },
  { re: /^\/headquarters\/?$/, source: '^/headquarters/?$', target: '/contact/', to: function() { return routes.contact(); } },
  { re: /^\/cases(?:\/.*)?\/?$/, source: '^/cases(/.*)?$', target: '/', to: function() { return routes.home(); } }
];

module.exports = {
  SITE_URL: SITE_URL,
  routes: routes,
  absolute: absolute,
  outFile: outFile,
  RESERVED_SLUGS: RESERVED_SLUGS,
  assertNotReservedSlug: assertNotReservedSlug,
  legacyRoutes: legacyRoutes
};
