#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { escapeHtml, sanitize, assertSlug } = require('./src/lib/escape');
const SITE_URL = 'https://antimanager.pro';
// Real build date drives sitemap lastmod and JSON-LD dates; BUILD_DATE env is a
// test seam so output stays deterministic.
const BUILD_DATE = process.env.BUILD_DATE || new Date().toISOString().slice(0, 10);
const VERSION = '20260728b';
// Social platforms do not render SVG OG images; prefer the rasterized PNG and
// fall back to the SVG when it has not been generated yet.
const OG_IMAGE_PNG = path.join(__dirname, 'src', 'templates', 'og-image.png');
const OG_IMAGE_URL = fs.existsSync(OG_IMAGE_PNG) ? SITE_URL + '/og-image.png' : SITE_URL + '/og-image.svg';

function read(name) { return fs.readFileSync(path.isAbsolute(name) ? name : path.join(__dirname, name), 'utf-8'); }
function write(filepath, content) {
  const dir = path.dirname(path.join(__dirname, 'dist', filepath));
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(__dirname, 'dist', filepath), content, 'utf-8');
}
// Clean output so removed source files do not linger in dist/ (deploy copies dist/*).
const DIST_DIR = path.join(__dirname, 'dist');
if (fs.existsSync(DIST_DIR)) fs.rmSync(DIST_DIR, { recursive: true, force: true });

function copyDir(src, dst) {
  const s = path.join(__dirname, src);
  if (!fs.existsSync(s)) return;
  const entries = fs.readdirSync(s, { withFileTypes: true });
  for (const e of entries) {
    const sp = path.join(s, e.name);
    const dp = path.join(__dirname, 'dist', dst, e.name);
    if (e.isDirectory()) { copyDir(path.join(src, e.name), path.join(dst, e.name)); }
    else { if (!fs.existsSync(path.dirname(dp))) fs.mkdirSync(path.dirname(dp), { recursive: true }); fs.copyFileSync(sp, dp); }
  }
}

const base = read('src/templates/base.html');
const headerHtml = read('src/components/header.html');
const footerHtml = read('src/components/footer.html');

// Text fields are HTML-escaped at load time so authored data can never inject
// markup (defense in depth for a public repo). id/slug/zone/thinker stay raw:
// they are used for lookups and filesystem paths and must not be encoded.
const weapons = sanitize(JSON.parse(read(process.env.WEAPONS_FILE || 'src/data/weapons.json')), ['title', 'subtitle']);
const scenarios = sanitize(JSON.parse(read('src/data/scenarios.json')), ['title', 'subtitle', 'icon']);
const thinkers = sanitize(JSON.parse(read('src/data/thinkers.json')), ['name', 'years', 'idea', 'weapon', 'photo']);
const cases = sanitize(JSON.parse(read('src/data/cases.json')), ['title', 'desc', 'readtime']);

// slug/id become output paths and URL segments — fail the build on anything
// that could traverse directories or break out of markup.
weapons.forEach(function(w) { assertSlug(w.slug, 'weapons.json slug'); assertSlug(w.id, 'weapons.json id'); });

// Per-article downloadable materials. The article PDF itself is auto-detected
// from site/materials/<slug>.pdf; this file holds the extra hand-authored
// artifacts (checklists, templates). The href is restricted so authored data
// can never point outside /materials/ or smuggle a javascript: URL.
const materials = (function() {
  const raw = JSON.parse(read(process.env.MATERIALS_FILE || 'src/data/materials.json'));
  if (!Array.isArray(raw)) throw new Error('materials.json must be a JSON array');
  const bySlug = {};
  raw.forEach(function(entry) {
    assertSlug(entry.slug, 'materials.json slug');
    const items = Array.isArray(entry.items) ? entry.items : [];
    bySlug[entry.slug] = items.map(function(it) {
      const href = String(it.href || '');
      if (!/^\/materials\/[a-z0-9-]+\/[A-Za-z0-9._-]+$/.test(href)) {
        throw new Error('Invalid materials.json href: ' + JSON.stringify(it.href));
      }
      return {
        kind: escapeHtml(String(it.kind || 'file')),
        title: escapeHtml(String(it.title || '')),
        meta: escapeHtml(String(it.meta || '')),
        href: href,
      };
    });
  });
  return bySlug;
})();

const zoneLabels = { crisis: 'КРИЗИС', team: 'КОМАНДА', changes: 'ИЗМЕНЕНИЯ', system: 'СИСТЕМА' };
const statusLabels = { published: 'Опубликовано', review: 'На ревью', draft: 'Черновик' };

// Russian plural form: 1 → one, 2–4 → few, otherwise many (11–14 take many).
function plural(n, one, few, many) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return n + ' ' + one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return n + ' ' + few;
  return n + ' ' + many;
}

function weaponById(id) { return weapons.find(w => w.id === id); }

function zoneBadgeHtml(zone) {
  if (!zone) return '';
  return `<span class="badge badge-zone badge-zone-${escapeHtml(zone)}">${escapeHtml(zoneLabels[zone] || zone)}</span>`;
}

function statusBadgeHtml(status) {
  return `<span class="badge badge-status badge-status-${escapeHtml(status)}">${escapeHtml(statusLabels[status] || status)}</span>`;
}

// Plain-text word count → reading time estimate (~180 wpm), minimum 1 minute.
function readMinutes(html) {
  const text = String(html).replace(/<[^>]*>/g, ' ').replace(/&[a-z#0-9]+;/gi, ' ');
  const words = text.split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 180));
}

// Inject anchor ids into H2/H3 and return { html, toc } so the full-text page
// ships a static, no-JS table of contents.
function withToc(html) {
  const items = [];
  let n = 0;
  const out = String(html).replace(/<h([23])([^>]*)>([\s\S]*?)<\/h\1>/gi, function(m, level, attrs, inner) {
    const text = inner.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
    if (!text) return m;
    n++;
    const idMatch = (attrs || '').match(/\bid="([^"]+)"/);
    let id;
    if (idMatch) {
      id = idMatch[1];
    } else {
      id = 'sec-' + n;
      attrs = (attrs || '') + ' id="' + id + '"';
    }
    items.push({ level: level, id: id, text: text });
    return '<h' + level + attrs + '>' + inner + '</h' + level + '>';
  });
  if (items.length < 2) return { html: out, toc: '' };
  const toc = '<nav class="article-toc" aria-label="Содержание"><div class="article-toc-title">Содержание</div><ol>'
    + items.map(function(it) {
        return '<li class="toc-level-' + it.level + '"><a href="#' + it.id + '">' + it.text + '</a></li>';
      }).join('')
    + '</ol></nav>';
  return { html: out, toc: toc };
}

