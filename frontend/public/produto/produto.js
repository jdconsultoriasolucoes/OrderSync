// ==================== produto.js ====================

// === Config ===
const API_BASE = "https://ordersync-backend-edjq.onrender.com";
window.API_BASE = API_BASE;

// candidatos de rotas (ordem de preferência)
const CANDIDATES = [
  `${API_BASE}/api/produtos`,
  `${API_BASE}/api/produto`,
  `${API_BASE}/api/produtos_v2`,
  `${API_BASE}/api/produto_v2`,
  `${API_BASE}/produtos`,
  `${API_BASE}/produto`,
];

const API = {
  familias:   `${API_BASE}/api/familias`,
  tiposGiro:  `${API_BASE}/api/tipos-giro`,
  status:     `${API_BASE}/api/produtos/status`,
};

// cache em memória/localStorage do endpoint resolvido
let PROD_ENDPOINT = localStorage.getItem('ordersync_prod_endpoint') || null;

// === Utils ===
const $ = (id) => document.getElementById(id);
const toast = (msg) => {
  const t = $('toast');
  if (!t) return alert(msg);
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(() => (t.style.display = 'none'), 2400);
};

async function fetchRaw(url, opts = {}) {
  return fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
}
async function fetchJSON(url, opts = {}) {
  const res = await fetchRaw(url, opts);
  if (!res.ok) {
    const body = await res.text().catch(()=> '');
    const err = new Error(body || res.statusText);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

// ---------- Descoberta do endpoint de produtos ----------
async function resolveProdutosEndpoint(force = false) {
  if (!force && PROD_ENDPOINT) return PROD_ENDPOINT;

  for (const base of CANDIDATES) {
    try {
      // tentativa: GET lista com limite pequeno; se 404, tenta o próximo
      const probe = await fetchRaw(`${base}?page=1&pageSize=1`);
      if (probe.status !== 404) {
        PROD_ENDPOINT = base;
        localStorage.setItem('ordersync_prod_endpoint', base);
        console.log('[produto] endpoint resolvido:', base);
        return base;
      }
    } catch (_) { /* ignora e tenta próximo */ }
  }
  // fallback (pode 404, mas evita ficar null)
  PROD_ENDPOINT = CANDIDATES[0];
  localStorage.setItem('ordersync_prod_endpoint', PROD_ENDPOINT);
  return PROD_ENDPOINT;
}

// wrappers que usam fallback automático quando 404
async function produtosGET(path = '', qs = '') {
  const tried = new Set();
  while (tried.size < CANDIDATES.length) {
    const base = await resolveProdutosEndpoint();
    try {
      return await fetchJSON(`${base}${path}${qs}`, { method: 'GET' });
    } catch (e) {
      if (e.status === 404) {
        tried.add(base);
        // força resolver para o próximo candidato
        const idx = CANDIDATES.indexOf(base);
        const next = CANDIDATES[(idx + 1) % CANDIDATES.length];
        PROD_ENDPOINT = next;
        localStorage.setItem('ordersync_prod_endpoint', next);
        continue;
      }
      throw e;
    }
  }
  // última tentativa com o primeiro candidato
  return fetchJSON(`${CANDIDATES[0]}${path}${qs}`, { method: 'GET' });
}

async function produtosPOST(body) {
  const base = await resolveProdutosEndpoint();
  try {
    return await fetchJSON(base, { method: 'POST', body: JSON.stringify(body) });
  } catch (e) {
    if (e.status === 404) {
      // tenta os demais
      for (const cand of CANDIDATES) {
        if (cand === base) continue;
        try {
          PROD_ENDPOINT = cand;
          localStorage.setItem('ordersync_prod_endpoint', cand);
          return await fetchJSON(cand, { method: 'POST', body: JSON.stringify(body) });
        } catch (ee) { if (ee.status !== 404) throw ee; }
      }
    }
    throw e;
  }
}

async function produtosPATCH(id, body) {
  const base = await resolveProdutosEndpoint();
  const paths = [`${base}/${id}`];
  // se a rota for singular sem /{id}, não há muito o que fazer; mantemos /{id}
  for (const p of [ `${base}/${id}`, `${base}/${encodeURIComponent(id)}` ]) {
    try { return await fetchJSON(p, { method: 'PATCH', body: JSON.stringify(body) }); }
    catch (e) {
      if (e.status === 404) continue;
      throw e;
    }
  }
  // tenta outros candidatos
  for (const cand of CANDIDATES) {
    try { 
      PROD_ENDPOINT = cand;
      localStorage.setItem('ordersync_prod_endpoint', cand);
      return await fetchJSON(`${cand}/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
    } catch (e) { if (e.status !== 404) throw e; }
  }
  throw new Error('Não foi possível localizar a rota de PATCH dos produtos.');
}

// ---------- cálculos/aux ----------
function setSelect(el, items, getLabel = (x) => x.label, getValue = (x) => x.value) {
  if (!el) return;
  el.innerHTML = '<option value="">— selecione —</option>' +
    (items || []).map((it) => `<option value="${getValue(it)}">${getLabel(it)}</option>`).join('');
}
function reajustePercentual(atual, anterior) {
  if (!Number.isFinite(anterior) || anterior === 0 || !Number.isFinite(atual)) return null;
  return ((atual - anterior) / anterior) * 100;
}
function vigenciaAtiva(validadeISO) {
  if (!validadeISO) return null;
  const hoje = new Date();
  const d = new Date(`${validadeISO}T00:00:00`);
  return hoje >= d;
}

// ===== Modal helpers (defensivo) =====
const modal = {
  open()  {
    const m = $('search-modal');
    if (!m) { console.warn('search-modal não encontrado no HTML'); return; }
    m.classList.remove('hidden');
    const inp = $('search-input');
    if (inp) setTimeout(()=>inp.focus(), 30);
  },
  close() {
    const m = $('search-modal');
    if (!m) return;
    m.classList.add('hidden');
    const box = $('search-results');
    if (box) box.innerHTML = '';
    const inp = $('search-input');
    if (inp) inp.value = '';
  }
};
function debounce(fn, ms=300){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), ms); }; }

function renderResults(list){
  const box = $('search-results');
  if (!box) return;
  if (!list || !list.length){
    box.innerHTML = `<div class="empty">Nada encontrado.</div>`;
    return;
  }
  const rows = list.map(p => `
    <tr data-id="${p.id}">
      <td style="width:160px"><strong>${p.codigo_supra ?? ''}</strong></td>
      <td>${p.nome_produto ?? ''}</td>
      <td style="width:120px; text-align:right">R$ ${Number(p.preco ?? 0).toFixed(2)}</td>
      <td style="width:120px">${p.unidade ?? ''}</td>
      <td style="width:140px">${p.status_produto ?? ''}</td>
    </tr>
  `).join('');
  box.innerHTML = `
    <table>
      <thead><tr>
        <th>Código</th><th>Descrição</th><th>Preço</th><th>Unid.</th><th>Status</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
  box.querySelectorAll('tbody tr').forEach(tr=>{
    tr.addEventListener('click', async ()=>{
      const id = tr.getAttribute('data-id');
      try{
        const base = await resolveProdutosEndpoint();
        const data = await fetchJSON(`${base}/${id}`);
        fillForm(data);
        modal.close();
        toast('Produto carregado.');
      } catch(e){ toast('Erro ao abrir item.'); console.error(e); }
    });
  });
}

const doSearch = debounce(async ()=>{
  const inp = $('search-input');
  const box = $('search-results');
  if (!inp || !box) return;
  const q = inp.value.trim();
  if (!q){ box.innerHTML = `<div class="empty">Digite parte do código ou descrição…</div>`; return; }
  try{
    const list = await produtosGET('', `?q=${encodeURIComponent(q)}&page=1&pageSize=25`);
    renderResults(list);
  }catch(e){
    console.error(e);
    box.innerHTML = `<div class="empty">Erro ao buscar.</div>`;
  }
}, 300);

// === Carregar selects ===
async function loadSelects() {
  try {
    const fams = await fetchJSON(API.familias);
    setSelect($('familia'), fams, (f) => f.familia, (f) => f.id);
    const linhas = Array.from(new Map(
      (fams || []).map(f => [f.tipo, { label: f.tipo, value: f.tipo }])
    ).values());
    setSelect($('linha'), linhas);
  } catch {
    setSelect($('familia'), [{ label: 'DIVERSOS', value: 1 }], x => x.label, x => x.value);
    setSelect($('linha'), [{ label: 'INSUMOS', value: 'INSUMOS' }], x => x.label, x => x.value);
  }

  try {
    const stats = await fetchJSON(API.status);
    setSelect($('status_produto'), stats, (s) => s.label, (s) => s.value);
  } catch {
    setSelect($('status_produto'), [
      { label: 'ATIVO', value: 'ATIVO' },
      { label: 'INATIVO', value: 'INATIVO' },
    ]);
  }

  try {
    const tg = await fetchJSON(API.tiposGiro);
    setSelect($('tipo_giro'), tg, (s) => s.label, (s) => s.value);
  } catch {
    setSelect($('tipo_giro'), [
      { label: 'Encomenda', value: 'Encomenda' },
      { label: 'Estoque', value: 'Estoque' },
    ]);
  }
}

// === Leitura do formulário ===
function readForm() {
  const v = (id) => ($(id)?.value ?? '').trim();
  const n = (id) => { const raw = v(id); return raw === '' ? null : Number(raw); };

  return {
    codigo_supra: v('codigo_supra') || null,
    nome_produto: v('nome_produto') || null,
    status_produto: v('status_produto') || null,
    tipo_giro: v('tipo_giro') || null,
    familia: $('familia')?.value ? Number($('familia').value) : null,
    filhos: $('filhos')?.value ? Number($('filhos').value) : null,

    unidade: v('unidade') || null,
    unidade_anterior: v('unidade_anterior') || null,
    peso: n('peso'),
    peso_bruto: n('peso_bruto'),
    embalagem_venda: v('embalagem_venda') || null,
    unidade_embalagem: n('unidade_embalagem'),

    ncm: v('ncm') || null,
    estoque_disponivel: n('estoque_disponivel'),
    estoque_ideal: n('estoque_ideal'),

    codigo_ean: v('codigo_ean') || null,
    codigo_embalagem: v('codigo_embalagem') || null,
    fornecedor: v('fornecedor') || null,

    preco: n('preco'),
    preco_tonelada: n('preco_tonelada'),
    validade_tabela: v('validade_tabela') || null,

    desconto_valor_tonelada: n('desconto_valor_tonelada'),
    data_desconto_inicio: v('data_desconto_inicio') || null,
    data_desconto_fim: v('data_desconto_fim') || null,
  };
}

function readImposto() {
  const n = (id) => { const raw = ($(id)?.value ?? '').trim(); return raw === '' ? 0 : Number(raw); };
  return { ipi: n('ipi'), icms: n('icms'), iva_st: n('iva_st'), cbs: n('cbs'), ibs: n('ibs') };
}

// === Preencher form ===
let CURRENT_ID = null;
function fillForm(p) {
  const set = (id, v) => { if ($(id)) $(id).value = (v ?? ''); };
  set('codigo_supra', p.codigo_supra);
  set('nome_produto', p.nome_produto);
  set('status_produto', p.status_produto);
  set('tipo_giro', p.tipo_giro);
  set('familia', p.familia);
  set('filhos', p.filhos);
  set('unidade', p.unidade);
  set('unidade_anterior', p.unidade_anterior);
  set('peso', p.peso);
  set('peso_bruto', p.peso_bruto);
  set('embalagem_venda', p.embalagem_venda);
  set('unidade_embalagem', p.unidade_embalagem);
  set('ncm', p.ncm);
  set('estoque_disponivel', p.estoque_disponivel);
  set('estoque_ideal', p.estoque_ideal);
  set('codigo_ean', p.codigo_ean);
  set('codigo_embalagem', p.codigo_embalagem);
  set('fornecedor', p.fornecedor);
  set('preco', p.preco);
  set('preco_tonelada', p.preco_tonelada);
  set('validade_tabela', p.validade_tabela);

  set('preco_anterior', p.preco_anterior);
  set('preco_tonelada_anterior', p.preco_tonelada_anterior);
  set('validade_tabela_anterior', p.validade_tabela_anterior);
  if ($('unidade_anterior_ro')) $('unidade_anterior_ro').value = p.unidade_anterior ?? '';

  set('desconto_valor_tonelada', p.desconto_valor_tonelada);
  set('data_desconto_inicio', p.data_desconto_inicio);
  set('data_desconto_fim', p.data_desconto_fim);
  set('preco_final', p.preco_final);

  const r = reajustePercentual(Number(p.preco ?? 0), Number(p.preco_anterior ?? 0));
  if ('reajuste' in window && $('reajuste')) $('reajuste').textContent = r == null ? '—' : r.toFixed(2) + '%';

  const vig = vigenciaAtiva(p.validade_tabela);
  if ($('vigencia')) {
    $('vigencia').textContent = vig == null ? '—' : (vig ? 'ATIVA' : 'FUTURA');
    $('vigencia').className = 'pill ' + (vig ? 'ok' : '');
  }

  CURRENT_ID = p?.id ?? null;
}

// ====== Eventos ======
document.addEventListener('DOMContentLoaded', async () => {
  await resolveProdutosEndpoint().catch(()=>{});
  loadSelects().catch(console.error);

  $('btn-novo')?.addEventListener('click', () => {
    document.querySelectorAll('input').forEach((i) => (i.value = ''));
    document.querySelectorAll('select').forEach((s) => (s.value = ''));
    CURRENT_ID = null;
    toast('Formulário limpo.');
  });

  $('btn-buscar')?.addEventListener('click', () => {
    modal.open();
    const box = $('search-results');
    if (box) box.innerHTML = `<div class="empty">Digite para buscar…</div>`;
  });

  $('btn-editar')?.addEventListener('click', async () => {
    const q = prompt('Código ou descrição para editar:');
    if (!q) return;
    try {
      const list = await produtosGET('', `?q=${encodeURIComponent(q)}&limit=1`);
      if (!list.length) { toast('Nenhum produto encontrado.'); return; }
      fillForm(list[0]);
      toast('Modo edição: produto carregado.');
    } catch (e) { toast('Erro ao carregar para edição.'); console.error(e); }
  });

  $('btn-salvar')?.addEventListener('click', async () => {
    const produto = readForm();
    if (produto.desconto_valor_tonelada != null &&
        (!produto.data_desconto_inicio || !produto.data_desconto_fim)) {
      toast('Preencha início e fim do desconto.');
      return;
    }
    const imposto = readImposto();

    try {
      if (CURRENT_ID) {
        const res = await produtosPATCH(CURRENT_ID, { produto, imposto });
        fillForm(res);
        toast('Produto atualizado.');
        return;
      }

      // probe por código -> decide PATCH vs POST
      let alvoId = null;
      if (produto.codigo_supra) {
        try {
          const probe = await produtosGET('', `?q=${encodeURIComponent(produto.codigo_supra)}&limit=1`);
          alvoId = (probe && probe.length && probe[0].id) ? probe[0].id : null;
        } catch {}
      }

      if (alvoId) {
        const res = await produtosPATCH(alvoId, { produto, imposto });
        fillForm(res);
        toast('Produto atualizado.');
      } else {
        const res = await produtosPOST({ produto, imposto });
        fillForm(res);
        toast('Produto criado.');
      }
    } catch (e) {
      toast('Erro ao salvar. Veja o console.');
      console.error(e);
    }
  });

  // Modal
  $('search-close')?.addEventListener('click', modal.close);
  $('search-cancel')?.addEventListener('click', modal.close);
  $('search-input')?.addEventListener('input', doSearch);
  $('search-input')?.addEventListener('keydown', (ev)=>{
    if (ev.key === 'Escape'){ modal.close(); }
    if (ev.key === 'Enter'){
      const first = document.querySelector('#search-results tbody tr');
      if (first) first.click();
    }
  });
});
