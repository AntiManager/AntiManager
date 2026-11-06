// AntiManager — Brutalist JS
document.addEventListener('DOMContentLoaded', function() {
  initFlash();
  initScrollReveal();
  initStickyOffset();
  initReadingProgress();
  initAccordions();
  initMenuToggle();
  initScrollTop();
  initMethodSample();
});

function initFlash() {
  document.body.classList.add('flash-in');
  setTimeout(function() { document.body.classList.remove('flash-in'); }, 500);
}

function initScrollReveal() {
  var els = document.querySelectorAll('.reveal');
  if (!els.length) return;
  if (!window.IntersectionObserver) {
    for (var i = 0; i < els.length; i++) els[i].classList.add('revealed');
    return;
  }
  var obs = new IntersectionObserver(function(entries) {
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].isIntersecting) {
        entries[i].target.classList.add('revealed');
        obs.unobserve(entries[i].target);
      }
    }
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  for (var j = 0; j < els.length; j++) obs.observe(els[j]);
}

function initStickyOffset() {
  var header = document.querySelector('.site-header');
  if (!header) return;
  function set() {
    document.documentElement.style.setProperty('--header-h', header.offsetHeight + 'px');
  }
  set();
  window.addEventListener('resize', set);
}

function initReadingProgress() {
  var bar = document.querySelector('.reading-progress-fill');
  var article = document.querySelector('.full-article') || document.querySelector('[data-reading]');
  if (!bar || !article) return;

  function update() {
    var start = article.offsetTop;
    var total = article.offsetHeight - window.innerHeight;
    if (total <= 0) { bar.style.width = '100%'; return; }
    var pct = ((window.scrollY - start) / total) * 100;
    bar.style.width = Math.min(100, Math.max(0, pct)) + '%';
  }

  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  update();
}

function initAccordions() {
  var headers = document.querySelectorAll('.accordion-header');
  for (var i = 0; i < headers.length; i++) {
    headers[i].addEventListener('click', function() {
      var item = this.closest('.accordion-item');
      if (item) item.classList.toggle('active');
    });
  }
}

function initMenuToggle() {
  var toggle = document.querySelector('.menu-toggle');
  var nav = document.querySelector('.header-nav');
  if (!toggle || !nav) return;

  function closeMenu(returnFocus) {
    if (!nav.classList.contains('open')) return;
    nav.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Меню');
    toggle.textContent = '☰';
    if (returnFocus) toggle.focus();
  }

  toggle.addEventListener('click', function() {
    var isOpen = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(isOpen));
    toggle.setAttribute('aria-label', isOpen ? 'Закрыть меню' : 'Меню');
    toggle.textContent = isOpen ? '✕' : '☰';
  });

  // Close menu when a link is clicked
  var links = nav.querySelectorAll('a');
  for (var i = 0; i < links.length; i++) {
    links[i].addEventListener('click', function() {
      closeMenu(false);
    });
  }

  // Escape closes the menu and returns focus to the toggle (a11y).
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' || e.key === 'Esc') closeMenu(true);
  });
}

function initScrollTop() {
  var btn = document.querySelector('.scroll-top');
  if (!btn) return;

  window.addEventListener('scroll', function() {
    if (window.scrollY > 300) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }
  });

  btn.addEventListener('click', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

// The PLAN sample ships its first process expanded to prove the level of
// detail. At phone widths that one block is ~6,000px tall — collapse it so the
// offer stays reachable; desktop keeps the open preview.
function initMethodSample() {
  if (!window.matchMedia || !window.matchMedia('(max-width: 640px)').matches) return;
  var open = document.querySelector('#sample details[open]');
  if (open) open.removeAttribute('open');
}