// Honest materials block: the article PDF is offered only when a real file
// exists; declared extras are listed after it. Never promises future files.
function materialsBlockHtml(w) {
  const extras = materials[w.slug] || [];
  const hasPdf = fs.existsSync(path.join(__dirname, 'materials', w.slug + '.pdf'));
  let items = '';
  if (hasPdf) {
    items += '<li class="material-item">'
      + '<span class="material-icon" aria-hidden="true">📄</span>'
      + '<span class="material-body"><span class="material-title">Статья «' + w.title + '»</span>'
      + '<span class="material-meta">PDF · полный текст</span></span>'
      + '<a class="btn btn-primary btn-sm" href="/materials/' + escapeHtml(w.slug) + '.pdf" download>Скачать</a></li>';
  }
  extras.forEach(function(it) {
    items += '<li class="material-item">'
      + '<span class="material-icon" aria-hidden="true">🧰</span>'
      + '<span class="material-body"><span class="material-title">' + it.title + '</span>'
      + '<span class="material-meta">' + (it.meta || it.kind) + '</span></span>'
      + '<a class="btn btn-ghost btn-sm" href="' + it.href + '" download>Скачать</a></li>';
  });
  const empty = (!hasPdf && !extras.length)
    ? '<p class="materials-empty">Печатные материалы к статье готовятся. Пока — сохраните страницу в PDF или придите за разбором в Штаб.</p>'
    : '';
  const printBtn = hasPdf
    ? ''
    : '<button type="button" class="btn btn-ghost btn-sm print-pdf-btn" onclick="window.print()">Сохранить в PDF</button>';
  return '<section class="materials-section" id="materials">'
    + '<h2>Материалы по теме</h2>'
    + '<p class="materials-desc">Статья целиком и рабочие артефакты — для скачивания и печати.</p>'
    + (items ? '<ul class="materials-list">' + items + '</ul>' : '')
    + empty
    + '<div class="materials-actions">' + printBtn
    + '<a class="btn btn-ghost btn-sm" href="https://t.me/antimanager">Новые материалы — в Штабе</a></div>'
    + '</section>';
}

function makeStructuredData(pageType, data) {
  data = data || {};
  function json(ld) {
    // Escape "<" so a value containing "</script>" cannot break out of the tag.
    return '\n<script type="application/ld+json">' + JSON.stringify(ld, null, 2).replace(/</g, '\\u003c') + '</script>';
  }
  if (pageType === 'landing') {
    return json({
      '@context': 'https://schema.org',
      '@graph': [
        { '@type': 'WebSite', 'name': 'AntiManager', 'url': SITE_URL, 'inLanguage': 'ru' },
        { '@type': 'Organization', 'name': 'AntiManager', 'url': SITE_URL, 'sameAs': ['https://t.me/antimanager'] }
      ]
    });
  }
  if (pageType === 'weapon') {
    var article = {
      '@type': 'Article',
      'headline': data.title,
      'description': data.subtitle || data.title,
      'url': data.canonicalUrl,
      'datePublished': BUILD_DATE,
      'dateModified': BUILD_DATE,
      'inLanguage': 'ru',
      'author': { '@type': 'Organization', 'name': 'AntiManager', 'url': SITE_URL },
      'publisher': { '@type': 'Organization', 'name': 'AntiManager', 'url': SITE_URL }
    };
    if (data.articleSection) article.articleSection = data.articleSection;
    return json({
      '@context': 'https://schema.org',
      '@graph': [
        article,
        {
          '@type': 'BreadcrumbList',
          'itemListElement': [
            { '@type': 'ListItem', 'position': 1, 'name': 'Главная', 'item': SITE_URL + '/' },
            { '@type': 'ListItem', 'position': 2, 'name': 'Арсенал', 'item': SITE_URL + '/arsenal/' },
            { '@type': 'ListItem', 'position': 3, 'name': data.title }
          ]
        }
      ]
    });
  }
  if (pageType === 'articleFull') {
    var fullArticle = {
      '@type': 'Article',
      'headline': data.title,
      'description': data.subtitle || data.title,
      'url': data.canonicalUrl,
      'datePublished': BUILD_DATE,
      'dateModified': BUILD_DATE,
      'inLanguage': 'ru',
      'author': { '@type': 'Organization', 'name': 'AntiManager', 'url': SITE_URL },
      'publisher': { '@type': 'Organization', 'name': 'AntiManager', 'url': SITE_URL }
    };
    if (data.articleSection) fullArticle.articleSection = data.articleSection;
    return json({
      '@context': 'https://schema.org',
      '@graph': [
        fullArticle,
        {
          '@type': 'BreadcrumbList',
          'itemListElement': [
            { '@type': 'ListItem', 'position': 1, 'name': 'Главная', 'item': SITE_URL + '/' },
            { '@type': 'ListItem', 'position': 2, 'name': 'Арсенал', 'item': SITE_URL + '/arsenal/' },
            { '@type': 'ListItem', 'position': 3, 'name': data.title, 'item': SITE_URL + '/weapons/' + data.slug + '/' },
            { '@type': 'ListItem', 'position': 4, 'name': 'Полный текст' }
          ]
        }
      ]
    });
  }
  if (pageType === 'static') {
    return json({
      '@context': 'https://schema.org',
      '@graph': [
        { '@type': 'WebSite', 'name': 'AntiManager', 'url': SITE_URL, 'inLanguage': 'ru' },
        {
          '@type': 'BreadcrumbList',
          'itemListElement': [
            { '@type': 'ListItem', 'position': 1, 'name': 'Главная', 'item': SITE_URL + '/' },
            { '@type': 'ListItem', 'position': 2, 'name': data.name || 'Раздел', 'item': data.url || SITE_URL + '/' }
          ]
        }
      ]
    });
  }
  return '';
}

// === RENDER ===

