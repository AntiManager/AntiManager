'use strict';

const routes = require('../routes');

const situationLabels = { crisis: 'Кризис', team: 'Команда', changes: 'Изменения', system: 'Система' };
const roleLabels = { director: 'Директор', 'shop-floor': 'Цех', hr: 'HR' };
const typeLabels = { chapter: 'Глава', article: 'Статья', document: 'Документ' };

function indexBySlug(list, label) {
  var map = new Map();
  (list || []).forEach(function(item) {
    if (!item || typeof item.slug !== 'string') throw new Error(label + ': missing slug');
    if (map.has(item.slug)) throw new Error(label + ': duplicate slug ' + item.slug);
    map.set(item.slug, item);
  });
  return map;
}

function unionTags(a, b) {
  var out = [];
  (a || []).concat(b || []).forEach(function(tag) {
    if (tag && out.indexOf(tag) === -1) out.push(tag);
  });
  return out;
}

function byChapterId(a, b) {
  return Number(a.id) - Number(b.id);
}

function buildCatalog(input) {
  var weapons = input.weapons || [];
  var chapters = input.chapters || [];
  var articles = input.articles || [];
  var documents = input.documents || [];

  if (weapons.length !== chapters.length) {
    throw new Error('Catalog: weapons/chapters count mismatch (' + weapons.length + ' vs ' + chapters.length + ')');
  }

  var weaponsBySlug = indexBySlug(weapons, 'weapons.json');
  var chaptersBySlug = indexBySlug(chapters, 'chapters.json');

  chapters.forEach(function(c) {
    if (!weaponsBySlug.has(c.slug)) throw new Error('Catalog: chapter has no weapon: ' + c.slug);
  });

  var chapterEntries = weapons.map(function(w) {
    var c = chaptersBySlug.get(w.slug);
    if (!c) throw new Error('Catalog: weapon has no chapter metadata: ' + w.slug);
    if (c.id !== w.id) throw new Error('Catalog: id drift for ' + w.slug + ' (' + w.id + ' vs ' + c.id + ')');
    if (c.title !== w.title) throw new Error('Catalog: title drift for ' + w.slug);
    if ((c.subtitle || '') !== (w.subtitle || '')) throw new Error('Catalog: subtitle drift for ' + w.slug);
    if (w.zone && !situationLabels[w.zone]) throw new Error('Catalog: unknown situation ' + w.zone + ' for ' + w.slug);
    return {
      type: 'chapter',
      id: w.id,
      slug: w.slug,
      title: w.title,
      subtitle: w.subtitle || '',
      url: routes.routes.chapter(w.slug),
      situation: w.zone || null,
      topic: c.ray || null,
      roles: Array.isArray(c.roles) ? c.roles.slice() : [],
      tags: unionTags(w.tags, c.tags),
      date: w.date || null
    };
  }).sort(byChapterId);

  var articleEntries = articles.map(function(a) {
    return {
      type: 'article',
      id: a.id,
      slug: a.slug,
      title: a.title || '',
      subtitle: a.subtitle || '',
      url: routes.routes.article(a.topic, a.slug),
      situation: null,
      topic: a.topic || null,
      roles: [],
      tags: Array.isArray(a.tags) ? a.tags.slice() : [],
      date: a.date || null
    };
  }).sort(function(a, b) { return Number(a.id) - Number(b.id); });

  var documentEntries = documents.map(function(d) {
    return {
      type: 'document',
      id: d.slug,
      slug: d.slug,
      title: d.title || '',
      subtitle: d.subtitle || '',
      url: routes.routes.document(d.slug),
      situation: null,
      topic: null,
      roles: [],
      tags: [],
      date: d.updated || null
    };
  }).sort(function(a, b) { return a.slug.localeCompare(b.slug); });

  var entries = chapterEntries.concat(articleEntries, documentEntries);
  var byUrl = new Map();
  entries.forEach(function(e) {
    if (byUrl.has(e.url)) throw new Error('Catalog: duplicate url ' + e.url);
    byUrl.set(e.url, e);
  });

  var situationCounts = {};
  Object.keys(situationLabels).forEach(function(k) { situationCounts[k] = 0; });
  chapterEntries.forEach(function(e) {
    if (e.situation) situationCounts[e.situation] += 1;
  });

  return {
    entries: entries,
    chapters: chapterEntries,
    articles: articleEntries,
    documents: documentEntries,
    byUrl: byUrl,
    situationCounts: situationCounts
  };
}

module.exports = {
  buildCatalog: buildCatalog,
  situationLabels: situationLabels,
  roleLabels: roleLabels,
  typeLabels: typeLabels
};
