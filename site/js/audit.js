// AntiManager — /genome/audit/.
// <details> works without JS; this only adds toggle-all, opens a criterion
// targeted by the URL hash, and expands everything for printing.
(function () {
  'use strict';

  function criteria() {
    return Array.prototype.slice.call(document.querySelectorAll('.audit-criterion'));
  }

  function setAll(open) {
    criteria().forEach(function (item) { item.open = open; });
  }

  function openHash() {
    var id = window.location.hash.replace(/^#/, '');
    if (!id) return;
    var target = document.getElementById(decodeURIComponent(id));
    if (target && target.tagName === 'DETAILS') {
      target.open = true;
      target.scrollIntoView({ block: 'start' });
    }
  }

  var closedBeforePrint = null;

  function init() {
    document.querySelectorAll('[data-audit-toggle]').forEach(function (button) {
      button.addEventListener('click', function () {
        setAll(button.getAttribute('data-audit-toggle') === 'open');
      });
    });

    window.addEventListener('hashchange', openHash);
    openHash();

    window.addEventListener('beforeprint', function () {
      closedBeforePrint = criteria().filter(function (item) { return !item.open; });
      setAll(true);
    });
    window.addEventListener('afterprint', function () {
      if (!closedBeforePrint) return;
      closedBeforePrint.forEach(function (item) { item.open = false; });
      closedBeforePrint = null;
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();
