// public/js/config.js
(function () {
  // evita rodar duas vezes
  if (window.__CFG_LOADED && typeof window.__CFG_LOADED.then === 'function') return;

  function stripEndSlash(s) { return String(s || '').replace(/\/+$/, ''); }

  // tenta localizar o config.json mesmo quando a página está em /tabela_preco/...
  const CANDIDATES = [
    '/config.json',      // raiz do site (ex.: quando serve /public como root)
    '../config.json',    // uma pasta acima (ex.: /tabela_preco/…)
    '../../config.json'  // duas acima (casos específicos)
  ];

  function fetchFirst(paths) {
    let i = 0;
    function tryNext() {
      if (i >= paths.length) return Promise.reject(new Error('config.json não encontrado'));
      const url = paths[i++];
      return fetch(url, { cache: 'no-store' }).then(r => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      }).catch(tryNext);
    }
    return tryNext();
  }

  window.__CFG_LOADED = fetchFirst(CANDIDATES)
    .then(cfg => {
      window.__CFG = cfg || {};
      const base = stripEndSlash(window.__CFG.API_BASE_URL);
      // define/normaliza API_BASE se existir no JSON; senão preserva o que já houver
      window.API_BASE = base || stripEndSlash(window.API_BASE || '');
      return window.API_BASE;
    })
    .catch(() => {
      // sem config.json: apenas normaliza o que houver (útil em dev puro)
      window.API_BASE = stripEndSlash(window.API_BASE || '');
      return window.API_BASE;
    });
})();