function renderPage(title, description, content, opts) {
  opts = opts || {};

  const desc = description || title;
  const canonicalUrl = opts.canonicalUrl || SITE_URL + '/';
  const ogType = opts.ogType || 'website';
  const ogImage = opts.ogImage || OG_IMAGE_URL;
  // Dimensions are only known for the built-in 1200×630 card; a caller-provided
  // override may differ, so do not claim its size.
  const ogImageMeta = opts.ogImage
    ? ''
    : '<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n';

  let headTags = ''
    + '<link rel="canonical" href="' + canonicalUrl + '">\n'
    + '<meta property="og:title" content="' + escapeHtml(title) + '">\n'
    + '<meta property="og:description" content="' + escapeHtml(desc) + '">\n'
    + '<meta property="og:url" content="' + canonicalUrl + '">\n'
    + '<meta property="og:type" content="' + ogType + '">\n'
    + '<meta property="og:image" content="' + ogImage + '">\n'
    + ogImageMeta
    + '<meta property="og:site_name" content="AntiManager">\n'
    + '<meta property="og:locale" content="ru_RU">\n'
    + '<meta name="twitter:card" content="summary_large_image">\n'
    + '<meta name="twitter:title" content="' + escapeHtml(title) + '">\n'
    + '<meta name="twitter:description" content="' + escapeHtml(desc) + '">\n'
    + '<meta name="twitter:image" content="' + ogImage + '">';

  if (opts.structuredData) headTags += opts.structuredData;

  if (ogType === 'article') {
    if (opts.ogArticleSection) headTags += '\n<meta property="article:section" content="' + escapeHtml(opts.ogArticleSection) + '">';
    headTags += '\n<meta property="article:published_time" content="' + BUILD_DATE + '">';
    headTags += '\n<meta property="article:modified_time" content="' + BUILD_DATE + '">';
    headTags += '\n<meta property="article:author" content="' + SITE_URL + '/about/">';
    if (opts.ogTags && opts.ogTags.length) {
      opts.ogTags.forEach(function(t) { headTags += '\n<meta property="article:tag" content="' + escapeHtml(t) + '">'; });
    }
  }

  if (opts.headExtra) headTags += '\n' + opts.headExtra;

  const scripts = '<script src="/js/brutalist.js?v=' + VERSION + '" defer></script>'
    + (opts.scripts ? '\n' + opts.scripts : '');

  let html = base;
  html = html.replace(/\{\{version\}\}/g, VERSION);
  html = html.replace('{{title}}', title);
  html = html.replace('{{description}}', description);
  html = html.replace('{{header}}', headerHtml);
  html = html.replace('{{content}}', content);
  html = html.replace('{{footer}}', footerHtml.replace('{{year}}', '2026'));
  html = html.replace('{{head_extra}}', headTags);
  html = html.replace('{{scripts}}', scripts);
  if (opts.noindex) html = html.replace('</head>', '<meta name="robots" content="noindex"></head>');
  return html;
}

// === STAR MAP (Story 08) ===

function starSvg() {
  const CX = 300, CY = 300, R = 220;
  const n = scenarios.length;
  const angleStep = 360 / n;
  let svg = '<svg viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Карта зон Антименеджера" style="width:100%;max-width:600px;height:auto;">';
  svg += '<circle cx="' + CX + '" cy="' + CY + '" r="250" fill="none" stroke="#DC2626" stroke-width="1" stroke-dasharray="8 8" opacity="0.3"/>';
  svg += '<circle cx="' + CX + '" cy="' + CY + '" r="240" fill="none" stroke="#DC2626" stroke-width="0.5" opacity="0.15"/>';
  svg += '<circle cx="' + CX + '" cy="' + CY + '" r="55" fill="none" stroke="#DC2626" stroke-width="0.5" stroke-dasharray="4 4" opacity="0.4"/>';
  svg += '<circle cx="' + CX + '" cy="' + CY + '" r="75" fill="none" stroke="#DC2626" stroke-width="0.5" stroke-dasharray="4 4" opacity="0.2"/>';
  scenarios.forEach(function(s, i) {
    var angle = (i * angleStep - 90) * Math.PI / 180;
    var ex = CX + R * Math.cos(angle);
    var ey = CY + R * Math.sin(angle);
    var labelR = R + 30;
    var lx = CX + labelR * Math.cos(angle);
    var ly = CY + labelR * Math.sin(angle);
    svg += '<line x1="' + CX + '" y1="' + CY + '" x2="' + ex + '" y2="' + ey + '" stroke="#DC2626" stroke-width="3" opacity="0.3" stroke-linecap="round"/>';
    var count = Math.min(s.weapons.filter(function(id) { return weaponById(id); }).length, 8);
    for (var j = 0; j < count; j++) {
      var t = (j + 1) / (count + 1);
      var dx = CX + (R * 0.85 * t) * Math.cos(angle);
      var dy = CY + (R * 0.85 * t) * Math.sin(angle);
      svg += '<circle cx="' + dx + '" cy="' + dy + '" r="3" fill="#DC2626" opacity="' + (0.4 + j * 0.1) + '"/>';
    }
    svg += '<text x="' + lx + '" y="' + ly + '" fill="#DC2626" font-family="\'Golos Text\',sans-serif" font-weight="900" font-size="12" text-anchor="middle" letter-spacing="1">' + s.title + '</text>';
    svg += '<circle cx="' + lx + '" cy="' + (ly + 18) + '" r="12" fill="#DC2626"/>';
    svg += '<text x="' + lx + '" y="' + (ly + 22) + '" fill="#fff" font-family="\'Golos Text\',sans-serif" font-weight="700" font-size="10" text-anchor="middle">' + count + '</text>';
  });
  svg += '<circle cx="' + CX + '" cy="' + CY + '" r="40" fill="#0A0A0A" stroke="#DC2626" stroke-width="3"/>';
  svg += '<text x="' + CX + '" y="' + (CY - 5) + '" fill="#fff" font-family="\'Golos Text\',sans-serif" font-weight="900" font-size="11" text-anchor="middle" letter-spacing="3">АНТИ</text>';
  svg += '<text x="' + CX + '" y="' + (CY + 12) + '" fill="#DC2626" font-family="\'Golos Text\',sans-serif" font-weight="900" font-size="11" text-anchor="middle" letter-spacing="2">МЕНЕДЖЕР</text>';
  svg += '</svg>';
  return svg;
}

// === CONTENT GENERATORS ===

// Feature published weapons first, then top up with review ones so the landing
// block always shows four cards.
const featuredWeapons = weapons
  .filter(function(w) { return w.status === 'published'; })
  .concat(weapons.filter(function(w) { return w.status === 'review'; }))
  .slice(0, 4);

const featuredWeaponsHtml = featuredWeapons.map(function(w) {
  return '<a href="/weapons/' + escapeHtml(w.slug) + '/" class="weapon-card">'
    + '<div class="weapon-title">' + w.title + '</div>'
    + '<div class="weapon-subtitle">' + (w.subtitle || '') + '</div>'
    + (w.zone ? '<span class="weapon-status">' + zoneLabels[w.zone] + '</span>' : '')
    + '</a>';
}).join('');

// Full manifesto. Content source of truth: vault article 01 (mirror: manifesto-ru.md).
// Kept as structured data so the landing teaser and the /manifesto page cannot drift apart.
const manifestoPreamble = 'Мы — инженеры человеческих управленческих систем, архитекторы порядка и гаранты справедливости. Мы больше не «менеджеры» в старом смысле этого слова. Наша задача — не контролировать людей, а проектировать и запускать социальные машины, которые раскрывают потенциал каждого для достижения общих целей. Мы обнаруживаем, что через осознанный подход к созданию среды мы достигаем лучших результатов. Осознавая историческую преемственность управленческой мысли, мы провозглашаем этот манифест.';

