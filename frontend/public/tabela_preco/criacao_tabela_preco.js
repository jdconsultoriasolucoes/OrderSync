// === Config ===
const API_BASE = "https://ordersync-backend-edjq.onrender.com";

// === Estado ===
const MODE = { NEW:'new', VIEW:'view', EDIT:'edit', DUP:'duplicate' };
let mapaCondicoes = {}; // { codigo: taxa }
let mapaDescontos = {}; // { codigo: fator }
let itens = []; // itens carregados
let currentMode = 'new';       // 'new' | 'view' | 'edit' | 'duplicate'
let currentTabelaId = null;
let sourceTabelaId  = null;
let ivaStAtivo = !!document.getElementById('iva_st_toggle')?.checked;




// ✅ Se a página for recarregada (F5), zera o buffer legado
try {
  const nav = performance.getEntriesByType('navigation')[0];
  if (nav && nav.type === 'reload') {
    sessionStorage.removeItem('criacao_tabela_preco_produtos');
  }
} catch {}

// === Contexto e Snapshot de Cabeçalho ===
function getCtxId() {
  return currentTabelaId ? String(currentTabelaId) : 'new';
}

function getHeaderSnapshot() {
  return {
    nome_tabela: document.getElementById('nome_tabela')?.value || '',
    cliente: document.getElementById('cliente')?.value || '',
    validade_inicio: document.getElementById('validade_inicio')?.value || '',
    validade_fim: document.getElementById('validade_fim')?.value || '',
    frete_kg: document.getElementById('frete_kg')?.value || '0',
    plano_pagamento: document.getElementById('plano_pagamento')?.value || '',
    desconto_global: document.getElementById('desconto_global')?.value || '',
  };
}

function saveHeaderSnapshot() {
  const ctx = getCtxId();
  sessionStorage.setItem(`TP_HEADER_SNAPSHOT:${ctx}`, JSON.stringify(getHeaderSnapshot()));
}

function restoreHeaderSnapshotIfNew() {
  // Só restaura em NEW (sem id na URL) para não sujar edição/visualização
  if (currentTabelaId) return;
  const ctx = getCtxId();
  const raw = sessionStorage.getItem(`TP_HEADER_SNAPSHOT:${ctx}`);
  if (!raw) return;
  try {
    const snap = JSON.parse(raw);
    const set = (id, v) => { const el = document.getElementById(id); if (el && v != null) el.value = v; };
    set('nome_tabela', snap.nome_tabela);
    set('cliente', snap.cliente);
    set('validade_inicio', snap.validade_inicio);
    set('validade_fim', snap.validade_fim);
    set('frete_kg', snap.frete_kg);
    set('plano_pagamento', snap.plano_pagamento);
    // selects precisam existir antes
    atualizarPillTaxa();
    set('desconto_global', '');              // não reimpõe desconto global
    recalcTudo();
    refreshToolbarEnablement();
  } catch {}
}


// === Ponte Pai–Filho (contexto de itens) ===
function clearPickerBridgeFor(ctx) {
  try { sessionStorage.removeItem(`TP_ATUAL:${ctx}`); } catch {}
  try { sessionStorage.removeItem(`TP_BUFFER:${ctx}`); } catch {}
}

function preparePickerBridgeBeforeNavigate() {
  const ctx = getCtxId();
  sessionStorage.setItem('TP_CTX_ID', ctx);
  // salva itens atuais do pai para pré‑marcação no picker
  sessionStorage.setItem(`TP_ATUAL:${ctx}`, JSON.stringify(itens || []));
}

function mergeBufferFromPickerIfAny() {
  const ctx = getCtxId();
  const raw = sessionStorage.getItem(`TP_BUFFER:${ctx}`);
  if (!raw) return;
  try {
    const recebidos = JSON.parse(raw) || [];
    console.log('[DEBUG] BUFFER recebido do picker:', recebidos);
    const map = new Map((itens || []).map(x => [x.codigo_tabela, x]));
    for (const p of recebidos) {
      map.set(p.codigo_tabela, { ...(map.get(p.codigo_tabela) || {}), ...p });
    }
    itens = Array.from(map.values());
    renderTabela();
  } catch {}
  finally {
//    try { sessionStorage.removeItem(`TP_BUFFER:${ctx}`); } catch {}
  }
}

