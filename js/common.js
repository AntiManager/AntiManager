// AntiManager — Common Utilities

document.addEventListener('DOMContentLoaded', function() {
  initTheme();
  initSidebar();
  initScrollTop();
  initModals();
  initAccordions();
  initDownloadButtons();
});

// --- Theme ---
function initTheme() {
  var toggle = document.getElementById('themeToggle');
  if (!toggle) return;
  toggle.addEventListener('click', function() {
    var html = document.documentElement;
    var next = html.classList.contains('dark') ? 'light' : 'dark';
    html.classList.toggle('dark', next === 'dark');
    localStorage.setItem('am-theme', next);
  });
}

// --- Sidebar ---
function initSidebar() {
  var toggles = document.querySelectorAll('.sidebar-toggle');
  var shell = document.getElementById('appShell');
  var sidebar = document.getElementById('sidebar');
  var backdrop = document.getElementById('sidebarBackdrop');
  if (!toggles.length || !shell) return;

  function lockBody(lock) {
    document.body.style.overflow = lock ? 'hidden' : '';
  }

  toggles.forEach(function(btn) {
    btn.addEventListener('click', function() {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
        if (backdrop) backdrop.style.display = sidebar.classList.contains('open') ? 'block' : 'none';
        lockBody(sidebar.classList.contains('open'));
      } else {
        shell.classList.toggle('sidebar-collapsed');
      }
    });
  });

  if (backdrop) {
    backdrop.addEventListener('click', function() {
      sidebar.classList.remove('open');
      this.style.display = 'none';
      lockBody(false);
    });
  }

  // Keyboard shortcut
  document.addEventListener('keydown', function(e) {
    if (e.key === 'b' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
        if (backdrop) backdrop.style.display = sidebar.classList.contains('open') ? 'block' : 'none';
        lockBody(sidebar.classList.contains('open'));
      } else {
        shell.classList.toggle('sidebar-collapsed');
      }
    }
    // Escape closes mobile sidebar
    if (e.key === 'Escape' && window.innerWidth <= 768 && sidebar.classList.contains('open')) {
      sidebar.classList.remove('open');
      if (backdrop) backdrop.style.display = 'none';
      lockBody(false);
    }
  });
}

// --- Scroll to Top ---
function initScrollTop() {
  var btn = document.getElementById('scrollTop');
  var main = document.getElementById('main');
  if (!btn || !main) return;

  function check() {
    btn.classList.toggle('visible', main.scrollTop > 300);
  }
  main.addEventListener('scroll', check);
  btn.addEventListener('click', function() {
    main.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

// --- Accordions ---
function initAccordions() {
  document.querySelectorAll('.accordion-header').forEach(function(header) {
    header.addEventListener('click', function() {
      var item = this.closest('.accordion-item');
      if (item) item.classList.toggle('active');
    });
  });
}

// --- Utility: open modal ---
function openModal(id) {
  var modal = document.getElementById(id);
  if (!modal) return;
  // Save focus origin BEFORE moving focus into modal
  modal._lastFocused = document.activeElement;
  modal.classList.add('open');
  // Focus-trap: focus first focusable element
  var first = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  if (first) first.focus();
}

// --- Utility: close modal ---
function closeModal(id) {
  var modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.remove('open');
  // Restore focus to element that opened the modal
  if (modal._lastFocused) modal._lastFocused.focus();
}

// --- Modal focus trap (override initModals) ---
function initModals() {
  document.addEventListener('click', function(e) {
    if (e.target.closest('.close-modal')) {
      var modal = e.target.closest('.modal');
      if (modal) closeModal(modal.id);
    }
  });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal.open').forEach(function(m) { closeModal(m.id); });
    }
    // Trap focus within open modal
    if (e.key === 'Tab') {
      var openModal = document.querySelector('.modal.open');
      if (!openModal) return;
      var focusable = openModal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (!focusable.length) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });
}

// --- Utility: filter helper ---
function toggleFilter(btn, selector) {
  document.querySelectorAll(selector).forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
}

// --- Dummy Download Button (Yandex Metrica goal) ---
function initDownloadButtons() {
  document.querySelectorAll('.download-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var chapter = this.dataset.chapter || 'unknown';
      var feedback = this.parentNode.querySelector('.download-feedback');

      // Show loading state
      var originalText = this.textContent;
      this.textContent = 'Отправляем...';
      this.disabled = true;

      // Send Yandex Metrica goal if available
      if (typeof ym !== 'undefined' && typeof window.AM_METRIKA_ID !== 'undefined') {
        try { ym(window.AM_METRIKA_ID, 'reachGoal', 'download_intent', { chapter: chapter }); } catch(e) {}
      }

      // Show confirmation after brief delay (no file download)
      window.setTimeout(function() {
        if (feedback) {
          feedback.textContent = 'Спасибо! Мы записали ваш интерес к главе «' + chapter + '». Когда полный формат выйдет — сообщим.';
          feedback.style.display = 'block';
        }
        btn.textContent = 'Заявка отправлена ✓';
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-ghost');
      }, 600);
    });
  });
}