const manifestoValues = [
  { lead: 'Люди и их потенциал', tail: 'над слепым исполнением инструкций.', body: 'То есть мы ценим инициативу и интеллект выше, чем простое исполнение инструкций, хотя признаём, что дисциплина и послушание являются необходимым фундаментом для старта любого дела.' },
  { lead: 'Работающая и справедливая система', tail: 'над героизмом и авралами.', body: 'То есть мы вкладываем силы в создание стабильных и предсказуемых процессов, а не поощряем режим перманентного подвига, хотя мы бесконечно благодарны героям, которые спасают положение в кризис.' },
  { lead: 'Сотрудничество и доверие', tail: 'над тотальным контролем и подозрительностью.', body: 'То есть мы ценим открытость и взаимопомощь выше, чем попытки проконтролировать каждый шаг, хотя аудит и отчётность — это необходимые инструменты прозрачности, а не недоверия.' },
  { lead: 'Постоянное улучшение процессов', tail: 'над поиском виноватых.', body: 'То есть мы рассматриваем любую ошибку как симптом системного сбоя и возможность для улучшения, а не как повод для наказания человека, хотя личная ответственность и обязанность исправить последствия остаются неизменными.' },
  { lead: 'Смысл и осознанность', tail: 'над слепым следованием трендам.', body: 'То есть мы внедряем любое новшество только тогда, когда понимаем, какую боль оно решает и какой смысл в него заложен, хотя мы сохраняем открытость и любопытство ко всему новому.' },
  { lead: 'Прозрачность и конституция', tail: 'над устными указаниями и кулуарными решениями.', body: 'То есть мы закрепляем правила игры в письменной форме, доступной всем, чтобы они служили защитой от произвола и хаоса, хотя живое общение остаётся главным инструментом управления.' },
  { lead: 'Ментальное здоровье', tail: 'над когнитивным перегрузом.', body: 'То есть мы считаем выгорание и хронический перегруз критическим дефектом управления, а не нормой труда. Мы безжалостно удаляем устаревшее, чтобы освободить ресурс для создания нового.' },
  { lead: 'Конфликт мнений', tail: 'над уютным консенсусом.', body: 'То есть мы сознательно поощряем инакомыслие, которое бросает вызов консенсусу, потому что истина рождается в споре, а комфорт — это иллюзия, ведущая к стагнации.' },
  { lead: 'Антихрупкость', tail: 'над хрупкой эффективностью.', body: 'То есть мы строим систему, которая под внешним ударом не ломается и не просто выживает, а становится сильнее, благодаря гибкости своих правил и принципов.' },
  { lead: 'Открытая политика', tail: 'над неформальной властью.', body: 'То есть мы легализуем и выносим на публичное обсуждение любое лоббирование и использование неформальной власти, чтобы подвергнуть его критике. Иначе скрытая политика становится раком, разъедающим организацию изнутри.' }
];

const manifestoPrinciples = [
  'Наша высшая цель — построить самовоспроизводящуюся систему, которая стабильно даёт результат, даже когда нас нет на месте.',
  'Мы выходим в <em>«гембу»</em> не для того, чтобы найти виноватых, а чтобы понять и улучшить процесс.',
  'Мы — гаранты конституции. Наша роль — защищать правила игры, обеспечивать их справедливость и неукоснительное соблюдение всеми, включая себя.',
  'Мы создаём среду, где любая проблема может быть озвучена без страха. Мы верим, что скрытая проблема наносит больший ущерб, чем неприятный разговор.',
  'Мы платим за вклад и результат, а не за время, проведённое на работе. Справедливость оплаты — наш ключевой приоритет.',
  'Мы платим и за результат, и за смелость остановить сломанный процесс.',
  'Мы инвестируем в развитие «сообразительных умов», а не эксплуатируем «тёплые тела». Наша задача — чтобы каждый сотрудник стал инженером своего участка работы.',
  'Мы строим конкретные пути роста, а не учим «вообще полезному».',
  'Мы признаём, что настоящая команда — это не когда все делают работу друг за друга, а когда каждый так делает свою, что другим легко делать свою.',
  'Мы не ждём и не догоняем. Мы сами задаём стандарты качества и эффективности внутри своей отрасли.',
  'Мы понимаем, что люди проводят на работе большую часть жизни. Поэтому мы строим место силы, уважения и удовольствия от хорошо сделанного дела.',
  'Мы относимся к кулуарным решениям как к симптому загнивания системы.',
  'Любой кризис — стресс-тест правил. Необходимо нарушить правило в кризисе — измени правило.',
  'Мы защищаем фокус команды: нововведение внедряется взамен чего-то старого.',
  'Мы постоянно совершенствуем нашу архитектуру управления, используя как проверенные практики, так и смелые эксперименты, всегда соизмеряя их с нашими ценностями.'
];

const manifestoClosing = [
  'Мы призываем лидеров и управленцев принять эту эволюционную парадигму. Оставить в прошлом эпоху надсмотрщиков и вступить в эру инженеров человеческих управленческих систем. Наш инструмент — не приказ, а конституция. Наша цель — не контроль, а порядок, рождённый из свободы и смысла. Наша сила — не в героях-одиночках, а в системе, которая тиражирует героизм как стандартную практику.',
  'К нам присоединяются те, кто устал выбирать между результатом и людьми. Кто верит, что можно и нужно иметь и то, и другое. Кто не боится сложности и сознательно выбирает путь строительства, а не эксплуатации.',
  'Этот манифест — живой документ. Он не догма, а руководство к осознанному действию. Он для тех, кто готов брать на себя ответственность за созидание порядка из хаоса.'
];

const manifestoValueHtml = function(v, i) {
  return '<div class="manifesto-value"><span>' + (i + 1) + '.</span> <strong>' + v.lead + '</strong> ' + v.tail
    + '<div class="manifesto-value-body">' + v.body + '</div></div>';
};

const manifestoContent = '<section class="content-page">'
  + '<h1>Манифест</h1>'
  + '<p class="weapon-subtitle">Manifestum Imperii Rationalis — Манифест рационального управления</p>'
  + '<p class="manifesto-preamble">' + manifestoPreamble + '</p>'
  + '<h2>10 ценностей — выбор в пользу развития, а не догмы</h2>'
  + '<div class="manifesto-values">' + manifestoValues.map(manifestoValueHtml).join('') + '</div>'
  + '<h2>15 принципов — правила нашей повседневной практики</h2>'
  + '<ol class="manifesto-principles">' + manifestoPrinciples.map(function(p) { return '<li>' + p + '</li>'; }).join('') + '</ol>'
  + '<h2>Заключение</h2>'
  + manifestoClosing.map(function(p) { return '<p>' + p + '</p>'; }).join('')
  + '</section>';

const archiveContent = '<section class="content-page">'
  + '<h1>Архив великих идей</h1>'
  + '<p class="weapon-subtitle">Великие мыслители уже говорили это. Мы просто снимаем консалтинговую пыль.</p>'
  + '<div class="thinker-grid">'
  + thinkers.map(function(t) {
    return '<div class="thinker-card">'
      + (t.photo ? '<img src="/images/thinkers/' + t.photo + '" alt="' + t.name + ' — фото" class="thinker-photo" loading="lazy">' : '')
      + '<div class="thinker-name">' + t.name + '</div>'
      + '<div class="thinker-years">' + t.years + '</div>'
      + '<div class="thinker-idea">' + t.idea + '</div>'
      + '<div class="thinker-arrow">→ ' + t.weapon + '</div>'
      + '</div>';
  }).join('')
  + '</div></section>';

