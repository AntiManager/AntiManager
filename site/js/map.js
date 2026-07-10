(function() {
  'use strict';

  var RAY_CONFIG = {
    strategy:    { color: '#3A6EA5' },
    processes:   { color: '#D4711E' },
    information: { color: '#339999' },
    people:      { color: '#B34A6E' },
    adaptation:  { color: '#6B8C2E' },
  };

  var RAY_NAMES = {
    strategy:    'Стратегия и смысл',
    processes:   'Процессы и структура',
    information: 'Информация и данные',
    people:      'Люди и мотивация',
    adaptation:  'Изменения и адаптация',
  };

  var STATUS_LABELS = {
    published: { label: 'Опубликовано', cls: 'badge-green' },
    review:    { label: 'На ревью',     cls: 'badge-orange' },
    draft:     { label: 'Черновик',     cls: 'badge-gray' },
  };

  var chaptersData = [];

  function init() {
    var mapContainer = document.getElementById('systemMap');
    if (mapContainer) {
      var dataScript = document.getElementById('chaptersData');
      if (dataScript) {
        try { chaptersData = JSON.parse(dataScript.textContent); } catch(e) {}
      }
      setupRayClicks(mapContainer);
    }

    // Sidebar ray links — trigger ray selection on any page
    document.querySelectorAll('.ray-link').forEach(function(link) {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        var ray = this.dataset.ray;
        if (!ray) return;
        // If map exists, use it; otherwise navigate to home with hash
        if (mapContainer) {
          showRay(ray);
          document.getElementById('rayChapters').scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
          window.location.href = '/#ray-' + ray;
        }
      });
    });

    // Handle URL hash like /#ray-strategy on page load
    if (mapContainer && window.location.hash) {
      var hash = window.location.hash.replace('#ray-', '');
      if (RAY_NAMES[hash]) {
        setTimeout(function() { showRay(hash); }, 300);
      }
    }

    setupCardKeyboard();
  }

  function setupRayClicks(mapContainer) {
    document.querySelectorAll('.ray-group').forEach(function(group) {
      var ray = group.dataset.ray;

      // Keyboard accessibility: make ray groups focusable
      group.setAttribute('role', 'button');
      group.setAttribute('tabindex', '0');
      group.setAttribute('aria-label', 'Показать главы контура: ' + (RAY_NAMES[ray] || ray));

      group.addEventListener('click', function(e) {
        e.stopPropagation();
        if (ray) showRay(ray);
      });

      group.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          e.stopPropagation();
          if (ray) showRay(ray);
        }
      });

      group.addEventListener('mouseenter', function() {
        var lines = this.querySelectorAll('line');
        if (lines[0]) lines[0].setAttribute('stroke-width', '24'); // glow base 18 → 24
        if (lines[1]) lines[1].setAttribute('stroke-width', '5');  // flow base 3 → 5
      });

      group.addEventListener('mouseleave', function() {
        var lines = this.querySelectorAll('line');
        if (lines[0]) lines[0].setAttribute('stroke-width', '18'); // glow base
        if (lines[1]) lines[1].setAttribute('stroke-width', '3');  // flow base
      });
    });

    // Click on center hub to show all chapters (uses class instead of fragile coordinate selector)
    var hub = mapContainer.querySelector('.map-center-hub');
    if (hub) {
      hub.setAttribute('role', 'button');
      hub.setAttribute('tabindex', '0');
      hub.setAttribute('aria-label', 'Показать все главы');

      hub.addEventListener('click', function(e) {
        e.stopPropagation();
        showAllRays();
      });

      hub.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          e.stopPropagation();
          showAllRays();
        }
      });
    }

    // Also show all when clicking empty SVG area
    mapContainer.querySelector('svg').addEventListener('click', function(e) {
      if (e.target === this || e.target.tagName === 'svg') {
        showAllRays();
      }
    });
  }

  function setupCardKeyboard() {
    // Delegate keyboard handling for dynamically created cards
    document.getElementById('rayChapters').addEventListener('keydown', function(e) {
      var card = e.target.closest('.chapter-card');
      if (!card) return;
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        card.click();
      }
    });

    // Mark existing and future cards as interactive
    var observer = new MutationObserver(function() {
      document.querySelectorAll('#rayChapters .chapter-card').forEach(function(card) {
        if (!card.hasAttribute('role')) {
          card.setAttribute('role', 'button');
          card.setAttribute('tabindex', '0');
        }
      });
    });
    var container = document.getElementById('rayChapters');
    if (container) observer.observe(container, { childList: true, subtree: true });
  }

  function showRay(rayKey) {
    var ray = RAY_CONFIG[rayKey];
    if (!ray) return;

    // Highlight sidebar
    document.querySelectorAll('.ray-link').forEach(function(link) {
      link.classList.toggle('active', link.dataset.ray === rayKey);
    });

    // Highlight SVG ray: set active ray full-opacity, others dimmed
    document.querySelectorAll('.ray-group').forEach(function(g) {
      var isActive = g.dataset.ray === rayKey;
      g.style.opacity = isActive ? '1' : '0.3';
      var lines = g.querySelectorAll('line');
      if (isActive) {
        if (lines[0]) lines[0].setAttribute('stroke-width', '24');
        if (lines[1]) lines[1].setAttribute('stroke-width', '5');
      } else {
        if (lines[0]) lines[0].setAttribute('stroke-width', '18');
        if (lines[1]) lines[1].setAttribute('stroke-width', '3');
      }
    });

    var container = document.getElementById('rayChapters');
    if (!container) return;

    var chapters = chaptersData.filter(function(c) { return c.ray === rayKey; });
    if (!chapters.length) {
      container.innerHTML = '<p style="color:var(--color-text-tertiary);text-align:center;padding:var(--space-8)">В этом секторе пока нет глав.</p>';
      return;
    }

    var rayName = RAY_NAMES[rayKey] || rayKey;

    var html = '<div class="ray-chapters"><div class="ray-header" style="border-color:' + ray.color + '">';
    html += '<span class="ray-color" style="background:' + ray.color + '"></span>';
    html += '<h2>' + rayName + '</h2></div><div class="card-grid">';

    chapters.forEach(function(ch) {
      var st = STATUS_LABELS[ch.status] || { label: 'Черновик', cls: 'badge-gray' };
      html += '<div class="chapter-card" role="button" tabindex="0" aria-label="Открыть главу: ' + ch.title + '" onclick="window.location.href=\'/books/' + ch.slug + '/\'">';
      html += '<h4>' + ch.id + '. ' + ch.title + '</h4>';
      html += '<p>' + (ch.subtitle || '') + '</p>';
      html += '<div class="meta"><span class="badge ' + st.cls + '">' + st.label + '</span></div>';
      html += '</div>';
    });

    html += '</div></div>';
    container.innerHTML = html;
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function showAllRays() {
    // Reset all rays to default state
    document.querySelectorAll('.ray-group').forEach(function(g) {
      g.style.opacity = '1';
      var lines = g.querySelectorAll('line');
      if (lines[0]) lines[0].setAttribute('stroke-width', '18'); // reset glow
      if (lines[1]) lines[1].setAttribute('stroke-width', '3');  // reset flow
    });
    document.querySelectorAll('.ray-link').forEach(function(l) { l.classList.remove('active'); });

    var container = document.getElementById('rayChapters');
    if (!container) return;

    var html = '';
    var rayKeys = Object.keys(RAY_NAMES);
    rayKeys.forEach(function(key) {
      var chapters = chaptersData.filter(function(c) { return c.ray === key; });
      if (!chapters.length) return;
      var ray = RAY_CONFIG[key];
      var rayName = RAY_NAMES[key];
      html += '<div class="ray-chapters"><div class="ray-header" style="border-color:' + ray.color + '">';
      html += '<span class="ray-color" style="background:' + ray.color + '"></span>';
      html += '<h2>' + rayName + '</h2></div><div class="card-grid">';
      chapters.forEach(function(ch) {
        var st = STATUS_LABELS[ch.status] || { label: 'Черновик', cls: 'badge-gray' };
        html += '<div class="chapter-card" role="button" tabindex="0" aria-label="Открыть главу: ' + ch.title + '" onclick="window.location.href=\'/books/' + ch.slug + '/\'">';
        html += '<h4>' + ch.id + '. ' + ch.title + '</h4>';
        html += '<p>' + (ch.subtitle || '') + '</p>';
        html += '<div class="meta"><span class="badge ' + st.cls + '">' + st.label + '</span></div>';
        html += '</div>';
      });
      html += '</div></div>';
    });
    container.innerHTML = html;
  }

  document.addEventListener('DOMContentLoaded', init);
})();
