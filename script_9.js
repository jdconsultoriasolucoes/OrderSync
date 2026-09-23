// Carrega dados da aba Compras quando aberta
            function carregarAbaCompras() {
              const codigo = document.getElementById('codigo_da_empresa')?.value?.trim();
              if (!codigo) return;

              const api = window.API_BASE || 'http://127.0.0.1:8000';
              const token = window.Auth ? window.Auth.getToken() : localStorage.getItem('ordersync_token');
              const headers = token ? { 'Authorization': 'Bearer ' + token } : {};

              // --- Últimas Compras ---
              const loadingEl = document.getElementById('compras-loading');
              const tabelaEl  = document.getElementById('compras-tabela');
              const tbodyEl   = document.getElementById('compras-tbody');
              const vazioEl   = document.getElementById('compras-vazio');

              loadingEl.style.display = 'block';
              tabelaEl.style.display  = 'none';
              vazioEl.style.display   = 'none';

              fetch(`${api}/cliente/${encodeURIComponent(codigo)}/ultimas_compras`, { headers })
                .then(r => r.json())
                .then(data => {
                  loadingEl.style.display = 'none';
                  if (!data || data.length === 0) {
                    vazioEl.style.display = 'block';
                    return;
                  }
                  tbodyEl.innerHTML = data.map(c => {
                    const statusColor = (c.status || '').toUpperCase() === 'CANCELADO'
                      ? '#dc2626' : (c.status || '').toUpperCase() === 'CONFIRMADO' ? '#16a34a' : '#374151';
                    const total = (c.total_pedido || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
                    return `<tr style="border-bottom:1px solid #f1f5f9;">
                      <td style="padding:8px 10px; white-space:nowrap;">${c.data}</td>
                      <td style="padding:8px 10px;">${c.tabela_preco_nome}</td>
                      <td style="padding:8px 10px; text-align:right; font-weight:600;">${total}</td>
                      <td style="padding:8px 10px; white-space:nowrap; color:${statusColor}; font-weight:600;">${c.status}</td>
                    </tr>`;
                  }).join('');
                  tabelaEl.style.display = 'table';
                })
                .catch(() => {
                  loadingEl.textContent = 'Erro ao carregar histórico de compras.';
                });

              // --- Tabelas de Preço ---
              const tLoadEl  = document.getElementById('tabelas-loading');
              const tListaEl = document.getElementById('tabelas-lista');
              const tVazioEl = document.getElementById('tabelas-vazio');

              tLoadEl.style.display  = 'block';
              tListaEl.style.display = 'none';
              tVazioEl.style.display = 'none';

              fetch(`${api}/cliente/${encodeURIComponent(codigo)}/tabelas_preco`, { headers })
                .then(r => r.json())
                .then(data => {
                  tLoadEl.style.display = 'none';
                  if (!data || data.length === 0) {
                    tVazioEl.style.display = 'block';
                    return;
                  }
                  tListaEl.innerHTML = data.map(t =>
                    `<a href="/tabela_preco/criacao_tabela_preco.html?id=${t.id_tabela}"
                        style="display:flex; align-items:center; gap:8px; padding:10px 14px;
                               background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;
                               text-decoration:none; color:#1e40af; font-size:13px; font-weight:500;
                               transition: background 0.15s, border-color 0.15s;"
                        onmouseover="this.style.background='#eff6ff';this.style.borderColor='#93c5fd';"
                        onmouseout="this.style.background='#f8fafc';this.style.borderColor='#e2e8f0';">
                      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none"
                           viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="flex-shrink:0;">
                        <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
                        <line x1="7" y1="7" x2="7.01" y2="7"/>
                      </svg>
                      ${t.nome_tabela}
                    </a>`
                  ).join('');
                  tListaEl.style.display = 'flex';
                })
                .catch(() => {
                  tLoadEl.textContent = 'Erro ao carregar tabelas de preço.';
                });
            }

            // Hook: dispara carregamento ao clicar na aba Compras
            document.addEventListener('DOMContentLoaded', function() {
              const btnCompras = document.querySelector('.tab[onclick*="compras"]');
              if (btnCompras) {
                btnCompras.addEventListener('click', function() {
                  carregarAbaCompras();
                });
              }
            });