const arsenalContent = '<section class="content-page">'
  + '<h1>Арсенал</h1>'
  + '<p class="weapon-subtitle">' + weapons.filter(function(w) { return w.status === 'published'; }).length + ' опубликовано, ' + weapons.length + ' всего. Выбери оружие.</p>'
  + '<div class="filters">'
  + '<button class="filter-btn active" data-filter="all">ВСЕ</button>'
  + scenarios.map(function(s) { return '<button class="filter-btn" data-filter="' + escapeHtml(s.id) + '">' + s.title + '</button>'; }).join('')
  + '</div>'
  + '<div class="weapon-grid" id="arsenalGrid">'
  + weapons.map(function(w) {
    return '<a href="/weapons/' + escapeHtml(w.slug) + '/" class="weapon-card" data-zone="' + escapeHtml(w.zone || '') + '">'
      + '<div class="weapon-title">' + w.title + '</div>'
      + '<div class="weapon-subtitle">' + (w.subtitle || '') + '</div>'
      + (w.zone ? zoneBadgeHtml(w.zone) : '')
      + statusBadgeHtml(w.status)
      + '</a>';
  }).join('')
  + '</div></section>'
  + '<script>document.addEventListener(\'DOMContentLoaded\',function(){'
  + 'var btns=document.querySelectorAll(\'.filters .filter-btn\');'
  + 'var cards=document.querySelectorAll(\'#arsenalGrid .weapon-card\');'
  + 'btns.forEach(function(b){b.addEventListener(\'click\',function(){'
  + 'btns.forEach(function(x){x.classList.remove(\'active\');});'
  + 'this.classList.add(\'active\');var f=this.dataset.filter;'
  + 'cards.forEach(function(c){c.style.display=(f===\'all\'||c.dataset.zone===f)?\'\':\'none\';});});});});</script>';

const scenariosContent = '<section class="content-page">'
  + '<h1>Сценарии</h1>'
  + '<p class="weapon-subtitle">Выбери свой участок фронта — получи набор оружия.</p>'
  + scenarios.map(function(s) {
    var zoneWeapons = s.weapons.map(function(id) { return weaponById(id); }).filter(Boolean);
    return '<div class="zone-card zone-' + escapeHtml(s.id) + '" style="margin-bottom:var(--space-6);">'
      + '<div class="zone-icon">' + s.icon + '</div>'
      + '<div class="zone-title">' + s.title + '</div>'
      + '<p style="margin-top:var(--space-2);">' + s.subtitle + '</p>'
      + '<div class="weapon-grid" style="margin-top:var(--space-4);">'
      + zoneWeapons.map(function(w) {
        return '<a href="/weapons/' + escapeHtml(w.slug) + '/" class="weapon-card">'
          + '<div class="weapon-title">' + w.title + '</div>'
          + '<div class="weapon-subtitle">' + (w.subtitle || '') + '</div>'
          + '</a>';
      }).join('')
      + '</div></div>';
  }).join('')
  + '</section>';

const casesContent = '<section class="content-page">'
  + '<h1>Полевые дневники</h1>'
  + '<p class="weapon-subtitle">Реальные истории с заводов.</p>'
  + '<div class="case-grid">'
  + cases.map(function(c) {
    return '<div class="case-card">'
      + '<div class="case-headline"><span>⚔️</span>' + c.title + '</div>'
      + '<p class="weapon-subtitle" style="margin-top:var(--space-2);">' + c.desc + '</p>'
      + '<div class="case-readtime">⏱ ' + (c.readtime || '5 минут') + '</div>'
      + '</div>';
  }).join('')
  + '</div></section>';

const hqContent = '<section class="content-page" style="text-align:center;padding-top:var(--space-16);">'
  + '<h1>Штаб</h1>'
  + '<p class="weapon-subtitle">Закрытый клуб партизан. Здесь не обсуждают теорию. Здесь разбирают боевые ситуации.</p>'
  + '<p style="color:var(--color-steel);margin:var(--space-4) 0;">⚡ Еженедельный разбор полётов · ⚡ Анонимные вопросы · ⚡ Реальные кейсы</p>'
  + '<a href="https://t.me/antimanager" class="btn btn-crisis" style="margin-top:var(--space-6);">💬 ВСТУПИТЬ В TELEGRAM</a>'
  + '</section>';

const aboutContent = '<section class="content-page">'
  + '<h1>О проекте</h1>'
  + '<p class="weapon-subtitle">Антименеджер — это не метод. Это присяга.</p>'
  + '<div class="weapon-block" style="margin:var(--space-6) 0;">'
  + '<p>Мы не изобретаем велосипед. Мы просто снимаем консалтинговую упаковку с идей Деминга, Тейлора, Богданова, Оно, Медоуз, Хапрова, Клаузевица... И адаптируем их к твоему конвейеру.</p>'
  + '</div>'
  + '<p style="color:var(--color-steel);">Единственный способ изменить систему — начать думать и делать осознанно.</p>'
  + '</section>';

// === LANDING PAGE ===