async function previewFiscalLinha(payload) {
  const r = await fetch(`${API_BASE}/fiscal/preview-linha`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(await r.text().catch(()=> 'Falha ao calcular preview fiscal'));
  return r.json();
}

async function atualizarPrecosAtuais(){
  const codigos = Array.from(new Set((itens||[]).map(x=>x.codigo_tabela).filter(Boolean)));
  if (!codigos.length) return;

  let mapa = {};
  // 1) tenta batch
  try {
    const r = await fetch(`${API_BASE}/catalogo/precos?ids=${encodeURIComponent(codigos.join(','))}`);
    if (r.ok) mapa = await r.json(); // esperado: { "COD1": 123.45, ... }
  } catch {}

  // 2) fallback por item (evita travar a UI)
  if (!Object.keys(mapa).length){
    for (const cod of codigos){
      try{
        const r = await fetch(`${API_BASE}/catalogo/produto/${encodeURIComponent(cod)}`);
        if (r.ok){
          const p = await r.json();
          mapa[cod] = Number(p.valor || p.preco || p.preco_venda || 0);
        }
      } catch {}
    }
  }

  // aplica e atualiza a grade
  let mudou=false;
  itens = (itens||[]).map(it=>{
    const novo = mapa[it.codigo_tabela];
    if (novo!=null && !isNaN(novo) && Number(novo)!==Number(it.valor)){
      mudou=true; return {...it, valor:Number(novo)};
    }
    return it;
  });

  if (mudou){
    const rows = Array.from(document.querySelectorAll('#tbody-itens tr'));
    rows.forEach((tr,i)=>{
      const tdValor = tr.querySelector('td:nth-child(7)');
      if (tdValor) tdValor.textContent = fmtMoney(itens[i].valor||0);
    });
    await recalcTudo();
  }
}

// Habilita/desabilita todos os campos e a grade
function setFormDisabled(disabled) {
  // topo
  document.querySelectorAll('input, select').forEach(el => {
    // não travar o botão, só inputs/selects
    if (['BUTTON','A'].includes(el.tagName)) return;
    el.disabled = disabled;
  });

  // grade
  document.querySelectorAll('#tbody-itens input, #tbody-itens select').forEach(el => el.disabled = disabled);
  const chkAll = document.getElementById('chk-all');
  if (chkAll) chkAll.disabled = disabled;
}

function goToListarTabelas() {
  window.location.href = 'listar_tabelas.html';
}

function onDuplicar() {
  // guarda a tabela de ORIGEM para poder voltar na hora do Cancelar
  sourceTabelaId = currentTabelaId ? String(currentTabelaId) : null;

  // entra em duplicação: libera campos e garante que será POST
  setMode(MODE.DUP);
  currentTabelaId = null;      // POST
  const nome = document.getElementById('nome_tabela');
  if (nome) nome.value = '';   // força novo cadastro com outro nome
}

// MOSTRAR/OCULTAR botões corretamente em todos os modos
function toggleToolbarByMode() {
  const show = (id, visible) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.toggle('hidden', !visible);
  };

  const hasId       = !!currentTabelaId;
  const isView      = currentMode === MODE.VIEW;
  const isEditLike  = currentMode === MODE.EDIT || currentMode === MODE.DUP || currentMode === MODE.NEW;
  const isEditOrDup = currentMode === MODE.EDIT || currentMode === MODE.DUP;

  // Listar: APENAS quando NÃO há id (tela nova)
  show('btn-listar', currentMode === MODE.NEW);

  // Buscar: em NEW/EDIT/DUP (quando mexendo)
  show('btn-buscar', isEditLike);

  // Editar/Duplicar: apenas em VIEW com id
  show('btn-editar',   isView && hasId);
  show('btn-duplicar', isView && hasId);

  // Remover/Salvar: em NEW/EDIT/DUP
  show('btn-remover-selecionados', isEditLike);
  show('btn-salvar',               isEditLike);

  // Cancelar:
  //  - visível em EDIT/DUP
  //  - e também em VIEW com id (atua como voltar pra lista)
  show('btn-cancelar', isEditOrDup || (isView && hasId));
}

// AÇÕES DE BOTÃO
function onEditar(){
  setMode(MODE.EDIT);
}

// Atalhos
function setMode(mode) {
  currentMode = mode;
  setFormDisabled(mode === 'view');
  toggleToolbarByMode();
}

// === Utils ===
const fmtMoney = (v) => (Number(v || 0)).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmt4 = (v) => (Number(v || 0)).toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
const fmtPct = (v) => (Number(v || 0)).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 4 });

function calcularLinha(item, fator, taxaCond, freteKg) {
  const valor = Number(item.valor || 0);
  const peso  = Number(item.peso_liquido || 0);

  const acrescimoCond = valor * Number(taxaCond || 0);
  const descontoValor = valor * Number(fator || 0);

  const freteValor    = (Number(freteKg || 0) / 1000) * peso;

  // preço-base sem impostos (vai para o backend fiscal)
  const precoBase = valor + acrescimoCond - descontoValor;

  return { acrescimoCond, freteValor, descontoValor, precoBase };
}


async function previewFiscalLinha(payload) {
  const r = await fetch(`${API_BASE}/fiscal/preview-linha`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const txt = await r.text().catch(()=> '');
    throw new Error(txt || 'Falha ao calcular preview fiscal');
  }
  return r.json();
}

function normaliza(s){ return String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(); }

async function buscarClientes(term){
  const q = (term || '').trim();
  if (q.length < 2) return [];

  const api  = API_BASE.replace(/\/$/, '');
  const base = `${api}/tabela_preco/busca_cliente/`;

  // tenta ?query= e depois ?q=
  for (const p of [`query=${encodeURIComponent(q)}`, `q=${encodeURIComponent(q)}`]) {
    try {
      const r = await fetch(`${base}?${p}`, { cache: 'no-store' });
      if (r.ok) {
        const data = await r.json();
        if (Array.isArray(data)) return data;
      }
    } catch {}
  }

  // Fallback: GET + filtro SOMENTE por Nome/CNPJ (sem código)
  try {
    const r2 = await fetch(base, { cache: 'no-store' });
    if (!r2.ok) return [];
    const all = (await r2.json()) || [];

    const nq   = normaliza(q);
    const qCnj = q.replace(/\D/g, '');

    return all.filter(c => {
      const nome = normaliza(c.nome || c.razao || c.razao_social || c.fantasia || c.NOME || '');
      const cnpj = String(c.cnpj || c.CNPJ || '').replace(/\D/g, '');
      return (nome.includes(nq) || (qCnj && cnpj.includes(qCnj)));
    });
  } catch {
    return [];
  }
}


