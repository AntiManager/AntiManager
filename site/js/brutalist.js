// AntiManager — Brutalist JS
document.addEventListener('DOMContentLoaded', function() {
  initFlash();
  initScrollReveal();
  initDownloadButtons();
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

function initDownloadButtons() {
  var btns = document.querySelectorAll('.download-btn');
  for (var i = 0; i < btns.length; i++) {
    btns[i].addEventListener('click', function() {
      var feedback = this.parentNode.querySelector('.download-feedback');
      if (feedback) {
        feedback.textContent = 'Спасибо! Мы записали ваш интерес к статье. Когда материалы будут готовы — сообщим.';
        feedback.style.display = 'block';
      }
      this.textContent = 'Заявка отправлена ✓';
      this.classList.remove('btn');
      this.style.opacity = '0.5';
      this.style.cursor = 'default';
    });
  }
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
