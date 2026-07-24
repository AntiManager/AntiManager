#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const SITE_URL = 'https://antimanager.pro';
const BUILD_DATE = '2026-07-24';

function read(name) { return fs.readFileSync(path.join(__dirname, name), 'utf-8'); }
function write(filepath, content) {
  const dir = path.dirname(path.join(__dirname, 'dist', filepath));
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(__dirname, 'dist', filepath), content, 'utf-8');
}
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

const weapons = JSON.parse(read('src/data/weapons.json'));
const scenarios = JSON.parse(read('src/data/scenarios.json'));
const thinkers = JSON.parse(read('src/data/thinkers.json'));
const cases = JSON.parse(read('src/data/cases.json'));

const zoneLabels = { crisis: 'КРИЗИС', team: 'КОМАНДА', changes: 'ИЗМЕНЕНИЯ', system: 'СИСТЕМА' };
const statusLabels = { published: 'Опубликовано', review: 'На ревью', draft: 'Черновик' };

function weaponById(id) { return weapons.find(w => w.id === id); }

function zoneBadgeHtml(zone) {
  if (!zone) return '';
  return `<span class="badge badge-zone badge-zone-${zone}">${zoneLabels[zone] || zone}</span>`;
}

function statusBadgeHtml(status) {
  return `<span class="badge badge-status badge-status-${status}">${statusLabels[status] || status}</span>`;
}