const landingContent = '<section class="hero">'
  + '<div class="hero-challenge">'
  + '<h1 class="hero-heading">ТЫ ПРИШЁЛ ЗА ТАБЛЕТКОЙ?</h1>'
  + '<h2 class="hero-answer">ЕЁ НЕТ.</h2>'
  + '</div>'
  + '<div class="hero-mckinsey">'
  + '<p>Хочешь красивый совет? Иди к McKinsey. Они нарисуют тебе 100 слайдов. Ты заплатишь 10 миллионов. Через год всё вернётся.</p>'
  + '<p class="hero-stay">Хочешь понять, как на самом деле работают великие идеи управления? <strong>Оставайся.</strong></p>'
  + '</div>'
  + '<div class="hero-thinkers">'
  + '<p>Мы просто снимаем слой консалтинговой пыли с идей Деминга, Тейлора, Богданова, Оно, Медоуз, Хапрова, Клаузевица...</p>'
  + '<p class="hero-quote">«Сначала среда, потом требования». «Сложность управляется сложностью». «Любая система лжёт». Просто консультанты забыли это сказать.</p>'
  + '</div>'
  + '<div class="hero-cta">'
  + '<a href="/weapons/antikrizis/" class="btn btn-crisis">🔥 У МЕНЯ КРИЗИС</a>'
  + '<a href="#system-map" class="btn btn-primary">🗺️ ХОЧУ ПОНЯТЬ СИСТЕМУ</a>'
  + '</div>'
  + '</section>'

  + '<section class="section archaeology">'
  + '<h2 class="section-title">МЫ — АРХЕОЛОГИ УПРАВЛЕНИЯ</h2>'
  + '<p class="section-desc">Каждый инструмент Антименеджера — это раскопка. Мы находим изначальную идею великого мыслителя. Очищаем её от консалтинговой упаковки. И адаптируем к твоему конвейеру.</p>'
  + '<div class="thinker-chain">'
  + thinkers.slice(0, 5).map(function(t) { return '<span>' + t.name.split(' ').pop() + ' → ' + t.weapon + '</span>'; }).join('')
  + '</div>'
  + '<a href="/archive/" class="btn" style="margin-top:var(--space-4);">🏛️ ВЕСЬ АРХИВ</a>'
  + '</section>'

  + '<section class="section" id="weapons-section">'
  + '<h2 class="section-title">ЭТО — ОРУЖИЕ. А НЕ ЕЩЁ ОДНА КНИГА</h2>'
  + '<p class="section-desc">Антименеджер — это не метод. Это способ думать. Метод можно скопировать. Способ думать — нельзя.</p>'
  + '<p class="section-desc">Разница простая: метод даёт тебе инструкцию. Способ думать даёт тебе критерий: «Как понять, что инструкция врёт».</p>'
  + '<div class="weapon-grid">' + featuredWeaponsHtml + '</div>'
  + '<a href="/arsenal/" class="btn btn-primary">🔫 ВЕСЬ АРСЕНАЛ</a>'
  + '</section>'

  + '<section class="section" id="system-map">'
  + '<h2 class="section-title">КАРТА СИСТЕМЫ</h2>'
  + '<div class="map-container">' + starSvg() + '</div>'
  + '</section>'

  + '<section class="section">'
  + '<h2 class="section-title">ВЫБЕРИ СВОЙ УЧАСТОК ФРОНТА</h2>'
  + '<div class="zone-grid">'
  + scenarios.map(function(s) {
    var count = s.weapons.filter(function(id) { return weaponById(id); }).length;
    return '<a href="/scenarios/" class="zone-card zone-' + escapeHtml(s.id) + '">'
      + '<div class="zone-icon">' + s.icon + '</div>'
      + '<div class="zone-title">' + s.title + '</div>'
      + '<div class="zone-subtitle">' + s.subtitle + '</div>'
      + '<span class="zone-count">' + count + '</span>'
      + '</a>';
  }).join('')
  + '</div>'
  + '</section>'

  + '<section class="section manifesto-teaser">'
  + '<h2 class="section-title">МАНИФЕСТ ИМПЕРИИ РАЦИОНАЛЬНОГО</h2>'
  + '<p class="section-desc">Это не просто слова. Это конституция Антименеджера.</p>'
  + '<div class="manifesto-values">'
  + manifestoValues.map(function(v, i) {
      return '<div class="manifesto-value"><span>' + (i + 1) + '.</span> <strong>' + v.lead + '</strong> ' + v.tail + '</div>';
    }).join('')
  + '</div>'
  + '<a href="/manifesto/" class="btn">📜 ЧИТАТЬ ПОЛНОСТЬЮ</a>'
  + '</section>'

  + '<section class="section">'
  + '<h2 class="section-title">ПОЛЕВЫЕ ДНЕВНИКИ</h2>'
  + '<p class="section-desc">Реальные истории с заводов.</p>'
  + '<div class="case-grid">'
  + cases.slice(0, 3).map(function(c) {
    return '<a href="/cases/" class="case-card">'
      + '<div class="case-headline"><span>⚔️</span>' + c.title + '</div>'
      + '<div class="weapon-subtitle">' + c.desc + '</div>'
      + '<div class="case-readtime">⏱ ' + (c.readtime || '5 минут') + '</div>'
      + '</a>';
  }).join('')
  + '</div>'
  + '<a href="/cases/" class="btn" style="margin-top:var(--space-4);">📖 ВСЕ ИСТОРИИ</a>'
  + '</section>'

  + '<section class="section hq-section">'
  + '<h2 class="section-title">ВСТУПАЙ В ШТАБ</h2>'
  + '<p class="section-desc">Это закрытый клуб партизан. Здесь не обсуждают теорию. Здесь разбирают боевые ситуации.</p>'
  + '<p class="section-desc">⚡ Еженедельный разбор полётов · ⚡ Анонимные вопросы · ⚡ Реальные кейсы</p>'
  + '<a href="https://t.me/antimanager" class="btn btn-primary">💬 ВСТУПИТЬ В TELEGRAM</a>'
  + '</section>'

  + '<section class="section stats-section">'
  + '<h2 class="section-title">СЕГОДНЯ В ОКОПЕ</h2>'
  + '<div class="stats-grid">'
  + '<div class="stats-item"><strong>2 847</strong>управленцев читают</div>'
  + '<div class="stats-item"><strong>113</strong>внедрили «правило трёх вопросов»</div>'
  + '<div class="stats-item"><strong>47</strong>вышли из кризиса за 90 дней</div>'
  + '</div>'
  + '</section>'
  + '<section style="text-align:center;padding-bottom:var(--space-8);">'
  + '<p style="color:var(--color-steel);">Ты либо берёшь ответственность за хаос, либо продолжаешь заполнять таблички.</p>'
  + '</section>';

// === WEAPON TEMPLATE ===

const weaponTemplate = '<div class="content-page">'
  + '<nav class="breadcrumbs"><a href="/">Главная</a> <span class="sep">→</span> <a href="/arsenal/">Арсенал</a> <span class="sep">→</span> <span>{{title}}</span></nav>'
  + '<section class="weapon-hero">'
  + '{{zone_badge}}'
  + '<h1>{{title}}</h1>'
  + '<p class="weapon-subtitle">{{subtitle}}</p>'
  + '{{status_badge}}'
  + '</section>'
  + '{{content_body}}'
  + '{{thinker_block}}'
  + '{{related_weapons}}'
  + '</div>';

const fullTemplate = '<div class="content-page full-article-page">'
  + '<nav class="breadcrumbs"><a href="/">Главная</a> <span class="sep">→</span> <a href="/arsenal/">Арсенал</a> <span class="sep">→</span> <a href="/weapons/{{slug}}/">{{title}}</a> <span class="sep">→</span> <span>Полный текст</span></nav>'
  + '<div class="reading-progress" aria-hidden="true"><div class="reading-progress-fill"></div></div>'
  + '<header class="full-hero">'
  + '{{zone_badge}}'
  + '<h1>{{title}}</h1>'
  + '<p class="weapon-subtitle">{{subtitle}}</p>'
  + '<p class="full-meta">⏱ {{read_minutes}} мин чтения · Полный текст</p>'
  + '<a class="btn btn-ghost btn-sm" href="/weapons/{{slug}}/">← К интерактивной модели</a>'
  + '</header>'
  + '{{toc}}'
  + '<article class="full-article">{{content_body}}</article>'
  + '{{materials_section}}'
  + '{{thinker_block}}'
  + '{{related_weapons}}'
  + '</div>';

// === BUILD: MAIN ===

console.log('\n🚀 AntiManager Brutalist Build\n');

