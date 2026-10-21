// AntiManager — feedback form on /contact/.
// Progressive enhancement over the native form: POST JSON to the same-origin
// /api/feedback (served by the feedback microservice), show inline status.
(function () {
  'use strict';

  var PACK_LABELS = {
    express: 'Экспресс-диагностика',
    process: 'Проработка процессов',
    library: 'Библиотека + правила',
    pilot: 'Одна пилотная группа',
    audit: 'Полный чек-лист ПС (120 критериев)',
  };

  function init() {
    var form = document.getElementById('feedbackForm');
    if (!form) return;

    var nameEl = document.getElementById('cf-name');
    var contactEl = document.getElementById('cf-contact');
    var messageEl = document.getElementById('cf-message');
    var consentEl = document.getElementById('cf-consent');
    var websiteEl = document.getElementById('cf-website');
    var packInput = document.getElementById('cf-pack');
    var packNote = document.getElementById('packNote');
    var status = document.getElementById('formStatus');
    var button = form.querySelector('button[type="submit"]');

    var pack = new URLSearchParams(window.location.search).get('pack') || '';
    if (PACK_LABELS[pack]) {
      if (packInput) packInput.value = pack;
      if (packNote) {
        packNote.textContent = 'Интересует: ' + PACK_LABELS[pack];
        packNote.hidden = false;
      }
    }

    function setStatus(message, kind) {
      if (!status) return;
      status.textContent = message;
      status.className = 'form-status' + (kind ? ' ' + kind : '');
    }

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      var payload = {
        name: nameEl ? nameEl.value.trim() : '',
        contact: contactEl ? contactEl.value.trim() : '',
        message: messageEl ? messageEl.value.trim() : '',
        pack: packInput ? packInput.value : '',
        website: websiteEl ? websiteEl.value : '',
        consent: consentEl ? consentEl.checked : false,
      };

      if (button) button.disabled = true;
      setStatus('Отправляем…', '');

      fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }).then(function (response) {
        if (!response.ok) {
          var err = new Error('bad status ' + response.status);
          err.status = response.status;
          throw err;
        }
        return response.json();
      }).then(function () {
        form.reset();
        if (packInput) packInput.value = pack;
        setStatus('Заявка отправлена. Отвечу в ближайшее время.', 'ok');
      }).catch(function (err) {
        if (err && err.status === 429) {
          setStatus('Слишком много заявок подряд. Напишите, пожалуйста, в Telegram.', 'err');
        } else {
          setStatus('Не удалось отправить. Попробуйте ещё раз или напишите в Telegram.', 'err');
        }
      }).finally(function () {
        if (button) button.disabled = false;
      });
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();
