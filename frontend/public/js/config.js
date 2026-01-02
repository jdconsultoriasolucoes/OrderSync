// Configuração dinâmica da API
// Se estiver rodando localmente (localhost ou 127.0.0.1), aponta para porta 8000
// Se estiver em produção (Render), aponta para a URL do Backend (edjq)
window.API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
  ? 'http://127.0.0.1:8000'
  : 'https://ordersync-backend-edjq.onrender.com';