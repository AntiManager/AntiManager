// AntiManager — site search (Pagefind).
// The index bundle is imported only when the dialog first opens, so a page view
// does not pay for the WASM reader until the visitor actually searches.

const RESULT_LIMIT = 10;

function plural(n, one, few, many) {
  var mod10 = n % 10;
  var mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}

function initSearch() {
  var dialog = document.getElementById('site-search');
  if (!dialog || typeof dialog.showModal !== 'function') return;

  var form = dialog.querySelector('[data-search-form]');
  var input = dialog.querySelector('[data-search-input]');
  var resultsList = dialog.querySelector('[data-search-results]');
  var statusEl = dialog.querySelector('[data-search-status]');
  var emptyEl = dialog.querySelector('[data-search-empty]');
  var closeBtn = dialog.querySelector('[data-search-close]');
  var triggers = Array.prototype.slice.call(document.querySelectorAll('[data-search-open]'));

  var pagefind = null;
  var pagefindFailed = false;
  var seq = 0;
  var timer = 0;
  var trigger = null;

  function setExpanded(value) {
    triggers.forEach(function(t) { t.setAttribute('aria-expanded', String(value)); });
  }

  function loadPagefind() {
    if (pagefind) return Promise.resolve(pagefind);
    if (pagefindFailed) return Promise.resolve(null);
    return import('/pagefind/pagefind.js').then(function(mod) {
      pagefind = mod;
      if (typeof mod.options === 'function') {
        return mod.options({ excerptLength: 26 }).then(function() { return mod; });
      }
      return mod;
    }).catch(function() {
      pagefindFailed = true;
      statusEl.textContent = 'Поиск временно недоступен. Откройте плейбук или методологию.';
      return null;
    });
  }

  function resetResults() {
    seq += 1;
    lastQuery = '';
    if (resultsList) resultsList.textContent = '';
    if (statusEl) statusEl.textContent = '';
    if (emptyEl) emptyEl.hidden = true;
  }

  var lastQuery = '';

  function open(query) {
    if (!dialog.open) {
      var active = document.activeElement;
      trigger = active && active.matches && active.matches('[data-search-open]') ? active : (triggers[0] || null);
      dialog.showModal();
      setExpanded(true);
      document.body.classList.add('search-open');
      document.dispatchEvent(new CustomEvent('am:search-open', { detail: { path: window.location.pathname } }));
    }
    if (typeof query === 'string') {
      input.value = query;
      if (query.trim()) run(query.trim());
      else resetResults();
    }
    input.focus();
  }

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function render(items, total) {
    resultsList.textContent = '';
    document.dispatchEvent(new CustomEvent('am:search-query', { detail: { query: lastQuery, total: total } }));
    if (!items.length) {
      setStatus('');
      if (emptyEl) emptyEl.hidden = false;
      return;
    }
    if (emptyEl) emptyEl.hidden = true;
    var shown = Math.min(total, RESULT_LIMIT);
    setStatus('Найдено ' + total + ' ' + plural(total, 'результат', 'результата', 'результатов')
      + (total > RESULT_LIMIT ? ' · показаны первые ' + shown : ''));

    items.forEach(function(item) {
      var li = document.createElement('li');
      li.className = 'search-result';

      var link = document.createElement('a');
      link.className = 'search-result-link';
      link.href = item.url;

      var meta = document.createElement('span');
      meta.className = 'search-result-meta';
      var type = (item.meta && item.meta.type) || 'Страница';
      var section = (item.meta && item.meta.section) || '';
      meta.textContent = section ? type + ' · ' + section : type;

      var title = document.createElement('span');
      title.className = 'search-result-title';
      title.textContent = (item.meta && item.meta.title) || item.url;

      link.appendChild(meta);
      link.appendChild(title);

      if (item.meta && item.meta.subtitle) {
        var sub = document.createElement('span');
        sub.className = 'search-result-sub';
        sub.textContent = item.meta.subtitle;
        link.appendChild(sub);
      }

      if (item.excerpt) {
        var excerpt = document.createElement('span');
        excerpt.className = 'search-result-excerpt';
        excerpt.innerHTML = item.excerpt;
        link.appendChild(excerpt);
      }

      li.appendChild(link);
      resultsList.appendChild(li);
    });
  }

  function run(query) {
    if (!query || query === lastQuery) return;
    lastQuery = query;
    var current = ++seq;
    setStatus('Ищем…');
    if (emptyEl) emptyEl.hidden = true;

    loadPagefind().then(function(mod) {
      if (!mod) return null;
      return mod.search(query).catch(function() {
        if (current === seq) setStatus('Поиск временно недоступен.');
        return null;
      });
    }).then(function(search) {
      if (!search || current !== seq) return null;
      var slice = search.results.slice(0, RESULT_LIMIT);
      return Promise.all(slice.map(function(result) { return result.data(); })).then(function(data) {
        if (current !== seq) return;
        render(data, search.results.length);
      });
    });
  }

  function moveFocus(step) {
    var links = resultsList.querySelectorAll('a');
    if (!links.length) return;
    var current = Array.prototype.indexOf.call(links, document.activeElement);
    var next = current + step;
    if (next < 0) next = links.length - 1;
    if (next >= links.length) next = 0;
    links[next].focus();
  }

  triggers.forEach(function(t) {
    t.addEventListener('click', function(e) {
      e.preventDefault();
      open();
    });
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', function() { dialog.close(); });
  }

  dialog.addEventListener('close', function() {
    setExpanded(false);
    document.body.classList.remove('search-open');
    if (trigger && typeof trigger.focus === 'function') trigger.focus();
  });

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    var query = input.value.trim();
    if (!query) return;
    if (window.location.pathname === '/search/' && window.history.replaceState) {
      var url = new URL(window.location.href);
      url.searchParams.set('q', query);
      window.history.replaceState(null, '', url);
    }
    run(query);
  });

  input.addEventListener('input', function() {
    var query = input.value.trim();
    if (timer) clearTimeout(timer);
    if (!query) {
      resetResults();
      return;
    }
    if (query.length < 2) return;
    timer = setTimeout(function() { run(query); }, 180);
  });

  input.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      var links = resultsList.querySelectorAll('a');
      if (!links.length) return;
      e.preventDefault();
      if (e.key === 'ArrowDown') links[0].focus();
      else links[links.length - 1].focus();
    }
  });

  resultsList.addEventListener('click', function(e) {
    var link = e.target && e.target.closest ? e.target.closest('a') : null;
    if (!link) return;
    var links = Array.prototype.slice.call(resultsList.querySelectorAll('a'));
    document.dispatchEvent(new CustomEvent('am:search-result-click', {
      detail: { url: link.getAttribute('href') || '', position: links.indexOf(link) + 1, query: lastQuery }
    }));
  });

  resultsList.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      moveFocus(1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      moveFocus(-1);
    }
  });

  document.addEventListener('keydown', function(e) {
    if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return;
    if (dialog.open) return;
    var el = document.activeElement;
    if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName))) return;
    e.preventDefault();
    open();
  });

  // /search/ is the shareable entry point: open with the query from the URL.
  if (window.location.pathname === '/search/') {
    var q = new URLSearchParams(window.location.search).get('q') || '';
    open(q);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSearch);
} else {
  initSearch();
}
