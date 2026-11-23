// AntiManager — feedback form on /contact/.
// Progressive enhancement over the native form: POST JSON to the same-origin
// /api/feedback (served by the feedback microservice), show inline status.
//
// Anti-bot: the service issues a signed challenge on page load; before sending
// we solve a small SHA-256 proof of work for it. The signed issue time also
// tells the server how long the form stayed open. Without WebCrypto (insecure
// context) or a challenge the form still sends — the server then decides.
(function () {
  'use strict';

  var PACK_LABELS = {
    express: 'Экспресс-диагностика',
    process: 'Проработка процессов',
    library: 'Библиотека + правила',
    pilot: 'Одна пилотная группа',
    audit: 'Полный чек-лист ПС (120 критериев)',
    documents: 'Типовые документы производственной системы',
    dengi: 'Деньги на виду',
    operacionka: 'Собственник выходит из операционки',
    moshnost: 'Мощность без капвложений',
    standart: 'Один завод — одна система',
    komanda: 'Команда, на которую можно опереться',
    dannye: 'Правда в цифрах к утру',
    peredacha: 'Система без автора',
  };

  var CHALLENGE_URL = '/api/feedback/challenge';
  // The service expires a challenge after 2 hours; refresh a little earlier so
  // a long-open tab never submits a stale one.
  var CHALLENGE_MAX_AGE_MS = 100 * 60 * 1000;
  var BATCH = 64;

  var challenge = null;

  function hasSubtle() {
    return !!(window.crypto && window.crypto.subtle && window.TextEncoder);
  }

  function loadChallenge() {
    if (!hasSubtle() || !window.fetch) return;
    fetch(CHALLENGE_URL, { headers: { Accept: 'application/json' } })
      .then(function (response) {
        return response.ok ? response.json() : null;
      })
      .then(function (data) {
        if (data && data.challenge && data.signature) challenge = data;
      })
      .catch(function () {
        // No challenge (static preview, offline, service down): submit without
        // one and let the server route the message.
      });
  }

  function leadingZeroBits(bytes) {
    var bits = 0;
    for (var i = 0; i < bytes.length; i += 1) {
      var byte = bytes[i];
      if (byte === 0) {
        bits += 8;
        continue;
      }
      bits += Math.clz32(byte) - 24;
      break;
    }
    return bits;
  }

  function solve(item) {
    var encoder = new TextEncoder();
    var prefix = item.challenge + ':';
    var target = item.bits;
    var nonce = 0;

    function attempt() {
      var pending = [];
      for (var i = 0; i < BATCH; i += 1) {
        const candidate = nonce + i;
        pending.push(window.crypto.subtle.digest('SHA-256', encoder.encode(prefix + candidate))
          .then(function (buffer) {
            return { nonce: candidate, digest: new Uint8Array(buffer) };
          }));
      }
      nonce += BATCH;
      return Promise.all(pending).then(function (results) {
        for (var j = 0; j < results.length; j += 1) {
          if (leadingZeroBits(results[j].digest) >= target) return String(results[j].nonce);
        }
        return null;
      });
    }

    function loop() {
      return attempt().then(function (found) {
        return found !== null ? found : loop();
      });
    }

    return loop();
  }

  function proofFor(payload) {
    if (!challenge || !hasSubtle()) return Promise.resolve(null);
    if (Date.now() / 1000 - challenge.issued > CHALLENGE_MAX_AGE_MS / 1000) {
      return Promise.resolve(null);
    }
    return solve(challenge).then(function (nonce) {
      if (nonce === null) return null;
      return {
        challenge: challenge.challenge,
        challenge_bits: challenge.bits,
        challenge_issued: challenge.issued,
        challenge_signature: challenge.signature,
        challenge_nonce: nonce,
      };
    });
  }

  function init() {
    var form = document.getElementById('feedbackForm');
    if (!form) return;

    var nameEl = document.getElementById('cf-name');
    var contactEl = document.getElementById('cf-contact');
    var messageEl = document.getElementById('cf-message');
    var consentEl = document.getElementById('cf-consent');
    var decoyEl = document.getElementById('cf-url');
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

    loadChallenge();

    function setStatus(message, kind) {
      if (!status) return;
      status.textContent = message;
      status.className = 'form-status' + (kind ? ' ' + kind : '');
    }

    function send(payload) {
      return fetch('/api/feedback', {
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
        // A separate goal from Metrika's automatic `contact_data_sent` (that
        // one cannot be reproduced in GA4 and would double-count). analytics.js
        // mirrors `am:goal` into both Metrika and GA4.
        document.dispatchEvent(new CustomEvent('am:goal', {
          detail: { name: 'lead_sent', params: { pack: pack || 'none' } },
        }));
        setStatus('Заявка отправлена. Отвечу в течение рабочего дня, пн–пт.', 'ok');
      }).catch(function (err) {
        if (err && err.status === 429) {
          setStatus('Слишком много заявок подряд. Напишите, пожалуйста, в Telegram.', 'err');
        } else {
          setStatus('Не удалось отправить. Попробуйте ещё раз или напишите в Telegram.', 'err');
        }
      }).finally(function () {
        if (button) button.disabled = false;
      });
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
        url: decoyEl ? decoyEl.value : '',
        consent: consentEl ? consentEl.checked : false,
      };

      if (button) button.disabled = true;
      setStatus('Проверяем…', '');

      proofFor(payload).then(function (proof) {
        var body = proof
          ? Object.assign({}, payload, proof)
          : payload;
        return send(body);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();