function setupClienteAutocomplete(){
  const input = document.getElementById('cliente_nome');
  const box   = document.getElementById('cliente_suggestions');
  if (!input || !box) return;

  let timer = null, items = [], idx = -1;

  function fmtDoc(s){
  const d = String(s||'').replace(/\D/g,'');
  if (d.length === 14) { // CNPJ
    return d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
  }
  if (d.length === 11) { // CPF (se vier algum)
    return d.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
  }
  return s || '';
  }

  function normCliente(c){
    if (!c) return null;
    if (typeof c === 'string' || typeof c === 'number'){
      const s = String(c);
      return { cod:s, nome:s, cnpj:'', ramo:'' };
    }
    return {
      cod:  c.codigo ?? c.id ?? c.CODIGO ?? c.cod ?? c.code ?? '',
      nome: c.nome ?? c.razao ?? c.razao_social ?? c.fantasia ?? c.NOME ?? '',
      cnpj: c.cnpj ?? c.CNPJ ?? '',
      ramo: c.ramo ?? c.segmento ?? c.RAMO ?? ''
    };
  }

  

  // BUSCA: só por nome/CNPJ; se não achar, oferece "usar o digitado"
  let searchToken = 0;
async function doSearch(q){
  const typed = (q || '').trim();
  if (typed.length < 2){ items = []; render(); return; }

  const myToken = ++searchToken;

  // 1) busca remota
  const data = await buscarClientes(typed);
  items = (data || [])
  .map(normCliente)
  .filter(c => c && (c.nome || c.cnpj));

  // 2) se nada veio, oferecer “usar o que digitei”
  if (!items.length){
  items = [{ __raw:true, cod:'', nome:typed, cnpj:'', ramo:'' }];
}

  // 3) render rápido (pode mostrar “(sem nome)” no primeiro momento)
  idx = -1; render();

  // 4) enriquecer os que não têm nome/CNPJ (top 8) e re-render ao preencher
  const faltando = items
    .map((c,i)=>({i,c}))
    .filter(x => !(x.c && x.c.nome && x.c.cnpj))
    .slice(0,8);

  for (const {i, c} of faltando){
    const det = await fetchClienteDetalhePorCodigo(c.cod);
    if (myToken !== searchToken) return; // aborta se o usuário digitou outra coisa
    if (det){
      const up = normCliente({ ...c, ...det });
      items[i] = up;
      render();
    }
  }
 }

  function render(){
  box.innerHTML = items.map((c,i)=>{
    if (c.__raw){
      return `
        <div class="suggest ${i===idx?'active':''}" data-i="${i}" style="padding:6px 8px; cursor:pointer;">
          <div>Usar: <strong>"${c.nome}"</strong></div>
          <small style="opacity:.7">não encontrado — gravar como texto</small>
        </div>`;
    }
    const doc = fmtDoc(c.cnpj);
    const linha = [doc, (c.nome || '(sem nome)')].filter(Boolean).join(' — ');
    const sub   = c.ramo ? `<small style="opacity:.7">${c.ramo}</small>` : '';
    return `
      <div class="suggest ${i===idx?'active':''}" data-i="${i}" style="padding:6px 8px; cursor:pointer;">
        <div>${linha}</div>
        ${sub}
      </div>`;
  }).join('');
  box.style.display = items.length ? 'block' : 'none';
}

  function selectItem(i){
  const c = items[i]; if (!c) return;

  const nomeEl = document.getElementById('cliente_nome');
  const codEl  = document.getElementById('cliente_codigo');
  const ramoEl = document.getElementById('cliente_ramo');

  if (c.__raw){
    if (nomeEl) nomeEl.value = c.nome;
    if (codEl)  codEl.value  = '';
    if (ramoEl) ramoEl.value = '';
  } else {
    const display = [fmtDoc(c.cnpj), c.nome].filter(Boolean).join(' - ');
    if (nomeEl) nomeEl.value = display || c.nome || '';
    if (codEl)  codEl.value  = c.cod || '';
    if (ramoEl) ramoEl.value = c.ramo || '';
  }

  box.innerHTML=''; box.style.display='none';
  Promise.resolve(recalcTudo()).catch(()=>{});
}

  // Eventos
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => { Promise.resolve(doSearch(input.value)).catch(()=>{}); }, 250);
  });
  input.addEventListener('keydown', (e)=>{
    if (!items.length) return;
    if (e.key === 'ArrowDown'){ idx=(idx+1)%items.length; render(); e.preventDefault(); }
    else if (e.key === 'ArrowUp'){ idx=(idx-1+items.length)%items.length; render(); e.preventDefault(); }
    else if (e.key === 'Enter'){ if (idx>=0){ selectItem(idx); e.preventDefault(); } }
    else if (e.key === 'Escape'){ box.innerHTML=''; box.style.display='none'; }
  });
  box.addEventListener('mousedown', (e)=>{
    const el = e.target.closest('.suggest'); if (!el) return;
    selectItem(Number(el.dataset.i)||0);
  });
  box.addEventListener('click', (e)=>{
    const el = e.target.closest('.suggest'); if (!el) return;
    selectItem(Number(el.dataset.i)||0);
  });
  input.addEventListener('blur', ()=> setTimeout(()=>{ box.innerHTML=''; box.style.display='none'; }, 150));
}