function escapeHtml(s) {
  return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function makeStructuredData(pageType, data) {
  data = data || {};
  function json(ld) {
    return '\n<script type="application/ld+json">' + JSON.stringify(ld, null, 2) + '</script>';
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
  if (pageType === 'static') {
    return json({
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      'name': 'AntiManager',
      'url': SITE_URL,
      'inLanguage': 'ru'
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
  const ogImage = opts.ogImage || SITE_URL + '/og-image.png';

  let headTags = ''
    + '<link rel="canonical" href="' + canonicalUrl + '">\n'
    + '<meta property="og:title" content="' + escapeHtml(title) + '">\n'
    + '<meta property="og:description" content="' + escapeHtml(desc) + '">\n'
    + '<meta property="og:url" content="' + canonicalUrl + '">\n'
    + '<meta property="og:type" content="' + ogType + '">\n'
    + '<meta property="og:image" content="' + ogImage + '">\n'
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
    headTags += '\n<meta property="article:author" content="' + SITE_URL + '/about/">';
  }

  if (opts.headExtra) headTags += '\n' + opts.headExtra;

  const scripts = '<script src="/js/brutalist.js" defer></script>'
    + (opts.scripts ? '\n' + opts.scripts : '');

  let html = base;
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

const publishedWeapons = weapons.filter(function(w) { return w.status === 'published'; });
const featuredWeapons = publishedWeapons.length > 0
  ? publishedWeapons.slice(0, 4)
  : weapons.filter(function(w) { return w.status === 'review'; }).slice(0, 4);

const featuredWeaponsHtml = featuredWeapons.map(function(w) {
  return '<a href="/weapons/' + w.slug + '/" class="weapon-card">'
    + '<div class="weapon-title">' + w.title + '</div>'
    + '<div class="weapon-subtitle">' + (w.subtitle || '') + '</div>'
    + (w.zone ? '<span class="weapon-status">' + zoneLabels[w.zone] + '</span>' : '')
    + '</a>';
}).join('');

const manifestoContent = '<section class="content-page">'
  + '<h1>Манифест</h1>'
  + '<p class="weapon-subtitle">Manifestum Imperii Rationalis — Манифест рационального управления</p>'
  + '<div class="manifesto-values">'
  + '<div class="manifesto-value"><span>1.</span> Люди и их потенциал над слепым исполнением инструкций</div>'
  + '<div class="manifesto-value"><span>2.</span> Работающая и справедливая система над героизмом и авралами</div>'
  + '<div class="manifesto-value"><span>3.</span> Сотрудничество и доверие над тотальным контролем</div>'
  + '<div class="manifesto-value"><span>4.</span> Постоянное улучшение процессов над поиском виноватых</div>'
  + '<div class="manifesto-value"><span>5.</span> Смысл и осознанность над слепым следованием трендам</div>'
  + '<div class="manifesto-value"><span>6.</span> Прозрачность и конституция над устными указаниями</div>'
  + '<div class="manifesto-value"><span>7.</span> Ментальное здоровье над когнитивным перегрузом</div>'
  + '<div class="manifesto-value"><span>8.</span> Конфликт мнений над уютным консенсусом</div>'
  + '<div class="manifesto-value"><span>9.</span> Антихрупкость над хрупкой эффективностью</div>'
  + '<div class="manifesto-value"><span>10.</span> Открытая политика над неформальной властью</div>'
  + '</div></section>';

const archiveContent = '<section class="content-page">'
  + '<h1>Архив великих идей</h1>'
  + '<p class="weapon-subtitle">Великие мыслители уже говорили это. Мы просто снимаем консалтинговую пыль.</p>'
  + '<div class="thinker-grid">'
  + thinkers.map(function(t) {
    return '<div class="thinker-card">'
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
  + scenarios.map(function(s) { return '<button class="filter-btn" data-filter="' + s.id + '">' + s.title + '</button>'; }).join('')
  + '</div>'
  + '<div class="weapon-grid" id="arsenalGrid">'
  + weapons.map(function(w) {
    return '<a href="/weapons/' + w.slug + '/" class="weapon-card" data-zone="' + (w.zone || '') + '">'
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
    return '<div class="zone-card zone-' + s.id + '" style="margin-bottom:var(--space-6);">'
      + '<div class="zone-icon">' + s.icon + '</div>'
      + '<div class="zone-title">' + s.title + '</div>'
      + '<p style="margin-top:var(--space-2);">' + s.subtitle + '</p>'
      + '<div class="weapon-grid" style="margin-top:var(--space-4);">'
      + zoneWeapons.map(function(w) {
        return '<a href="/weapons/' + w.slug + '/" class="weapon-card">'
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
  + '<a href="/scenarios/" class="btn btn-crisis">🔥 У МЕНЯ КРИЗИС</a>'
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
    return '<a href="/scenarios/" class="zone-card zone-' + s.id + '">'
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
  + '<div class="manifesto-value"><span>1.</span> Люди и их потенциал над слепым исполнением</div>'
  + '<div class="manifesto-value"><span>2.</span> Работающая система над героизмом и авралами</div>'
  + '<div class="manifesto-value"><span>3.</span> Сотрудничество и доверие над тотальным контролем</div>'
  + '<div class="manifesto-value"><span>4.</span> Постоянное улучшение процессов над поиском виноватых</div>'
  + '<div class="manifesto-value"><span>5.</span> Смысл и осознанность над слепым следованием трендам</div>'
  + '<div class="manifesto-value"><span>6.</span> Прозрачность и конституция над кулуарными решениями</div>'
  + '<div class="manifesto-value"><span>7.</span> Ментальное здоровье над когнитивным перегрузом</div>'
  + '<div class="manifesto-value"><span>8.</span> Конфликт мнений над уютным консенсусом</div>'
  + '<div class="manifesto-value"><span>9.</span> Антихрупкость над хрупкой эффективностью</div>'
  + '<div class="manifesto-value"><span>10.</span> Открытая политика над неформальной властью</div>'
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
  + '{{download_section}}'
  + '{{related_weapons}}'
  + '</div>';

// === BUILD: MAIN ===

console.log('\n🚀 AntiManager Brutalist Build\n');

// Landing
write('index.html', renderPage('AntiManager — Система управления производством', 'Интерактивная карта: 5 контуров, ' + weapons.length + ' глав, инструментов и кейсов для руководителя производства', landingContent, { canonicalUrl: SITE_URL + '/', structuredData: makeStructuredData('landing') }));

// Static pages
write('manifesto/index.html', renderPage('Манифест | AntiManager', 'Манифест рационального управления — 10 ценностей и принципов', manifestoContent, { canonicalUrl: SITE_URL + '/manifesto/', structuredData: makeStructuredData('static') }));
write('archive/index.html', renderPage('Архив великих идей | AntiManager', 'Великие мыслители управления: Шухарт, Деминг, Оно, Богданов, Гастев', archiveContent, { canonicalUrl: SITE_URL + '/archive/', structuredData: makeStructuredData('static') }));
write('arsenal/index.html', renderPage('Арсенал | AntiManager', 'Все ' + weapons.length + ' инструментов-орудий Антименеджера', arsenalContent, { canonicalUrl: SITE_URL + '/arsenal/', structuredData: makeStructuredData('static') }));
write('scenarios/index.html', renderPage('Сценарии | AntiManager', 'Выбери свой участок фронта: кризис, команда, изменения, система', scenariosContent, { canonicalUrl: SITE_URL + '/scenarios/', structuredData: makeStructuredData('static') }));
write('cases/index.html', renderPage('Полевые дневники | AntiManager', 'Реальные истории с заводов', casesContent, { canonicalUrl: SITE_URL + '/cases/', structuredData: makeStructuredData('static') }));
write('headquarters/index.html', renderPage('Штаб | AntiManager', 'Закрытый клуб партизан — Telegram', hqContent, { canonicalUrl: SITE_URL + '/headquarters/', structuredData: makeStructuredData('static') }));
write('about/index.html', renderPage('О проекте | AntiManager', 'Антименеджер — это не метод. Это присяга.', aboutContent, { canonicalUrl: SITE_URL + '/about/', structuredData: makeStructuredData('static') }));
write('404/index.html', renderPage('404 — Страница не найдена | AntiManager', '', '<div class="empty-state"><h1>404</h1><p>Страница не найдена. <a href="/" class="btn btn-primary" style="display:inline-flex;">На главную</a></p></div>', { noindex: true, canonicalUrl: SITE_URL + '/404/' }));
write('privacy/index.html', renderPage('Политика конфиденциальности | AntiManager', 'Политика конфиденциальности', '<section class="content-page"><h1>Политика конфиденциальности</h1><p>Мы не собираем персональные данные пользователей. Сайт использует только технические файлы cookie, необходимые для работы.</p></section>', { noindex: true, canonicalUrl: SITE_URL + '/privacy/' }));

// Weapon pages
for (var wi = 0; wi < weapons.length; wi++) {
  var w = weapons[wi];
  var contentPath = path.join(__dirname, 'src', 'content', w.id + '-' + w.slug + '.html');
  var hasContent = fs.existsSync(contentPath);
  var contentBody = hasContent ? fs.readFileSync(contentPath, 'utf-8') : '<div class="empty-state"><h3>Статья в разработке</h3><p>Эта статья ещё не готова. Скоро здесь появится текст.</p><p style="margin-top:var(--space-4);"><a href="/arsenal/" class="btn" style="display:inline-flex;">← Вернуться в арсенал</a></p></div>';

  var zoneBadge = w.zone ? '<span class="badge badge-zone badge-zone-' + w.zone + '">' + (zoneLabels[w.zone] || w.zone) + '</span>' : '';
  var statusSpan = statusBadgeHtml(w.status);

  var thinker = thinkers.find(function(t) { return t.id === w.thinker; });
  var thinkerBlock = thinker
    ? '<div class="thinker-block"><strong>Изначальная идея:</strong> ' + thinker.name + ' (' + thinker.years + ') → ' + thinker.weapon + '</div>'
    : '';

  var downloadSection = '<div class="download-section">'
    + '<h3>Скачать материалы</h3>'
    + '<p>Хотите получить дополнительные материалы к этой статье? Оставьте заявку — мы сообщим, когда формат будет готов.</p>'
    + '<button class="btn download-btn" data-article="' + w.slug + '">Скачать</button>'
    + '<p class="download-feedback" style="display:none;margin-top:var(--space-3);color:var(--color-steel);font-size:var(--text-sm);"></p>'
    + '</div>';

  var related = weapons.filter(function(r) { return r.zone !== null && r.zone === w.zone && r.slug !== w.slug; });
  var relatedHtml = '';
  if (related.length > 0) {
    relatedHtml = '<h2 class="section-title" style="margin-top:var(--space-10);">В том же окопе</h2><div class="weapon-grid">'
      + related.slice(0, 4).map(function(r) {
        return '<a href="/weapons/' + r.slug + '/" class="weapon-card">'
          + '<div class="weapon-title">' + r.title + '</div>'
          + '<div class="weapon-subtitle">' + (r.subtitle || '') + '</div>'
          + '</a>';
      }).join('')
      + '</div>';
  }

  var html = weaponTemplate;
  html = html.replace(/{{title}}/g, w.title);
  html = html.replace('{{subtitle}}', w.subtitle || '');
  html = html.replace('{{zone_badge}}', zoneBadge);
  html = html.replace('{{status_badge}}', statusSpan);
  html = html.replace('{{content_body}}', contentBody);
  html = html.replace('{{thinker_block}}', thinkerBlock);
  html = html.replace('{{download_section}}', downloadSection);
  html = html.replace('{{related_weapons}}', relatedHtml);

  var canonicalUrl = SITE_URL + '/weapons/' + w.slug + '/';
  var zoneLabel = w.zone ? zoneLabels[w.zone] : null;
  write('weapons/' + w.slug + '/index.html', renderPage(w.title + ' | AntiManager', w.subtitle || '', html, { canonicalUrl: canonicalUrl, ogType: 'article', ogArticleSection: zoneLabel, structuredData: makeStructuredData('weapon', { title: w.title, subtitle: w.subtitle, canonicalUrl: canonicalUrl, articleSection: zoneLabel }) }));
  console.log('  ✓ ' + w.id + ' ' + w.slug);
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
write('favicon.svg', read('favicon.svg'));
write('og-image.svg', read('src/templates/og-image.svg'));
write('yandex_XXXXXXXXXXXXXXXX.html', '<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></head><body>Verification: XXXXXXXXXXXXXXXX</body></html>');

console.log('\n✅ Build complete. Output: ' + path.join(__dirname, 'dist') + '\n');
