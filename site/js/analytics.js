// AntiManager — Yandex.Metrika goals (plan 12.6).
// Counter id is duplicated in base.html; keep both in sync.
(function() {
  var METRIKA_ID = 111010335;
  var scroll75Sent = false;

  function send(goal, params) {
    try {
      if (typeof window.ym === 'function') {
        window.ym(METRIKA_ID, 'reachGoal', goal, params || {});
      }
    } catch (e) { /* analytics must never break the page */ }
  }

  function placement() {
    var path = window.location.pathname === '/' ? 'home' : window.location.pathname.replace(/^\/|\/$/g, '');
    return path.replace(/\//g, '-') || 'home';
  }

  function fileName(href) {
    var path = href.split(/[?#]/)[0];
    return path.split('/').pop() || path;
  }

  function isTelegram(href) {
    return /^https?:\/\/(t|telegram)\.me\//i.test(href);
  }

  // UTM tags for Telegram links. Telegram ignores unknown parameters on bot
  // links, so this is safe for t.me/<bot>; it makes referral sources visible
  // when the destination is a chat or channel.
  function tagTelegramLinks() {
    var links = document.querySelectorAll('a[href*="t.me/"], a[href*="telegram.me/"]');
    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      if (!isTelegram(link.href)) continue;
      try {
        var url = new URL(link.href);
        if (!url.searchParams.has('utm_source')) {
          url.searchParams.set('utm_source', 'antimanager.pro');
          url.searchParams.set('utm_medium', 'site');
          url.searchParams.set('utm_campaign', placement());
          link.href = url.toString();
        }
      } catch (e) { /* leave malformed links untouched */ }
    }
  }

  document.addEventListener('am:search-open', function() {
    send('search_open', { placement: placement() });
  });

  document.addEventListener('am:search-query', function(e) {
    var detail = e.detail || {};
    send('search_query', { query: detail.query || '', results: detail.total || 0 });
  });

  document.addEventListener('am:search-result-click', function(e) {
    var detail = e.detail || {};
    send('search_result_click', { url: detail.url || '', position: detail.position || 0 });
  });

  document.addEventListener('click', function(e) {
    var target = e.target;
    var link = target && target.closest ? target.closest('a[href]') : null;
    if (!link) return;

    var cta = link.getAttribute('data-cta');
    if (cta) send('cta_click', { cta: cta, placement: placement() });

    var path = (link.getAttribute('href') || '').split(/[?#]/)[0];
    if (link.hasAttribute('download') || /\.(pdf|docx|xlsx)$/i.test(path)) {
      send('download', { file: fileName(link.getAttribute('href') || '') });
    }

    if (isTelegram(link.href)) {
      send('outbound_telegram', { placement: placement() });
    }
  });

  window.addEventListener('scroll', function() {
    if (scroll75Sent) return;
    var doc = document.documentElement;
    var height = doc.scrollHeight - window.innerHeight;
    if (height <= 0) return;
    var ratio = (window.scrollY + window.innerHeight) / doc.scrollHeight;
    if (ratio >= 0.75) {
      scroll75Sent = true;
      send('scroll_75', { placement: placement() });
    }
  }, { passive: true });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', tagTelegramLinks);
  } else {
    tagTelegramLinks();
  }
})();
