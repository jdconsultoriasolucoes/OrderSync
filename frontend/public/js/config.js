(function () {
  if (window.__CFG_LOADED && typeof window.__CFG_LOADED.then === 'function') return;

  function stripEndSlash(s) {
    return String(s || '').replace(/\/+$/, '');
  }

  window.__CFG_LOADED = fetch('/config.json', { cache: 'no-store' })
    .then(function (r) { return r.json(); })
    .then(function (cfg) {
      window.__CFG = cfg || {};
      var base = stripEndSlash(window.__CFG.API_BASE_URL);
      // se o config.json vier vazio, mantém o que já houver
      window.API_BASE = base || stripEndSlash(window.API_BASE);
      return window.API_BASE;
    })
    .catch(function () {
      // sem config.json: mantém o que já houver
      window.API_BASE = stripEndSlash(window.API_BASE);
      return window.API_BASE;
    });
})();