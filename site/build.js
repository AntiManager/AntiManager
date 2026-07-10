#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

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

function escapeScript(str) { return str.replace(/<\//g, '<\\/'); }

const SITE_URL = 'https://antimanager.pro';
const YM_COUNTER = '';

const RAYS = {
  strategy:    { key: 'strategy',    name: 'Стратегия\nи смысл',     color: '#3A6EA5', angle: 270 },
  processes:   { key: 'processes',   name: 'Процессы\nи структура',  color: '#D4711E', angle: 342 },
  information: { key: 'information', name: 'Информация\nи данные',   color: '#339999', angle: 54 },
  people:      { key: 'people',      name: 'Люди\nи мотивация',      color: '#B34A6E', angle: 126 },
  adaptation:  { key: 'adaptation',  name: 'Изменения\nи адаптация', color: '#6B8C2E', angle: 198 },
};

const STATUS_MAP = { published: { label: 'Опубликовано', badge: 'badge-green' }, review: { label: 'На ревью', badge: 'badge-orange' }, draft: { label: 'Черновик', badge: 'badge-gray' } };

const chapters = JSON.parse(read(path.join('src', 'data', 'chapters.json')));
const tools = JSON.parse(read(path.join('src', 'data', 'tools.json')));
const cases = JSON.parse(read(path.join('src', 'data', 'cases.json')));

const baseTemplate = read(path.join('src', 'templates', 'base.html'));
const chapterTemplate = read(path.join('src', 'templates', 'chapter.html'));
const headerHtml = read(path.join('src', 'components', 'header.html'));
const sidebarHtml = read(path.join('src', 'components', 'sidebar.html'));
const footerHtml = read(path.join('src', 'components', 'footer.html'));

const total = chapters.length;

function hasContentFile(ch) { return fs.existsSync(path.join(__dirname, 'src', 'content', ch.id + '-' + ch.slug + '.html')); }

function toolBadges(toolIds) {
  if (!toolIds || !toolIds.length) return '';
  return toolIds.map(id => { const t = tools.find(x => x.id === id); return t ? `<span class="badge badge-blue" style="font-size:var(--text-xs)">${t.name}</span>` : ''; }).join('');
}

function renderPage(title, description, content, opts = {}) {
  let html = baseTemplate;
  html = html.replace('{{title}}', title);
  html = html.replace('{{description}}', description);

  let canonical = opts.canonical || SITE_URL + '/';
  html = html.replace('{{canonical}}', `<link rel="canonical" href="${canonical}">`);

  let ogType = opts.og ? opts.og.type || 'website' : 'website';
  let ogTitle = opts.og ? opts.og.title || title : title;
  let ogDesc = opts.og ? opts.og.desc || description : description;
  let ogUrl = opts.og ? opts.og.url || canonical : canonical;
  let ogTags = `<meta property="og:title" content="${ogTitle}"><meta property="og:description" content="${ogDesc}"><meta property="og:url" content="${ogUrl}"><meta property="og:type" content="${ogType}"><meta property="og:site_name" content="AntiManager"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${ogTitle}"><meta name="twitter:description" content="${ogDesc}">`;
  html = html.replace('{{og_tags}}', ogTags);

  let noindex = opts.noindex;
  let jsonld = '';
  if (!noindex) {
    jsonld = `<script type="application/ld+json">${JSON.stringify({ '@context': 'https://schema.org', '@type': 'Article', headline: ogTitle, description: ogDesc, url: ogUrl })}</script>`;
  }
  html = html.replace('{{jsonld}}', jsonld);

  let metrika = '';
  if (YM_COUNTER) {
    metrika = '<script>window.AM_METRIKA_ID=' + JSON.stringify(YM_COUNTER) + ';(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};m[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){if(document.scripts[j].src===r){return;}}k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})(window,document,"script","https://mc.yandex.ru/metrika/tag.js","ym");ym(' + JSON.stringify(YM_COUNTER) + ',"init",{clickmap:true,trackLinks:true,accurateTrackBounce:true,webvisor:false});</script>\n<noscript><div><img src="https://mc.yandex.ru/watch/' + YM_COUNTER + '" style="position:absolute;left:-9999px;" alt=""/></div></noscript>';
  }
  html = html.replace('{{metrika}}', metrika);

  html = html.replace('{{head_extra}}', opts.headExtra || '');
  html = html.replace('{{body_class}}', opts.bodyClass ? ' class="' + opts.bodyClass + '"' : '');
  html = html.replace('{{header}}', headerHtml);
  html = html.replace('{{sidebar}}', sidebarHtml);
  html = html.replace('{{content}}', content);
  html = html.replace('{{footer}}', footerHtml);
  html = html.replace('{{scripts}}', opts.scripts || '');

  if (noindex) html = html.replace('<meta name="robots" content="noindex">', '').replace('</head>', '<meta name="robots" content="noindex"></head>');
  return html;
}

function buildChapter(ch) {
  const ray = RAYS[ch.ray];
  if (!ray) { console.warn('  ⚠ Unknown ray: ' + ch.ray + ' for chapter ' + ch.id); return; }
  const st = STATUS_MAP[ch.status] || STATUS_MAP.draft;
  const contentPath = path.join(__dirname, 'src', 'content', ch.id + '-' + ch.slug + '.html');
  const hasContent = fs.existsSync(contentPath);

  let contentBody = '';
  if (hasContent) { contentBody = fs.readFileSync(contentPath, 'utf-8'); }
  else { contentBody = `<div class="empty-state"><h3>Глава в разработке</h3><p>Эта глава ещё не готова. Скоро здесь появится полный текст.</p><p style="margin-top:var(--space-4);"><a href="/catalog/" class="btn btn-outline">← Вернуться к каталогу</a></p></div>`; }

  let chapterHtml = chapterTemplate;
  chapterHtml = chapterHtml.replace(/{{ray}}/g, ch.ray);
  chapterHtml = chapterHtml.replace('{{ray_name}}', ray.name);
  chapterHtml = chapterHtml.replace(/{{title}}/g, ch.title);
  chapterHtml = chapterHtml.replace('{{subtitle}}', ch.subtitle || '');
  chapterHtml = chapterHtml.replace('{{status_badge}}', st.badge);
  chapterHtml = chapterHtml.replace('{{status_label}}', st.label);
  chapterHtml = chapterHtml.replace('{{tools_badges}}', toolBadges(ch.tools));
  chapterHtml = chapterHtml.replace('{{content_body}}', contentBody);
  chapterHtml = chapterHtml.replace('{{slug}}', ch.slug);

  const downloadSection = hasContent
    ? `<section class="download-section" style="margin:var(--space-10) 0;padding:var(--space-6);background:var(--layer-surface);border-radius:var(--radius-lg);border:1px solid var(--color-border-light);text-align:center;"><h3 style="margin-bottom:var(--space-2)">Полный формат главы</h3><p style="margin-bottom:var(--space-4);max-width:480px;margin-left:auto;margin-right:auto;">Хотите получить полную версию главы с дополнительными материалами? Оставьте заявку — мы сообщим, когда формат будет готов.</p><button class="btn btn-primary download-btn" data-chapter="${ch.slug}">Скачать полный формат</button><p class="download-feedback text-sm text-muted" style="display:none;margin-top:var(--space-3);"></p></section>`
    : '';
  chapterHtml = chapterHtml.replace('{{download_section}}', downloadSection);

  const rayName = ray.name;
  const scripts = '<script>\n' +
    '    const CHAPTER_DATA = ' + escapeScript(JSON.stringify(ch)) + ';\n' +
    '    const RELATED_CHAPTERS = ' + escapeScript(JSON.stringify(chapters.filter(c => c.ray === ch.ray && c.id !== ch.id))) + ';\n' +
    '    document.addEventListener(\'DOMContentLoaded\', function(){\n' +
    '      var grid = document.getElementById(\'relatedChapters\');\n' +
    '      if(!grid) return;\n' +
    '      if (RELATED_CHAPTERS.length === 0) { grid.parentNode.style.display = \'none\'; return; }\n' +
    '      RELATED_CHAPTERS.forEach(function(c){\n' +
    '        var card = document.createElement(\'div\');\n' +
    '        card.className = \'chapter-card\';\n' +
    '        card.setAttribute(\'role\', \'button\');\n' +
    '        card.setAttribute(\'tabindex\', \'0\');\n' +
    '        card.setAttribute(\'aria-label\', \'Открыть главу \' + c.title);\n' +
    '        card.innerHTML = \'<h4>\' + c.title + \'</h4><p>\' + (c.subtitle || \'\') + \'</p><div class="meta"><span class="badge badge-ray-\' + c.ray + \'">' + rayName + '</span></div>\';\n' +
    '        card.addEventListener(\'click\', function(){ window.location.href = \'/books/\' + c.slug + \'/\'; });\n' +
    '        card.addEventListener(\'keydown\', function(e){ if(e.key === \'Enter\' || e.key === \' \') { e.preventDefault(); window.location.href = \'/books/\' + c.slug + \'/\'; } });\n' +
    '        grid.appendChild(card);\n' +
    '      });\n' +
    '    });\n' +
    '  </script>';

  const titlePage = ch.title + ' | AntiManager';
  const page = renderPage(titlePage, ch.subtitle || 'Глава ' + ch.id + ' системы управления производством', chapterHtml, {
    scripts, bodyClass: 'content-page' + (hasContent ? '' : ' noindex'),
    canonical: SITE_URL + '/books/' + ch.slug + '/',
    og: { type: 'article', title: titlePage, desc: ch.subtitle || '' },
    noindex: !hasContent
  });
  write(path.join('books', ch.slug, 'index.html'), page);
  console.log('  ✓ ' + ch.id + ' ' + ch.slug);
}

function starSvg() {
  const CX = 300, CY = 300, R = 220;
  let chByRay = {};
  Object.values(RAYS).forEach(function(r){ chByRay[r.key] = chapters.filter(function(c){ return c.ray === r.key; }); });
  let svg = '<svg viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Карта системы управления: пять контуров. Нажмите на луч, чтобы увидеть главы." style="width:100%;max-width:600px;height:auto;">';
  svg += '<circle cx="' + CX + '" cy="' + CY + '" r="' + (R+50) + '" fill="none" stroke="var(--color-border-light)" stroke-width="1" stroke-dasharray="4 4"/>';

  Object.values(RAYS).forEach(function(r, ri){
    const rad = r.angle * Math.PI / 180;
    const ex = CX + R * Math.cos(rad);
    const ey = CY + R * Math.sin(rad);
    const chaptersInRay = chByRay[r.key] || [];
    const delay = ri * 0.3;
    svg += '<g class="ray-group" data-ray="' + r.key + '" style="cursor:pointer;">';
    svg += '<line x1="' + CX + '" y1="' + CY + '" x2="' + ex + '" y2="' + ey + '" stroke="' + r.color + '" stroke-width="18" stroke-linecap="round" opacity="0.15"/>';
    svg += '<line x1="' + CX + '" y1="' + CY + '" x2="' + ex + '" y2="' + ey + '" stroke="' + r.color + '" stroke-width="3" stroke-linecap="round" opacity="0.4" class="ray-flow" style="animation-delay:' + delay + 's"/>';

    for (let pi = 0; pi < 3; pi++) {
      const pt = 0.15 + pi * 0.25;
      const px = CX + pt * R * Math.cos(rad);
      const py = CY + pt * R * Math.sin(rad);
      const pDelay = delay + pi * 0.4;
      svg += '<circle cx="' + px + '" cy="' + py + '" r="3" fill="' + r.color + '" class="ray-particle" style="animation-delay:' + pDelay + 's"/>';
    }

    const labelParts = r.name.split('\n');
    svg += '<text x="' + ex + '" y="' + ey + '" fill="' + r.color + '" font-family="var(--font-heading)" font-weight="700" font-size="14" text-anchor="middle">' + labelParts[0] + '</text>';
    if (labelParts.length > 1) {
      svg += '<text x="' + ex + '" y="' + (ey + 16) + '" fill="' + r.color + '" font-family="var(--font-sans)" font-weight="500" font-size="11" text-anchor="middle" opacity="0.8">' + labelParts[1] + '</text>';
    }
    if (chaptersInRay.length > 0) {
      svg += '<circle cx="' + (ex - 8) + '" cy="' + (ey + 28) + '" r="10" fill="' + r.color + '"/>';
      svg += '<text x="' + (ex - 8) + '" y="' + (ey + 32) + '" fill="white" font-family="var(--font-heading)" font-weight="700" font-size="10" text-anchor="middle">' + chaptersInRay.length + '</text>';
    }
    chaptersInRay.forEach(function(ch, i){
      const t = (i + 1) / (chaptersInRay.length + 1);
      const dx = CX + (R * 0.5 * t) * Math.cos(rad);
      const dy = CY + (R * 0.5 * t) * Math.sin(rad);
      svg += '<circle cx="' + dx + '" cy="' + dy + '" r="4" fill="' + r.color + '" opacity="0.6"/>';
    });
    svg += '</g>';
  });
  svg += '<circle class="map-center-hub" cx="' + CX + '" cy="' + CY + '" r="45" fill="var(--layer-surface)" stroke="var(--color-tertiary)" stroke-width="3"/>';
  svg += '<text x="' + CX + '" y="' + (CY - 6) + '" fill="var(--color-text)" font-family="var(--font-heading)" font-weight="800" font-size="13" text-anchor="middle">СИСТЕМА</text>';
  svg += '<text x="' + CX + '" y="' + (CY + 10) + '" fill="var(--color-text-secondary)" font-family="var(--font-sans)" font-weight="500" font-size="9" text-anchor="middle">УПРАВЛЕНИЯ</text>';
  svg += '</svg>';
  return svg;
}

function buildIndex() {
  const chaptersJson = escapeScript(JSON.stringify(chapters));
  const toolsJson = escapeScript(JSON.stringify(tools));
  const casesJson = escapeScript(JSON.stringify(cases));

  const content = `
    <section class="hero-full">
      <div class="main-inner">
        <h1>Система управления производством<br>в 5 контурах</h1>
        <p style="font-size:var(--text-lg);max-width:600px;margin:0 auto var(--space-6);">Главы, инструменты и кейсы — не разрозненные техники, а единая связанная система для руководителя производства.</p>
        <div style="display:flex;gap:var(--space-3);justify-content:center;flex-wrap:wrap;">
          <a href="#systemMap" class="btn btn-primary">Исследовать карту →</a>
          <a href="/catalog/" class="btn btn-outline" style="border-color:white;color:white;">Смотреть каталог</a>
        </div>
        <div style="display:flex;gap:var(--space-6);justify-content:center;margin-top:var(--space-8);flex-wrap:wrap;">
          <div style="text-align:center;"><strong style="font-size:var(--text-3xl);color:white;">${total}</strong><br><span style="font-size:var(--text-sm);color:hsla(220,15%,80%,0.8);">глав</span></div>
          <div style="text-align:center;"><strong style="font-size:var(--text-3xl);color:white;">${tools.length}</strong><br><span style="font-size:var(--text-sm);color:hsla(220,15%,80%,0.8);">инструментов</span></div>
          <div style="text-align:center;"><strong style="font-size:var(--text-3xl);color:white;">${cases.length}</strong><br><span style="font-size:var(--text-sm);color:hsla(220,15%,80%,0.8);">кейсов</span></div>
          <div style="text-align:center;"><strong style="font-size:var(--text-3xl);color:white;">${chapters.filter(function(c){return c.status === 'published'}).length}</strong><br><span style="font-size:var(--text-sm);color:hsla(220,15%,80%,0.8);">опубликовано</span></div>
        </div>
      </div>
    </section>
    <div class="main-inner">
      <section style="text-align:center;margin:var(--space-12) 0;">
        <h2>Карта системы</h2>
        <p style="margin-bottom:var(--space-6);">Пять управленческих контуров. Нажмите на луч — увидите главы и инструменты.</p>
        <div class="map-container" id="systemMap">${starSvg()}</div>
        <div id="rayChapters" style="margin-top:var(--space-6);"></div>
      </section>
      <section style="margin:var(--space-12) 0;">
        <h2 style="text-align:center;margin-bottom:var(--space-6);">Для кого эта система</h2>
        <div class="card-grid">
          <div class="chapter-card" style="text-align:center;">
            <div style="font-size:var(--text-4xl);margin-bottom:var(--space-3);color:var(--ray-strategy);">▣</div>
            <h3>Директору завода</h3>
            <p>Стратегия, каскадирование целей, антикризис, культура</p>
          </div>
          <div class="chapter-card" style="text-align:center;">
            <div style="font-size:var(--text-4xl);margin-bottom:var(--space-3);color:var(--ray-processes);">▦</div>
            <h3>Начальнику цеха</h3>
            <p>Процессы, OEE, ситуационное развитие, работа с хаосом</p>
          </div>
          <div class="chapter-card" style="text-align:center;">
            <div style="font-size:var(--text-4xl);margin-bottom:var(--space-3);color:var(--ray-people);">◈</div>
            <h3>HR и консультанту</h3>
            <p>Диагностика, JDR, культурный код, мотивация</p>
          </div>
        </div>
      </section>
    </div>
  `;

  const scripts = `<script id="chaptersData" type="application/json">${chaptersJson}</script><script src="/js/map.js"></script>`;

  const page = renderPage(
    'AntiManager — Система управления производством',
    `Интерактивная карта системы управления: 5 контуров, ${total} глав, ${tools.length} инструментов. Для руководителей производства.`,
    content,
    { headExtra: '', scripts, canonical: SITE_URL, og: { type: 'website', title: 'AntiManager — Система управления производством', desc: `Интерактивная карта: 5 контуров, ${total} глав` } }
  );
  write('index.html', page);
  console.log('  ✓ index (главная с картой)');
}

function buildCatalog() {
  const parts = [
    { id: 0, name: 'Пролог' },
    { id: 1, name: 'I. Диагностика' },
    { id: 2, name: 'II. Стратегия' },
    { id: 3, name: 'III. Операции' },
    { id: 4, name: 'IV. Люди' },
    { id: 5, name: 'V. Кризис и адаптация' },
    { id: 6, name: 'VI. Развитие и смысл' },
  ];

  let html = '<h1>Каталог глав</h1><p>Все ' + chapters.length + ' глав, сгруппированные по разделам книги.</p>';
  html += '<div class="filters" id="catalogFilters">';
  html += '<button class="filter-btn active" data-filter="all">Все</button>';
  html += Object.entries(RAYS).map(([k, v]) => `<button class="filter-btn" data-filter="${k}">${v.name}</button>`).join('');
  html += '</div>';
  html += '<div id="catalogGrid">';

  for (const part of parts) {
    const partChapters = chapters.filter(c => c.part === part.id);
    if (!partChapters.length) continue;
    html += `<div class="catalog-section"><h2 style="margin-top:var(--space-8);padding-bottom:var(--space-2);border-bottom:3px solid var(--color-tertiary);display:inline-block;">${part.name}</h2><div class="card-grid">`;
    for (const ch of partChapters) {
      const st = STATUS_MAP[ch.status] || STATUS_MAP.draft;
      html += `<div class="chapter-card" data-ray="${ch.ray}" data-roles="${ch.roles.join(',')}" data-status="${ch.status}" data-slug="${ch.slug}" role="button" tabindex="0" aria-label="Открыть главу: ${ch.id}. ${ch.title}">
        <div class="meta"><span class="badge badge-ray-${ch.ray}" style="font-size:var(--text-xs)">${RAYS[ch.ray].name}</span></div>
        <h3>${ch.id}. ${ch.title}</h3>
        <p>${ch.subtitle || ''}</p>
        <div class="meta"><span class="badge ${st.badge}">${st.label}</span></div>
      </div>`;
    }
    html += '</div></div>';
  }
  html += '</div>';

  const scripts = `<script>
    document.addEventListener('DOMContentLoaded', function(){
      const filters = document.querySelectorAll('#catalogFilters .filter-btn');
      const cards = document.querySelectorAll('#catalogGrid .chapter-card');
      const sections = document.querySelectorAll('#catalogGrid .catalog-section');
      filters.forEach(function(btn){
        btn.addEventListener('click', function(){
          filters.forEach(function(b){b.classList.remove('active');});
          this.classList.add('active');
          const f = this.dataset.filter;
          sections.forEach(function(section){
            const sectionCards = section.querySelectorAll('.chapter-card');
            let hasVisible = false;
            sectionCards.forEach(function(c){
              if(f === 'all' || c.dataset.ray === f) { c.style.display = ''; hasVisible = true; }
              else { c.style.display = 'none'; }
            });
            section.style.display = hasVisible ? '' : 'none';
          });
        });
      });
      cards.forEach(function(c){
        c.addEventListener('click', function(){ const slug = this.dataset.slug; if (slug) { window.location.href = '/books/' + slug + '/'; } });
        c.addEventListener('keydown', function(e){ if(e.key === 'Enter' || e.key === ' ') { e.preventDefault(); const slug = this.dataset.slug; if(slug) window.location.href = '/books/' + slug + '/'; } });
      });
    });
  </script>`;

  const page = renderPage('Каталог глав | AntiManager', 'Все ' + chapters.length + ' глав системы управления производством', html, { scripts, bodyClass: 'content-page', canonical: SITE_URL + '/catalog/', og: { type: 'website', title: 'Каталог глав | AntiManager', desc: 'Все ' + chapters.length + ' глав системы управления производством' } });
  write(path.join('catalog', 'index.html'), page);
  console.log('  ✓ catalog');
}

function buildAbout() {
  const manifestRu = `
    <div class="manifesto" lang="ru" id="manifesto-ru">
      <p class="manifesto-preamble">Мы — инженеры человеческих управленческих систем, архитекторы порядка и гаранты справедливости. Мы больше не «менеджеры» в старом смысле этого слова. Наша задача — проектировать и запускать социальные машины, которые раскрывают потенциал каждого для достижения общих целей.</p>
      <h2>10 ценностей — выбор в пользу развития, а не догмы</h2>
      <ol class="manifesto-values">
        <li><strong>Люди и их потенциал</strong> над слепым исполнением инструкций.</li>
        <li><strong>Работающая и справедливая система</strong> над героизмом и авралами.</li>
        <li><strong>Сотрудничество и доверие</strong> над тотальным контролем и подозрительностью.</li>
        <li><strong>Постоянное улучшение процессов</strong> над поиском виноватых.</li>
        <li><strong>Смысл и осознанность</strong> над слепым следованием трендам.</li>
        <li><strong>Прозрачность и конституция</strong> над устными указаниями и кулуарными решениями.</li>
        <li><strong>Ментальное здоровье</strong> над когнитивным перегрузом.</li>
        <li><strong>Конфликт мнений</strong> над уютным консенсусом.</li>
        <li><strong>Антихрупкость</strong> над хрупкой эффективностью.</li>
        <li><strong>Открытая политика</strong> над неформальной властью.</li>
      </ol>
      <h2>Принципы — правила нашей повседневной практики</h2>
      <ol class="manifesto-principles" start="1">
        <li>Наша высшая цель — построить самовоспроизводящуюся систему, которая стабильно даёт результат, даже когда нас нет на месте.</li>
        <li>Мы выходим в <em>гембу</em> не для того, чтобы найти виноватых, а чтобы понять и улучшить процесс.</li>
        <li>Мы — гаранты конституции. Наша роль — защищать правила игры для всех, включая себя.</li>
        <li>Мы создаём среду, где любая проблема может быть озвучена без страха.</li>
        <li>Мы платим за вклад и результат, а не за время, проведённое на работе.</li>
        <li>Мы платим и за результат, и за смелость остановить сломанный процесс.</li>
        <li>Мы инвестируем в развитие «сообразительных умов», а не эксплуатируем «тёплые тела».</li>
        <li>Мы строим конкретные пути роста, а не учим «вообще полезному».</li>
        <li>Настоящая команда — когда каждый так делает свою работу, что другим легко делать свою.</li>
        <li>Мы не ждём и не догоняем — сами задаём стандарты в своей отрасли.</li>
        <li>Люди проводят на работе большую часть жизни — мы строим место силы и уважения.</li>
        <li>Мы относимся к кулуарным решениям как к симптому загнивания системы.</li>
        <li>Любой кризис — стресс-тест правил. Нарушил правило в кризисе — измени правило.</li>
        <li>Мы защищаем фокус команды: нововведение внедряется взамен старого.</li>
        <li>Мы постоянно совершенствуем архитектуру управления, соизмеряя с нашими ценностями.</li>
      </ol>
      <div class="manifesto-closing"><p>Мы призываем лидеров принять эту эволюционную парадигму. Оставить в прошлом эпоху надсмотрщиков и вступить в эру инженеров человеческих управленческих систем. Наш инструмент — не приказ, а конституция. Наша сила — не в героях-одиночках, а в системе, которая тиражирует героизм как стандартную практику.</p><p>Этот манифест — живой документ. Для тех, кто готов брать на себя ответственность за созидание порядка из хаоса.</p></div>
    </div>`;

  const manifestEn = `
    <div class="manifesto" lang="en" id="manifesto-en" style="display:none">
      <p class="manifesto-preamble">We are the engineers of human management systems, the architects of order, and the guarantors of justice. We are no longer "managers" in the old sense of the word. Our task is to design and launch social machines that unlock each individual's potential to achieve common goals.</p>
      <h2>10 Values — A Choice for Evolution, Not Dogma</h2>
      <ol class="manifesto-values">
        <li><strong>People and their potential</strong> over blind adherence to instructions.</li>
        <li><strong>A working and fair system</strong> over heroism and firefighting.</li>
        <li><strong>Collaboration and trust</strong> over total control and suspicion.</li>
        <li><strong>Continuous process improvement</strong> over blame-seeking.</li>
        <li><strong>Meaning and intentionality</strong> over blind trend-following.</li>
        <li><strong>Transparency and constitution</strong> over oral directives and backroom decisions.</li>
        <li><strong>Mental health</strong> over cognitive overload.</li>
        <li><strong>Conflict of opinions</strong> over comfortable consensus.</li>
        <li><strong>Antifragility</strong> over fragile efficiency.</li>
        <li><strong>Open politics</strong> over informal power.</li>
      </ol>
      <h2>Principles — The Rules of Our Daily Practice</h2>
      <ol class="manifesto-principles" start="1">
        <li>Our ultimate goal is to build a self-sustaining system that delivers results consistently, even in our absence.</li>
        <li>We go to the <em>gemba</em> not to find someone to blame, but to understand and improve the process.</li>
        <li>We are the guarantors of the constitution — protecting the rules of the game for all, including ourselves.</li>
        <li>We create an environment where any problem can be voiced without fear.</li>
        <li>We pay for contribution and results, not for time spent at work.</li>
        <li>We pay for both results and the courage to stop a broken process.</li>
        <li>We invest in developing "capable minds," not exploiting "warm bodies."</li>
        <li>We build concrete growth paths, not teach "generally useful" things.</li>
        <li>A real team is when everyone does their work so well that others can do theirs easily.</li>
        <li>We don't wait or catch up — we set the standards within our industry.</li>
        <li>People spend most of their lives at work — we build a place of strength and respect.</li>
        <li>We treat backroom decisions as a symptom of a decaying system.</li>
        <li>Any crisis is a stress test for the rules. Break a rule in a crisis — change the rule.</li>
        <li>We protect the team's focus: any new implementation must replace something old.</li>
        <li>We continuously refine our management architecture, aligning with our values.</li>
      </ol>
      <div class="manifesto-closing"><p>We call on leaders to embrace this evolutionary paradigm — to leave the era of overseers and enter the era of engineers of human management systems. Our tool is not an order, but a constitution. Our strength is not in lone heroes, but in a system that replicates heroism as a standard practice.</p><p>This manifesto is a living document. It is for those ready to take responsibility for creating order out of chaos.</p></div>
    </div>`;

  const content = `
    <h1>AntiManager Manifesto</h1>
    <p class="text-muted" style="margin-bottom:var(--space-4);">Manifestum Imperii Rationalis — Манифест рационального управления</p>
    <div class="lang-switch" style="display:flex;gap:var(--space-2);margin-bottom:var(--space-8);">
      <button class="filter-btn active" id="langRu" onclick="switchLang('ru')">Русский</button>
      <button class="filter-btn" id="langEn" onclick="switchLang('en')">English</button>
    </div>
    ${manifestRu}${manifestEn}
    <hr style="margin:var(--space-10) 0;border-color:var(--color-border-light);">
    <script>function switchLang(lang){document.getElementById('langRu').classList.toggle('active',lang==='ru');document.getElementById('langEn').classList.toggle('active',lang==='en');document.getElementById('manifesto-ru').style.display=lang==='ru'?'':'none';document.getElementById('manifesto-en').style.display=lang==='en'?'':'none';}</script>`;

  const page = renderPage('AntiManager Manifesto | AntiManager', 'Manifestum Imperii Rationalis — Манифест рационального управления', content, { bodyClass: 'content-page', canonical: SITE_URL + '/about/', og: { type: 'article', title: 'AntiManager Manifesto', desc: 'Manifestum Imperii Rationalis — 10 ценностей и 15 принципов рационального управления' } });
  write(path.join('about', 'index.html'), page);
  console.log('  ✓ about (manifesto RU/EN)');
}

function buildTools() {
  let html = '<h1>Инструменты</h1><p>' + tools.length + ' инструментов управления производством.</p><div class="filters" id="toolFilters">';
  html += '<button class="filter-btn active" data-filter="all">Все</button>';
  html += Object.entries(RAYS).map(([k, v]) => `<button class="filter-btn" data-filter="${k}">${v.name}</button>`).join('');
  html += '</div><div class="card-grid" id="toolGrid">';
  for (const t of tools) {
    html += `<div class="chapter-card" data-rays="${t.rays.join(',')}" style="cursor:default;">
      <div class="meta"><span class="badge badge-ray-${t.rays[0]}" style="font-size:var(--text-xs)">${RAYS[t.rays[0]].name}</span></div>
      <h3>${t.name}</h3><p>${t.desc || ''}</p></div>`;
  }
  html += '</div>';

  const scripts = `<script>
    document.addEventListener('DOMContentLoaded', function(){
      const filters = document.querySelectorAll('#toolFilters .filter-btn');
      const cards = document.querySelectorAll('#toolGrid .chapter-card');
      filters.forEach(function(b){b.addEventListener('click', function(){
        filters.forEach(function(f){f.classList.remove('active');});
        this.classList.add('active'); const f=this.dataset.filter;
        cards.forEach(function(c){if(f==='all'||c.dataset.rays.includes(f))c.style.display='';else c.style.display='none';});
      });});
    });
  </script>`;

  const page = renderPage('Инструменты | AntiManager', tools.length + ' инструментов управления производством', html, { scripts, bodyClass: 'content-page', canonical: SITE_URL + '/tools/', og: { type: 'website', title: 'Инструменты | AntiManager', desc: tools.length + ' инструментов управления производством' } });
  write(path.join('tools', 'index.html'), page);
  console.log('  ✓ tools');
}

function buildPrivacy() {
  const content = `<h1>Политика конфиденциальности</h1><p>Мы не собираем персональные данные пользователей. Сайт использует только технические файлы cookie, необходимые для работы. Данные о посещениях (Яндекс.Метрика) обезличены и используются для статистики.</p><p>Если у вас есть вопросы — свяжитесь с нами.</p>`;
  const page = renderPage('Политика конфиденциальности | AntiManager', 'Политика конфиденциальности', content, { bodyClass: 'content-page', canonical: SITE_URL + '/privacy/' });
  write(path.join('privacy', 'index.html'), page);
  console.log('  ✓ privacy');
}

function build404() {
  const content = `<div class="empty-state"><h1>404</h1><p>Страница не найдена.</p><p><a href="/" class="btn btn-outline">← На главную</a></p></div>`;
  const page = renderPage('404 — Страница не найдена | AntiManager', 'Страница не найдена', content, { bodyClass: 'content-page', noindex: true });
  write(path.join('404', 'index.html'), page);
  console.log('  ✓ 404');
}

function generateSitemap() {
  const urls = [];
  urls.push({ loc: SITE_URL + '/', priority: '1.0' });
  urls.push({ loc: SITE_URL + '/catalog/', priority: '0.8' });
  urls.push({ loc: SITE_URL + '/tools/', priority: '0.7' });
  for (const ch of chapters) { if (hasContentFile(ch)) urls.push({ loc: SITE_URL + '/books/' + ch.slug + '/', priority: '0.9' }); }
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';
  for (const u of urls) xml += '  <url>\n    <loc>' + u.loc + '</loc>\n    <priority>' + u.priority + '</priority>\n  </url>\n';
  xml += '</urlset>';
  write('sitemap.xml', xml);
  console.log('  ✓ sitemap.xml');
}

function generateRobots() {
  const robots = 'User-agent: *\nAllow: /\n\nSitemap: ' + SITE_URL + '/sitemap.xml\n';
  write('robots.txt', robots);
  console.log('  ✓ robots.txt');
}

// --- MAIN ---
console.log('\n🚀 AntiManager Build\n');

for (const ch of chapters) buildChapter(ch);

buildIndex();
buildCatalog();
buildTools();
buildAbout();
buildPrivacy();
build404();

generateSitemap();
generateRobots();

console.log('\n📁 Copying assets...');
copyDir('css', 'css');
copyDir('js', 'js');
copyDir('fonts', 'fonts');

console.log('\n✅ Build complete. Output: ' + path.join(__dirname, 'dist') + '\n');
