// AntiManager — Brutalist JS
document.addEventListener('DOMContentLoaded', function() {
  initFlash();
  initScrollReveal();
  initReadingProgress();
  initAccordions();
  initMenuToggle();
  initScrollTop();
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

function initReadingProgress() {
  var bar = document.querySelector('.reading-progress-fill');
  var article = document.querySelector('.full-article');
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

  toggle.addEventListener('click', function() {
    var isOpen = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', isOpen);
    toggle.textContent = isOpen ? '✕' : '☰';
  });

  // Close menu when a link is clicked
  var links = nav.querySelectorAll('a');
  for (var i = 0; i < links.length; i++) {
    links[i].addEventListener('click', function() {
      nav.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.textContent = '☰';
    });
  }
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