// Landing
write('index.html', renderPage('AntiManager — Система управления производством', 'Интерактивная карта: ' + plural(scenarios.length, 'контур', 'контура', 'контуров') + ', ' + plural(weapons.length, 'глава', 'главы', 'глав') + ', инструментов и кейсов для руководителя производства', landingContent, { canonicalUrl: SITE_URL + '/', structuredData: makeStructuredData('landing') }));

// Static pages
write('manifesto/index.html', renderPage('Манифест | AntiManager', 'Манифест рационального управления — 10 ценностей и принципов', manifestoContent, { canonicalUrl: SITE_URL + '/manifesto/', structuredData: makeStructuredData('static', { name: 'Манифест', url: SITE_URL + '/manifesto/' }) }));
write('archive/index.html', renderPage('Архив великих идей | AntiManager', 'Великие мыслители управления: Шухарт, Деминг, Оно, Богданов, Гастев', archiveContent, { canonicalUrl: SITE_URL + '/archive/', structuredData: makeStructuredData('static', { name: 'Архив великих идей', url: SITE_URL + '/archive/' }) }));
write('arsenal/index.html', renderPage('Арсенал | AntiManager', 'Все ' + weapons.length + ' инструментов-орудий Антименеджера', arsenalContent, { canonicalUrl: SITE_URL + '/arsenal/', structuredData: makeStructuredData('static', { name: 'Арсенал', url: SITE_URL + '/arsenal/' }) }));
write('scenarios/index.html', renderPage('Сценарии | AntiManager', 'Выбери свой участок фронта: кризис, команда, изменения, система', scenariosContent, { canonicalUrl: SITE_URL + '/scenarios/', structuredData: makeStructuredData('static', { name: 'Сценарии', url: SITE_URL + '/scenarios/' }) }));
write('cases/index.html', renderPage('Полевые дневники | AntiManager', 'Реальные истории с заводов', casesContent, { canonicalUrl: SITE_URL + '/cases/', structuredData: makeStructuredData('static', { name: 'Полевые дневники', url: SITE_URL + '/cases/' }) }));
write('headquarters/index.html', renderPage('Штаб | AntiManager', 'Закрытый клуб партизан — Telegram', hqContent, { canonicalUrl: SITE_URL + '/headquarters/', structuredData: makeStructuredData('static', { name: 'Штаб', url: SITE_URL + '/headquarters/' }) }));
write('about/index.html', renderPage('О проекте | AntiManager', 'Антименеджер — это не метод. Это присяга.', aboutContent, { canonicalUrl: SITE_URL + '/about/', structuredData: makeStructuredData('static', { name: 'О проекте', url: SITE_URL + '/about/' }) }));
write('404/index.html', renderPage('404 — Страница не найдена | AntiManager', '', '<div class="empty-state"><h1>404</h1><p>Страница не найдена. <a href="/" class="btn btn-primary" style="display:inline-flex;">На главную</a></p></div>', { noindex: true, canonicalUrl: SITE_URL + '/404/' }));
write('privacy/index.html', renderPage('Политика конфиденциальности | AntiManager', 'Политика конфиденциальности', '<section class="content-page"><h1>Политика конфиденциальности</h1><p>Мы не собираем персональные данные пользователей. Сайт использует только технические файлы cookie, необходимые для работы.</p></section>', { noindex: true, canonicalUrl: SITE_URL + '/privacy/' }));