// --- Persistência compacta ---
async function salvarTabelaPreco(payload) {
  if (!payload?.nome_tabela || !payload?.cliente || !payload?.validade_inicio || !payload?.validade_fim) {
    throw new Error('Preencha Nome, Cliente, Data Início e Data Fim.');
  }
  if (!Array.isArray(payload?.produtos) || payload.produtos.length === 0) {
    throw new Error('Nenhum produto na lista.');
  }
  const r = await fetch(`${API_BASE}/tabela_preco/salvar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!r.ok) {
    let msg = 'Erro ao salvar a tabela.';
    try { const e = await r.json(); if (e?.detail) msg = e.detail; } catch {}
    throw new Error(msg);
  }
  return r.json();
}


function option(text, value) {
  const o = document.createElement('option'); o.textContent = text; o.value = value; return o;
}

// === Carregamentos ===
async function carregarCondicoes() {
  const sel = document.getElementById('plano_pagamento');
  sel.innerHTML = '';
  sel.appendChild(option('Selecione…', ''));
  const r = await fetch(`${API_BASE}/tabela_preco/condicoes_pagamento`);
  const data = await r.json();
  data.forEach(c => { mapaCondicoes[c.codigo] = Number(c.taxa_condicao) || 0; sel.appendChild(option(`${c.codigo} - ${c.descricao}`, c.codigo)); });
  document.getElementById('hint-condicao').textContent = 'Pronto.';
  atualizarPillTaxa();
}

async function carregarDescontos() {
  const r = await fetch(`${API_BASE}/tabela_preco/descontos`);
  const data = await r.json();
  mapaDescontos = {}; // reset
  const sel = document.getElementById('desconto_global');
  sel.innerHTML = '';
  sel.appendChild(option('Selecione…', ''));
  
  data.forEach(d => { 
  const frac = Number(d.percentual) || 0;        // mantém como fração 0–1
  mapaDescontos[d.codigo] = frac;
  sel.appendChild(option(`${d.codigo} - ${(frac*100).toFixed(2)}`, d.codigo));
  });
  atualizarPillDesconto();
}

function atualizarPillTaxa() {
  const codigo = document.getElementById('plano_pagamento').value;
  const taxa = mapaCondicoes[codigo];
  document.getElementById('pill-taxa').textContent = (taxa || taxa === 0) ? `${fmt4(taxa)}` : '—';
}

function atualizarPillDesconto() {
  const code = document.getElementById('desconto_global')?.value || '';
  const fator = mapaDescontos[code];
  const el = document.getElementById('pill-fator');
  if (el) el.textContent = (fator != null && !isNaN(fator)) ? `${(Number(fator)*100).toFixed(2)}` : '—';
}

function obterItensDaSessao() {
  try {
    const raw = sessionStorage.getItem('criacao_tabela_preco_produtos');
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr : [];
  } catch { return []; }
}

async function carregarItens() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  if (id) {
    const r = await fetch(`${API_BASE}/tabela_preco/${id}`);
    if (r.ok) {
      const t = await r.json();
      document.getElementById('nome_tabela').value = t.nome_tabela || '';
      document.getElementById('cliente_nome').value = t.cliente_nome || t.cliente || '';
      document.getElementById('cliente_codigo').value = t.cliente_codigo || '';
      document.getElementById('validade_inicio').value = t.validade_inicio || '';
      document.getElementById('validade_fim').value = t.validade_fim || '';

      // >>> NOVO: preencher frete/condição (se existirem) e inferir do item[0] se faltar
      const first = (Array.isArray(t.produtos) && t.produtos.length) ? t.produtos[0] : null;
      const freteInput = document.getElementById('frete_kg');
      const planoSel   = document.getElementById('plano_pagamento');

      if (freteInput) {
        const freteVal = t.frete_kg ?? first?.frete_kg ?? 0;
        freteInput.value = String(freteVal || 0);
      }
      if (planoSel) {
        const planoVal = t.plano_pagamento ?? first?.plano_pagamento ?? '';
        planoSel.value = planoVal || '';
      }

    itens = (t.produtos || []).map(p => ({...p, ipi: Number(p.ipi ?? 0), iva_st: Number(p.iva_st ?? p.st ?? 0) }));
      renderTabela();

      // Atualiza a pill e recálculo
      atualizarPillTaxa();
      Promise.resolve(recalcTudo()).catch(err => console.debug('recalcTudo falhou:', err));

      // >>> NOVO: fator global (se todos iguais)
      const fatores = Array.from(new Set((itens || []).map(x => Number(x.fator_comissao || 0))));
      const fatorGlobal = (fatores.length === 1) ? fatores[0] : null;
      const dg = document.getElementById('desconto_global');
      if (dg) dg.value = ''; // deixa desconto em branco

      // >>> Entrar em visualização
      currentTabelaId = id;
      setMode('view');
      return;
    }
  }

  const novos = obterItensDaSessao();              // o que veio do picker nesta volta
  itens = mergeItensExistentesENovos(itens, novos); // ✅ MESCLA em vez de substituir
  itens = itens.map(p => ({ ...p, ipi: Number(p.ipi ?? 0), iva_st: Number(p.iva_st ?? 0) }));
  // (opcional, mas recomendado) já limpa o buffer legado para não reaplicar depois
  try { sessionStorage.removeItem('criacao_tabela_preco_produtos'); } catch {}
  renderTabela();
  setMode('new'); 
}

function criarLinha(item, idx) {
  const tr = document.createElement('tr');
  tr.dataset.idx = idx;

  const tdSel = document.createElement('td');
  const chk = document.createElement('input'); chk.type = 'checkbox'; chk.className = 'chk-linha';
  tdSel.appendChild(chk);

  const tdCod = document.createElement('td'); tdCod.textContent = item.codigo_tabela || '';
  const tdDesc = document.createElement('td'); tdDesc.textContent = item.descricao || '';
  const tdEmb = document.createElement('td'); tdEmb.textContent = item.embalagem || '';
  const tdPeso = document.createElement('td'); tdPeso.className = 'num'; tdPeso.textContent = fmt4(item.peso_liquido || 0);
  const tdValor = document.createElement('td'); tdValor.className = 'num'; tdValor.textContent = fmtMoney(item.valor || 0);

  // Fator comissão (editável) + Desconto (select)
  const tdFator = document.createElement('td'); tdFator.className = 'num';
  const inpFator = document.createElement('input');Object.assign(inpFator, {type: 'number', step: '0.01', min: '0', max: '100',value:(item.fator_comissao != null) ? (Number(item.fator_comissao) * 100).toFixed(2) : ''});
  inpFator.title = 'Defina pelo seletor de desconto ou “Aplicar fator a todos”';
  inpFator.style.width = '110px';
  inpFator.addEventListener('input', () => recalcLinha(tr));
  tdFator.appendChild(inpFator); 
  const tdDescOpt = document.createElement('td');
  const selDesc = document.createElement('select');
  selDesc.appendChild(option('—', ''));
  Object.entries(mapaDescontos).forEach(([cod, fator]) => selDesc.appendChild(option(`${cod} - ${(Number(fator)*100).toFixed(2)}`, cod)));
  if (item.desconto && item.valor) {
    const fatorInferido = (Number(item.desconto) / Number(item.valor)).toFixed(4);
    const match = Object.entries(mapaDescontos).find(([, f]) => String(f) === fatorInferido);
    if (match) selDesc.value = match[0];
  }
  selDesc.addEventListener('change', () => {
    const code = selDesc.value; const fator = mapaDescontos[code];
    if (fator !== undefined) { inpFator.value = (Number(fator) * 100).toFixed(2); }
    recalcLinha(tr);
  });
  tdDescOpt.appendChild(selDesc);

// Condição por linha (código) — NOVO
  const tdCondCod = document.createElement('td');
  const selCond   = document.createElement('select');
  selCond.appendChild(option('—', ''));
  Object.entries(mapaCondicoes).forEach(([cod]) => selCond.appendChild(option(cod, cod)));
  // default: se a linha já tem plano_pagamento, usa; senão, usa o global selecionado
  const planoGlobal = document.getElementById('plano_pagamento')?.value || '';
  selCond.value = item.plano_pagamento || planoGlobal || '';
  selCond.addEventListener('change', () => recalcLinha(tr));
  tdCondCod.appendChild(selCond);

  const tdCondVal   = document.createElement('td'); tdCondVal.className = 'num'; tdCondVal.textContent = '0,00';
  const tdFrete = document.createElement('td'); tdFrete.className = 'num'; tdFrete.textContent = '0,00';
  const tdDescAplic = document.createElement('td'); tdDescAplic.className = 'num'; tdDescAplic.textContent = '0,00';
  
  // IPI e IVA_ST (%) — NOVOS
  const tdIpiR$     = document.createElement('td'); tdIpiR$.className     = 'num col-ipi';              tdIpiR$.textContent     = '0,00';
  const tdBaseStR$  = document.createElement('td'); tdBaseStR$.className  = 'num col-base-st';         tdBaseStR$.textContent  = '0,00';
  const tdIcmsProp$ = document.createElement('td'); tdIcmsProp$.className = 'num col-icms-proprio';    tdIcmsProp$.textContent = '0,00';
  const tdIcmsCheio$= document.createElement('td'); tdIcmsCheio$.className= 'num col-icms-st-cheio';   tdIcmsCheio$.textContent= '0,00';
  const tdIcmsReter$= document.createElement('td'); tdIcmsReter$.className= 'num col-icms-st-reter';   tdIcmsReter$.textContent= '0,00';

  const tdGrupo = document.createElement('td'); tdGrupo.textContent = [item.grupo, item.departamento].filter(Boolean).join(' / ');
  const tdFinal = document.createElement('td'); tdFinal.className = 'num col-total'; tdFinal.textContent = '0,00';

  tr.append(
  tdSel, tdCod, tdDesc, tdEmb, tdGrupo,
  tdPeso, tdValor, tdFator, tdDescOpt,
  tdCondCod, tdCondVal, tdFrete, tdDescAplic,
  tdIpiR$, tdBaseStR$, tdIcmsProp$, tdIcmsCheio$, tdIcmsReter$, tdFinal
);
  return tr;
}

function renderTabela() {
  const tbody = document.getElementById('tbody-itens');
  tbody.innerHTML = '';
  itens.forEach((it, i) => tbody.appendChild(criarLinha(it, i)));
  Promise.resolve(recalcTudo()).catch(err => console.debug('recalcTudo falhou:', err));
  if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
}

async function recalcLinha(tr) {
  const idx  = Number(tr.dataset.idx);
  const item = itens[idx]; if (!item) return;

  const fator    = Number(tr.querySelector('td:nth-child(8) input')?.value || 0) / 100;
  const freteKg  = Number(document.getElementById('frete_kg').value || 0);

  // Condição por linha → taxa
  const selCond  = tr.querySelector('td:nth-child(10) select');
  const codCond  = selCond ? selCond.value : '';
  const taxaCond = mapaCondicoes[codCond] ?? mapaCondicoes[document.getElementById('plano_pagamento').value] ?? 0;

  // base comercial (sem imposto)
  const { acrescimoCond, freteValor, descontoValor, precoBase } =
    calcularLinha(item, fator, taxaCond, freteKg);

  // pinta colunas comerciais
  tr.querySelector('td:nth-child(11)').textContent = fmtMoney(acrescimoCond); // Cond. (R$)
  tr.querySelector('td:nth-child(12)').textContent = fmtMoney(freteValor);    // Frete (R$)
  tr.querySelector('td:nth-child(13)').textContent = fmtMoney(descontoValor); // Desc. aplicado

  // chama backend fiscal (quantidade = 1 na tabela_preco)
  const clienteCodigo = Number(document.getElementById('cliente_codigo')?.value || 0) || null;
  const forcarST      = !!document.getElementById('iva_st_toggle')?.checked;
  const produtoId     = (tr.querySelector('td:nth-child(2)')?.textContent || '').trim();

  try {
    const f = await previewFiscalLinha({
      cliente_codigo: clienteCodigo,
      forcar_iva_st: forcarST,
      produto_id: produtoId,
      preco_unit: precoBase,
      quantidade: 1,
      desconto_linha: 0,
      frete_linha: freteValor
    });

    const setCell = (sel, val) => {
    const el = tr.querySelector(sel);
    if (el) el.textContent = fmtMoney(val);
    };
    setCell('.col-ipi',            f.ipi);
    setCell('.col-base-st',        f.base_st);
    setCell('.col-icms-proprio',   f.icms_proprio);
    setCell('.col-icms-st-cheio',  f.icms_st_cheio);
    setCell('.col-icms-st-reter',  f.icms_st_reter);
     setCell('.col-total',          f.total_linha_com_st); // ou total_linha

  } catch (e) {
    console.warn('Falha fiscal na linha:', e);
    ['.col-ipi','.col-base-st','.col-icms-proprio','.col-icms-st-cheio','.col-icms-st-reter','.col-total']
      .forEach(sel => { const el = tr.querySelector(sel); if (el) el.textContent = '0,00'; });
  }
}


async function recalcTudo() {
  const rows = Array.from(document.querySelectorAll('#tbody-itens tr'));
  for (const tr of rows) {
    // aguarda uma a uma para evitar flood; se quiser paralelizar, use Promise.all com cuidado
    // eslint-disable-next-line no-await-in-loop
    await recalcLinha(tr);
  }
}

function aplicarFatorGlobal() {
  const selGlobal = document.getElementById('desconto_global');
  const code = selGlobal?.value || '';
  const fator = mapaDescontos[code];

  if (fator == null || isNaN(fator)) {
    alert('Escolha um desconto válido.');
    return;
  }

  // Aplica em cada linha e sincroniza o select da linha
  document.querySelectorAll('#tbody-itens tr').forEach(tr => {
    const inp = tr.querySelector('td:nth-child(8) input'); // fator por linha
    const sel = tr.querySelector('td:nth-child(9) select'); // desconto por linha
    if (inp) inp.value = (Number(fator) * 100).toFixed(2);
    if (sel) sel.value = code;
    recalcLinha(tr);
  });

  atualizarPillDesconto();

  Promise.resolve(recalcTudo()).catch(err => console.debug('recalcTudo falhou:', err));
}

// Mantém o picker em dia com o que está na grade do PAI
function snapshotSelecionadosParaPicker() {
  try { sessionStorage.setItem('criacao_tabela_preco_produtos', JSON.stringify(itens || [])); }
  catch (e) { console.warn('snapshotSelecionadosParaPicker falhou:', e); }
}

function removerSelecionados() {
  const novas = [];
  const rows = Array.from(document.querySelectorAll('#tbody-itens tr'));
  rows.forEach((tr, i) => {
    const chk = tr.querySelector('input.chk-linha');
    if (chk && chk.checked) return; // descarta selecionadas
    novas.push(itens[i]);
  });
  itens = novas;
  renderTabela();
 // ✅ mantém o picker alinhado após remoção
  snapshotSelecionadosParaPicker();
  // reset visual e estado dos botões
  const chkAll = document.getElementById('chk-all');
  if (chkAll) chkAll.checked = false;
  if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
}

async function salvarTabela() {
  const nome_tabela = document.getElementById('nome_tabela').value.trim();
  const cliente = document.getElementById('cliente_nome').value.trim();
  const validade_inicio = document.getElementById('validade_inicio').value;
  const validade_fim = document.getElementById('validade_fim').value;
  const plano_pagamento = document.getElementById('plano_pagamento').value || null;
  const frete_kg = Number(document.getElementById('frete_kg').value || 0);

  // Mapeia as linhas já renderizadas na tabela para o formato do backend
  const produtos = Array.from(document.querySelectorAll('#tbody-itens tr')).map(tr => {
  const idx  = Number(tr.dataset.idx); 
  const item = itens[idx];

  const fator   = Number(tr.querySelector('td:nth-child(8) input')?.value || 0) / 100;
  const selCond = tr.querySelector('td:nth-child(10) select');
  const codCond = selCond ? selCond.value : (document.getElementById('plano_pagamento').value || null);

  const taxaCondLinha = mapaCondicoes[codCond] || 0;

  const { acrescimoCond, freteValor, descontoValor, valorFinal } =
    calcularLinha(item, fator, taxaCondLinha, frete_kg, ivaStAtivo);

  return {
    nome_tabela, validade_inicio, validade_fim, cliente, fornecedor: item.fornecedor || '',
    codigo_tabela: item.codigo_tabela, descricao: item.descricao, embalagem: item.embalagem,
    peso_liquido: item.peso_liquido || 0, peso_bruto: item.peso_bruto || item.peso_liquido || 0,
    valor: item.valor || 0,
    desconto: Number(descontoValor.toFixed(4)),
    acrescimo: Number((acrescimoCond + freteValor).toFixed(4)),
    fator_comissao: fator || 0,
    plano_pagamento: codCond || null,       // <<<<<< per‑line
    frete_kg,
    frete_percentual: null,
    valor_liquido: Number(valorFinal.toFixed(2)),
    grupo: item.grupo || null, departamento: item.departamento || null,
    ipi: item.ipi || 0,
    iva_st: ivaStAtivo ? (item.iva_st || 0) : 0 // salva coerente com o que foi calculado
  };
});

  const payload = { nome_tabela, validade_inicio, validade_fim, cliente, fornecedor: '', produtos };

  try {
    const resp = await salvarTabelaPreco(payload);
    alert(`Tabela salva! ${resp.qtd_produtos} produtos incluídos.`);
  } catch (e) {
    console.error(e);
    alert(e.message || 'Erro ao salvar a tabela.');
  }
}



function validarCabecalhoMinimo() {
  const nome   = document.getElementById('nome_tabela')?.value?.trim();
  const cliente = document.getElementById('cliente_nome')?.value?.trim();
  const ini    = document.getElementById('validade_inicio')?.value;
  const fim    = document.getElementById('validade_fim')?.value;

  if (!nome || !cliente || !ini || !fim) return false;

  // valida ordem das datas (se ambos presentes)
  const dIni = new Date(ini);
  const dFim = new Date(fim);
  if (isFinite(dIni) && isFinite(dFim) && dFim < dIni) return false;

  return true;
}

// Habilitar/desabilitar (Salvar e Remover) conforme conteúdo
function refreshToolbarEnablement() {
  const temLinhas = document.querySelectorAll('#tbody-itens tr').length > 0;
  const algumaMarcada = document.querySelectorAll('#tbody-itens .chk-linha:checked').length > 0;
  const cabecalhoOk = validarCabecalhoMinimo();

  const btnSalvar = document.getElementById('btn-salvar');
  const btnRemover = document.getElementById('btn-remover-selecionados');

  if (btnSalvar)  btnSalvar.disabled  = !(temLinhas && cabecalhoOk);
  if (btnRemover) btnRemover.disabled = !algumaMarcada;
}
function limparFormularioCabecalho() {
  // Campos principais
  document.getElementById('nome_tabela').value = '';
  document.getElementById('cliente_nome').value = '';
  document.getElementById('cliente_codigo').value = '';
  document.getElementById('validade_inicio').value = '';
  document.getElementById('validade_fim').value = '';

  // Parâmetros globais
  const frete = document.getElementById('frete_kg');
  if (frete) frete.value = 0;

  const cond = document.getElementById('plano_pagamento');
  if (cond) cond.value = '';

  const descGlobal = document.getElementById('desconto_global');
  if (descGlobal) descGlobal.value = '';

    // Pill de taxa
  const pill = document.getElementById('pill-taxa');
  if (pill) pill.textContent = '—';

  // Recalcula estado/habilitação
  if (typeof recalcTudo === 'function') recalcTudo();
  if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
}

function limparGradeProdutos() {
  try { sessionStorage.removeItem('criacao_tabela_preco_produtos'); } catch (e) {}

  // Zera fonte de dados e DOM
  if (Array.isArray(itens)) itens = [];
  const tbody = document.getElementById('tbody-itens');
  if (tbody) tbody.innerHTML = '';

  // Desmarca “selecionar todos”
  const chkAll = document.getElementById('chk-all');
  if (chkAll) chkAll.checked = false;

  // Recalcula estado/habilitação
  if (typeof recalcTudo === 'function') recalcTudo();
  if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
}

// CANCELAR — EDIT->VIEW(mesma) | DUP->VIEW(origem) | VIEW->NEW(limpo) | NEW->NEW(limpo)
async function onCancelar(e) {
  if (e) e.preventDefault?.();

  // NEW → mantém NEW zerado
  if (currentMode === MODE.NEW) {
    if (typeof limparFormularioCabecalho === 'function') limparFormularioCabecalho();
    if (typeof limparGradeProdutos === 'function') limparGradeProdutos();
    setMode(MODE.NEW);
    return;
  }

  // EDIT → VIEW (mesma tabela, travada)
  if (currentMode === MODE.EDIT) {
    setMode(MODE.VIEW);
    if (typeof setFormDisabled === 'function') setFormDisabled(true);
    if (typeof toggleToolbarByMode === 'function') toggleToolbarByMode();
    if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
    return;
  }

  // DUP → VIEW (tabela ORIGEM, travada) — sem navegar
  if (currentMode === MODE.DUP) {
    if (sourceTabelaId) {
      try {
        const r = await fetch(`${API_BASE}/tabela_preco/${encodeURIComponent(sourceTabelaId)}`);
        if (r.ok) {
          const t = await r.json();

          // repõe cabeçalho
          document.getElementById('nome_tabela').value     = t.nome_tabela || '';
          document.getElementById('cliente_nome').value = t.cliente_nome || t.cliente || '';
          document.getElementById('cliente_codigo').value = t.cliente_codigo || '';
          document.getElementById('validade_inicio').value = t.validade_inicio || '';
          document.getElementById('validade_fim').value    = t.validade_fim || '';

          // repõe itens e re-renderiza grade
          itens = Array.isArray(t.produtos) ? t.produtos.map(p => ({ ...p })) : [];
          if (typeof renderTabela === 'function') renderTabela();

          // volta a “apontar” para a origem
          currentTabelaId = String(sourceTabelaId);
        } else {
          console.warn('Cancelar DUP: não consegui recarregar a origem, mantendo tela atual.');
        }
      } catch (err) {
        console.warn('Cancelar DUP: erro ao recarregar a origem:', err);
      }
    }
    // sai do estado de duplicação
    sourceTabelaId = null;

    // trava e mostra botões de decisão (Editar/Duplicar)
    setMode(MODE.VIEW);
    if (typeof setFormDisabled === 'function') setFormDisabled(true);
    if (typeof toggleToolbarByMode === 'function') toggleToolbarByMode();
    if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
    return;
  }

  // VIEW (momento de decisão) → NEW (limpo) — sem navegar
  if (currentMode === MODE.VIEW) {
    if (typeof limparFormularioCabecalho === 'function') limparFormularioCabecalho();
    if (typeof limparGradeProdutos === 'function') limparGradeProdutos();
    currentTabelaId = null;
    sourceTabelaId  = null;
    setMode(MODE.NEW);
    if (typeof setFormDisabled === 'function') setFormDisabled(false);
    if (typeof toggleToolbarByMode === 'function') toggleToolbarByMode();
    if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
    return;
  }
}

function goToListarTabelas() {
  const ctx = getCtxId();
  clearPickerBridgeFor(ctx);
  window.location.href = 'listar_tabelas.html';
}


function mergeItensExistentesENovos(existentes, novos) {
  const map = new Map((existentes || []).map(x => [x.codigo_tabela, x]));
  (novos || []).forEach(nv => {
    const prev = map.get(nv.codigo_tabela);
    map.set(nv.codigo_tabela, prev ? { ...prev, ...nv } : nv);
  });
  return Array.from(map.values());
}



// === Bootstrap ===
document.addEventListener('DOMContentLoaded', () => {
  // Eventos globais
  setMode(MODE.NEW);
  document.getElementById('btn-listar')?.addEventListener('click', () => { goToListarTabelas(); });
  
  document.getElementById('btn-aplicar-todos')?.addEventListener('click', aplicarFatorGlobal);
  
  document.getElementById('plano_pagamento')?.addEventListener('change', () => { atualizarPillTaxa(); recalcTudo(); refreshToolbarEnablement();
    });
  document.getElementById('frete_kg')?.addEventListener('input', () => {
    recalcTudo();
    refreshToolbarEnablement();        // <— ADICIONE ESTA LINHA
  });
  // Habilitar/Desabilitar "Remover selecionados" ao marcar/desmarcar linhas individuais
  document.getElementById('tbody-itens')?.addEventListener('change', (e) => {
  if (e.target && e.target.classList.contains('chk-linha')) {
    // Atualiza o estado do botão
    if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();

    // Sincroniza o "selecionar todos"
    const all   = document.querySelectorAll('#tbody-itens .chk-linha');
    const marked= document.querySelectorAll('#tbody-itens .chk-linha:checked');
    const chkAll= document.getElementById('chk-all');
    if (chkAll) chkAll.checked = (all.length > 0 && marked.length === all.length);
  }
 });
 // Selecionar todos — robusto (funciona em click e change)
 (function bindChkAll(){
  const chkAll = document.getElementById('chk-all');
  if (!chkAll) return;

  const toggleAll = (e) => {
    const checked = (e && e.currentTarget) ? !!e.currentTarget.checked : !!chkAll.checked;
    document.querySelectorAll('#tbody-itens .chk-linha')
      .forEach(cb => { cb.checked = checked; });

    // Atualiza habilitação do botão "Remover selecionados"
    if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
  };

  // Usa os dois eventos para não depender do timing do 'change'
  chkAll.addEventListener('click',  toggleAll);
  chkAll.addEventListener('change', toggleAll);
 })();

  document.getElementById('btn-buscar')?.addEventListener('click', () => {
  saveHeaderSnapshot();  // <-- salva topo
  preparePickerBridgeBeforeNavigate(); // (ver tópico 3)
  snapshotSelecionadosParaPicker();
  window.location.href = 'tabela_preco.html';
 });

  document.getElementById('btn-remover-selecionados')?.addEventListener('click', () => {
    removerSelecionados();
    refreshToolbarEnablement();
  });

  document.getElementById('btn-salvar')?.addEventListener('click', async (e) => {
  // Evita submit do form caso o botão esteja como <button type="submit">
  if (e && typeof e.preventDefault === 'function') e.preventDefault();

  // Garante que o botão não é submit (caso o HTML esteja com type padrão)
  const btn = document.getElementById('btn-salvar');
  if (btn) btn.setAttribute('type', 'button');

  try {
    await salvarTabela();

    // ✅ Após salvar em QUALQUER modo, voltar para NEW limpo e destravado
    if (typeof limparFormularioCabecalho === 'function') limparFormularioCabecalho();
    if (typeof limparGradeProdutos === 'function') limparGradeProdutos();
    currentTabelaId = null;
    sourceTabelaId  = null;

    setMode(MODE.NEW);         // muda modo
    setFormDisabled(false);    // garante que está destravado

  } catch (e) {
    console.error(e);
    alert(e.message || 'Erro ao salvar a tabela.');
    // não muda de modo em erro
  } finally {
    if (typeof toggleToolbarByMode === 'function') toggleToolbarByMode();
    if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
  }
 });
  
  document.getElementById('btn-cancelar')?.addEventListener('click', onCancelar);
  document.getElementById('btn-editar')?.addEventListener('click', onEditar);
  document.getElementById('btn-duplicar')?.addEventListener('click', onDuplicar); 
  
  // Init
  (async function init(){
    await Promise.all([carregarCondicoes(), carregarDescontos()]);
    await carregarItens();
    setupClienteAutocomplete();
   // Se vier com ação na URL (?action=edit|duplicate), respeitar:
    const q = new URLSearchParams(location.search);
    const action = q.get('action') || q.get('mode') || q.get('modo');
    if (currentTabelaId) {
      if (action === 'edit') setMode(MODE.EDIT);
      else if (action === 'duplicate') onDuplicar(); // usa o fluxo que guarda a origem
      else setMode(MODE.VIEW);
    } else {
      setMode(MODE.NEW);
    }

    refreshToolbarEnablement();
  })();
 });
 restoreHeaderSnapshotIfNew();
 mergeBufferFromPickerIfAny();

 document.getElementById('btn-aplicar-condicao-todos')?.addEventListener('click', () => {
  const cod = document.getElementById('plano_pagamento')?.value || '';
  document.querySelectorAll('#tbody-itens tr').forEach(tr => {
    const sel = tr.querySelector('td:nth-child(10) select');
    if (sel) sel.value = cod;
    recalcLinha(tr);
  });
 });
 document.getElementById('iva_st_toggle')?.addEventListener('change', (e) => {
  ivaStAtivo = !!e.target.checked;
  Promise.resolve(recalcTudo()).catch(err => console.debug('recalcTudo falhou:', err));
 });

 document.getElementById('desconto_global')?.addEventListener('change', () => {
  atualizarPillDesconto();
  Promise.resolve(recalcTudo()).catch(err => console.debug('recalcTudo falhou:', err));
  
}); 