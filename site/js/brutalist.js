// AntiManager — Brutalist JS
document.addEventListener('DOMContentLoaded', function() {
  initFlash();
  initScrollReveal();
  initDownloadButtons();
  initAccordions();
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