// Weapon pages
for (var wi = 0; wi < weapons.length; wi++) {
  var w = weapons[wi];
  var contentPath = path.join(__dirname, 'src', 'content', w.id + '-' + w.slug + '.html');
  var hasContent = fs.existsSync(contentPath);
  var contentBody = hasContent ? fs.readFileSync(contentPath, 'utf-8') : '<div class="empty-state"><h3>Статья в разработке</h3><p>Эта статья ещё не готова. Скоро здесь появится текст.</p><p style="margin-top:var(--space-4);"><a href="/arsenal/" class="btn" style="display:inline-flex;">← Вернуться в арсенал</a></p></div>';

  var zoneBadge = zoneBadgeHtml(w.zone);
  var statusSpan = statusBadgeHtml(w.status);

  var thinker = thinkers.find(function(t) { return t.id === w.thinker; });
  var thinkerBlock = thinker
    ? '<div class="thinker-block">'
      + (thinker.photo ? '<img src="/images/thinkers/' + thinker.photo + '" alt="' + thinker.name + ' — фото" class="thinker-photo-sm" loading="lazy">' : '')
      + '<div class="thinker-block-text"><strong>Изначальная идея:</strong> ' + thinker.name + ' (' + thinker.years + ') → ' + thinker.weapon + '</div></div>'
    : '';

  var fullPath = path.join(__dirname, 'src', 'content', 'full', w.id + '-' + w.slug + '.html');
  var hasFull = fs.existsSync(fullPath);
  var fullBody = hasFull ? fs.readFileSync(fullPath, 'utf-8') : '';

  // Read-more card replaces the old lite "Тезисный отрывок": a short lede from
  // the full text plus an explicit path to it. Rendered only when the full text
  // actually exists, so no landing ever links to a missing page.
  var readMoreHtml = '';
  if (hasFull) {
    var ledeMatch = fullBody.match(/<p[^>]*>([\s\S]*?)<\/p>/i);
    var lede = ledeMatch ? ledeMatch[1].replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim() : '';
    if (lede.length > 220) lede = lede.slice(0, 217).replace(/\s+\S*$/, '') + '…';
    if (!lede) lede = w.subtitle || '';
    readMoreHtml = '<aside class="read-more-card">'
      + '<div class="read-more-label">Полный текст статьи</div>'
      + (lede ? '<p class="read-more-hook">' + lede + '</p>' : '')
      + '<div class="read-more-meta">⏱ ' + readMinutes(fullBody) + ' мин чтения</div>'
      + '<a class="btn btn-primary" href="/weapons/' + escapeHtml(w.slug) + '/full/">Читать статью полностью →</a>'
      + '</aside>';
  }

  // Prefer same zone; fall back to same thinker, then shared tags, then other
  // zone-less weapons so every article keeps at least one internal link.
  var related = weapons.filter(function(r) { return r.zone !== null && r.zone === w.zone && r.slug !== w.slug; });
  if (related.length === 0) {
    related = weapons.filter(function(r) { return r.slug !== w.slug && w.thinker && r.thinker === w.thinker; });
  }
  if (related.length === 0) {
    var wTags = w.tags || [];
    related = weapons.filter(function(r) {
      return r.slug !== w.slug && (r.tags || []).some(function(t) { return wTags.indexOf(t) !== -1; });
    });
  }
  if (related.length === 0) {
    related = weapons.filter(function(r) { return r.slug !== w.slug && !r.zone; });
  }
  related = related.slice(0, 4);
  var relatedHtml = '';
  if (related.length > 0) {
    relatedHtml = '<h2 class="section-title" style="margin-top:var(--space-10);">В том же окопе</h2><div class="weapon-grid">'
      + related.map(function(r) {
        return '<a href="/weapons/' + escapeHtml(r.slug) + '/" class="weapon-card">'
          + '<div class="weapon-title">' + r.title + '</div>'
          + '<div class="weapon-subtitle">' + (r.subtitle || '') + '</div>'
          + '</a>';
      }).join('')
      + '</div>';
  }

  // Resolve the read-more placeholder inside the authored partial. Function
  // replacers everywhere: authored text may contain "$" patterns.
  contentBody = contentBody.replace(/\{\{read_more\}\}/g, function() { return readMoreHtml; });

  var html = weaponTemplate;
  html = html.replace(/{{title}}/g, function() { return w.title; });
  html = html.replace('{{subtitle}}', function() { return w.subtitle || ''; });
  html = html.replace('{{zone_badge}}', function() { return zoneBadge; });
  html = html.replace('{{status_badge}}', function() { return statusSpan; });
  html = html.replace('{{content_body}}', function() { return contentBody; });
  html = html.replace('{{thinker_block}}', function() { return thinkerBlock; });
  html = html.replace('{{related_weapons}}', function() { return relatedHtml; });

  var canonicalUrl = SITE_URL + '/weapons/' + escapeHtml(w.slug) + '/';
  var zoneLabel = w.zone ? zoneLabels[w.zone] : null;
  write('weapons/' + w.slug + '/index.html', renderPage(w.title + ' | AntiManager', w.subtitle || '', html, { canonicalUrl: canonicalUrl, ogType: 'article', ogArticleSection: zoneLabel, ogTags: w.tags, structuredData: makeStructuredData('weapon', { title: w.title, subtitle: w.subtitle, canonicalUrl: canonicalUrl, articleSection: zoneLabel }) }));
  console.log('  ✓ ' + w.id + ' ' + w.slug);

  // Full-text page ships only when its source partial exists.
  if (hasFull) {
    var toc = withToc(fullBody);
    var fullHtml = fullTemplate;
    fullHtml = fullHtml.replace(/{{title}}/g, function() { return w.title; });
    fullHtml = fullHtml.replace(/{{slug}}/g, function() { return escapeHtml(w.slug); });
    fullHtml = fullHtml.replace('{{subtitle}}', function() { return w.subtitle || ''; });
    fullHtml = fullHtml.replace('{{zone_badge}}', function() { return zoneBadge; });
    fullHtml = fullHtml.replace('{{read_minutes}}', function() { return String(readMinutes(fullBody)); });
    fullHtml = fullHtml.replace('{{toc}}', function() { return toc.toc; });
    fullHtml = fullHtml.replace('{{content_body}}', function() { return toc.html; });
    fullHtml = fullHtml.replace('{{materials_section}}', function() { return materialsBlockHtml(w); });
    fullHtml = fullHtml.replace('{{thinker_block}}', function() { return thinkerBlock; });
    fullHtml = fullHtml.replace('{{related_weapons}}', function() { return relatedHtml; });

    var fullUrl = SITE_URL + '/weapons/' + escapeHtml(w.slug) + '/full/';
    write('weapons/' + w.slug + '/full/index.html', renderPage(w.title + ' — полный текст | AntiManager', w.subtitle || '', fullHtml, { canonicalUrl: fullUrl, ogType: 'article', ogArticleSection: zoneLabel, ogTags: w.tags, structuredData: makeStructuredData('articleFull', { title: w.title, subtitle: w.subtitle, canonicalUrl: fullUrl, articleSection: zoneLabel, slug: escapeHtml(w.slug) }) }));
    console.log('  ✓ ' + w.id + ' ' + w.slug + ' (full)');
  }
}

// Sitemap
var sitemapUrls = [
  { loc: SITE_URL + '/', priority: '1.0', changefreq: 'daily', lastmod: BUILD_DATE },
  { loc: SITE_URL + '/arsenal/', priority: '0.9', changefreq: 'weekly', lastmod: BUILD_DATE },
  { loc: SITE_URL + '/manifesto/', priority: '0.8', changefreq: 'monthly', lastmod: BUILD_DATE },
  { loc: SITE_URL + '/archive/', priority: '0.7', changefreq: 'monthly', lastmod: BUILD_DATE },
  { loc: SITE_URL + '/scenarios/', priority: '0.7', changefreq: 'weekly', lastmod: BUILD_DATE },
  { loc: SITE_URL + '/cases/', priority: '0.7', changefreq: 'monthly', lastmod: BUILD_DATE },
  { loc: SITE_URL + '/headquarters/', priority: '0.5', changefreq: 'monthly', lastmod: BUILD_DATE },
  { loc: SITE_URL + '/about/', priority: '0.5', changefreq: 'monthly', lastmod: BUILD_DATE },
];
for (var si = 0; si < weapons.length; si++) {
  if (fs.existsSync(path.join(__dirname, 'src', 'content', weapons[si].id + '-' + weapons[si].slug + '.html'))) {
    sitemapUrls.push({ loc: SITE_URL + '/weapons/' + weapons[si].slug + '/', priority: '0.9', changefreq: 'weekly', lastmod: BUILD_DATE });
  }
  if (fs.existsSync(path.join(__dirname, 'src', 'content', 'full', weapons[si].id + '-' + weapons[si].slug + '.html'))) {
    sitemapUrls.push({ loc: SITE_URL + '/weapons/' + weapons[si].slug + '/full/', priority: '0.9', changefreq: 'weekly', lastmod: BUILD_DATE });
  }
}
var sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';
for (var si2 = 0; si2 < sitemapUrls.length; si2++) {
  sitemap += '  <url>\n    <loc>' + sitemapUrls[si2].loc + '</loc>\n    <lastmod>' + sitemapUrls[si2].lastmod + '</lastmod>\n    <changefreq>' + sitemapUrls[si2].changefreq + '</changefreq>\n    <priority>' + sitemapUrls[si2].priority + '</priority>\n  </url>\n';
}
sitemap += '</urlset>';
write('sitemap.xml', sitemap);
write('robots.txt', 'User-agent: *\nAllow: /\n\nSitemap: ' + SITE_URL + '/sitemap.xml\n');

// Copy assets
copyDir('css', 'css');
copyDir('js', 'js');
copyDir('fonts', 'fonts');
copyDir('materials', 'materials');
  copyDir('../Фото_мыслителей', 'images/thinkers');
  write('favicon.svg', read('favicon.svg'));
if (fs.existsSync(OG_IMAGE_PNG)) write('og-image.png', read(OG_IMAGE_PNG));
write('og-image.svg', read('src/templates/og-image.svg'));
write('yandex_XXXXXXXXXXXXXXXX.html', '<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></head><body>Verification: XXXXXXXXXXXXXXXX</body></html>');

console.log('\n✅ Build complete. Output: ' + path.join(__dirname, 'dist') + '\n');
