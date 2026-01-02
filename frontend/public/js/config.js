// Configuração dinâmica da API
// Se estiver rodando localmente, assume backend no 8000
// Se estiver em produção (mesma origem), usa a própria origem
window.API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
  ? 'http://127.0.0.1:8000'
  : window.location.origin;