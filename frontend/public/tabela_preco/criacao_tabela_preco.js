// === Config ===
const API_BASE = "https://ordersync-backend-edjq.onrender.com";
window.API_BASE = API_BASE;
const ENDPOINT_VALIDADE = `${API_BASE}/tabela_preco/meta/validade_global`;

// === Estado ===
const MODE = { NEW:'new', VIEW:'view', EDIT:'edit', DUP:'duplicate' };
let mapaCondicoes = {}; // { codigo: taxa }
let mapaDescontos = {}; // { codigo: fator }
let itens = []; // itens carregados
let currentMode = 'new';       // 'new' | 'view' | 'edit' | 'duplicate'
let currentTabelaId = null;
let sourceTabelaId  = null;
let ivaStAtivo = !!document.getElementById('iva_st_toggle')?.checked;
let __recalcRunning = false;
let __recalcPending = false;

// ✅ Se a página for recarregada (F5), zera o buffer legado
const __IS_RELOAD = (() => {
  try {
    const nav = performance.getEntriesByType('navigation')[0];
    return !!(nav && nav.type === 'reload');
  } catch { return false; }
})();

if (__IS_RELOAD) {
  try { sessionStorage.removeItem('criacao_tabela_preco_produtos'); } catch {}
  // limpe também snapshots/ponte por contexto, se usar TP_CTX_ID
  Object.keys(sessionStorage).forEach(k => {
    if (k.startsWith('TP_HEADER_SNAPSHOT:')) sessionStorage.removeItem(k);
    if (k.startsWith('TP_ATUAL:'))           sessionStorage.removeItem(k);
    if (k.startsWith('TP_BUFFER:'))          sessionStorage.removeItem(k);
  });
}

window.isClienteLivreSelecionado = false;

function parseBool(v){
  if (typeof v === 'boolean') return v;
  if (typeof v === 'number') return v === 1;
  if (typeof v === 'string') return ['s','sim','true','1','y','yes'].includes(v.trim().toLowerCase());
  return false;
}

function setTabelaIds(id) {
  const v = id != null ? String(id) : '';
  currentTabelaId = v;
  window.currentTabelaId = v; // compat com código legado
  sourceTabelaId = v;
  window.sourceTabelaId = v;
}

// ======== Validador só de "preenchido" ========
const RequiredValidator = (() => {
  const CLS_ERR = 'field-error';
  const CLS_MSG = 'field-error-msg';

  function clear(root=document) {
    root.querySelectorAll('.' + CLS_ERR).forEach(el => el.classList.remove(CLS_ERR));
    root.querySelectorAll('.' + CLS_MSG).forEach(el => el.remove());
  }

  function mark(el, msg) {
    el.classList.add(CLS_ERR);
    const small = document.createElement('small');
    small.className = CLS_MSG;
    small.textContent = msg || 'Campo obrigatório.';
    el.insertAdjacentElement?.('afterend', small);
  }

  // 👇 aqui é CONST interna (não use RequiredValidator.* aqui)
  const REQUIRED_FIELDS = {
    '#nome_tabela':  'Informe o nome da tabela.',
    '#cliente_nome': 'Informe/selecione o cliente.',
    '#tbody-itens tr td:nth-child(8) select':  'Selecione a classificação para todos os itens.',
    '#tbody-itens tr td:nth-child(10) select': 'Selecione a condição de pagamento para todos os itens.'
  };

  function check(config = REQUIRED_FIELDS, root=document) {
    clear(root);
    const missing = [];

    for (const selector in config) {
      const msg = config[selector];
      const nodes = root.querySelectorAll(selector);
      if (!nodes.length) continue;

      nodes.forEach(el => {
        const val = (el.value ?? '').toString().trim();
        if (val === '') { // aceita 0
          mark(el, msg);
          missing.push({ selector, el, msg });
        }
      });
    }

    if (missing.length) missing[0].el?.focus?.();
    return { ok: missing.length === 0, missing };
  }

  return { check, clear, REQUIRED_FIELDS }; // <- aqui sim expõe o REQUIRED_FIELDS
})();



// === Contexto e Snapshot de Cabeçalho ===
function getCtxId() {
  return currentTabelaId ? String(currentTabelaId) : 'new';
}

function getHeaderSnapshot() {
  const $ = (id) => document.getElementById(id);
  const val = (id) => ($(`${id}`)?.value ?? "").trim();
  const on  = (id) => !!$(`${id}`)?.checked;

  return {
    // visuais
    nome_tabela:     val("nome_tabela"),
    cliente:         val("cliente_nome"),   // texto mostrado no input
    // ocultos/importantes
    codigo_cliente:  val("codigo_cliente"),
    ramo_juridico:   val("ramo_juridico"),
    
    // toggles/parametrizações
    iva_st:          on("iva_st_toggle"),
    frete_kg:        val("frete_kg") || "0",
    plano_pagamento: val("plano_pagamento"),
    desconto_global: val("desconto_global"),
    cliente_livre:   !!window.isClienteLivreSelecionado,   
    iva_enabled:     !$("iva_st_toggle")?.disabled
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
    const set = (id, v) => {
      const el = document.getElementById(id);
      if (el != null && v != null) el.value = v;
    };

    // ---- Cabeçalho básico
    set('nome_tabela',     snap.nome_tabela);
    set('cliente_nome',    snap.cliente);
    set('codigo_cliente',  snap.codigo_cliente);
    set('ramo_juridico',   snap.ramo_juridico);
    set('frete_kg',        snap.frete_kg);

    // ---- Selects (este método deve ser chamado DEPOIS de carregarCondicoes/Descontos)
    set('plano_pagamento', snap.plano_pagamento || '');
    set('desconto_global', snap.desconto_global || '');

    // ---- IVA_ST e flags do cliente livre
    const ivaChk = document.getElementById('iva_st_toggle');
    if (ivaChk) {
      ivaChk.checked  = !!snap.iva_st;
      ivaChk.disabled = !snap.iva_enabled;   // se estava habilitado, volta habilitado
      window.ivaStAtivo = ivaChk.checked;
    }
    window.isClienteLivreSelecionado = !!snap.cliente_livre;

    // ---- Atualizações visuais e locks
    atualizarPillTaxa?.();
    atualizarPillDesconto?.();
    enforceIvaLockByCliente?.();             // garante regra: cadastrado = travado, livre = habilita

    // ---- Recalcula e atualiza botões
    recalcTudo?.();
    refreshToolbarEnablement?.();
  } catch (e) {
    console.warn('restoreHeaderSnapshotIfNew: snapshot inválido', e);
  }
}


 // === Ponte Pai–Filho (contexto de itens) ===
 function clearPickerBridgeFor(ctx) {
  try { sessionStorage.removeItem(`TP_ATUAL:${ctx}`); } catch {}
  try { sessionStorage.removeItem(`TP_BUFFER:${ctx}`); } catch {}
 }

 function preparePickerBridgeBeforeNavigate() {
  const ctx = getCtxId();
  sessionStorage.setItem('TP_CTX_ID', ctx);
  sessionStorage.setItem(`TP_RETURN_MODE:${ctx}`, currentMode);
  try { sessionStorage.removeItem(`TP_BUFFER:${ctx}`); } catch {}
  // salva itens atuais do pai para pré‑marcação no picker
  sessionStorage.setItem(`TP_ATUAL:${ctx}`, JSON.stringify(itens || []));
  if (currentMode === MODE.DUP && sourceTabelaId) {
   sessionStorage.setItem('TP_SOURCE_ID', String(sourceTabelaId));
 }
}

 async function mergeBufferFromPickerIfAny() {
  const ctx = getCtxId();
  const raw = sessionStorage.getItem(`TP_BUFFER:${ctx}`);
  if (!raw) return;
  try {
    const recebidos = JSON.parse(raw) || [];
    const map = new Map((itens || []).map(x => [x.codigo_tabela, x]));
    for (const p of recebidos) {
      map.set(p.codigo_tabela, { ...(map.get(p.codigo_tabela) || {}), ...p });
    }
    itens = Array.from(map.values());
    renderTabela();
   // garante dados que o preview usa
    
    await atualizarPrecosAtuais();
    // agenda o recálculo no próximo tick
    queueMicrotask(() => Promise.resolve(recalcTudo()).catch(()=>{}));
  } catch {}
  finally {
    try { sessionStorage.removeItem(`TP_BUFFER:${ctx}`); } catch {}
  }
 }

async function atualizarPrecosAtuais(){
  const codigos = Array.from(new Set((itens||[]).map(x=>x.codigo_tabela).filter(Boolean)));
  if (!codigos.length) return;

  const mapa = {};
 for (const cod of codigos){
   try {
     const r = await fetch(`${API_BASE}/tabela_preco/produtos_filtro?codigo=${encodeURIComponent(cod)}`, { cache: 'no-store' });
     if (!r.ok) continue;
     const raw = await r.json();
     const p = raw?.items ? (raw.items[0] || {}) : raw;
     mapa[cod] = Number(p.valor ?? p.preco ?? p.preco_venda ?? 0);
   } catch {}
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
    if (el.id === 'iva_st_toggle' && !disabled) return;
    el.disabled = disabled;
  });

  // grade
  document.querySelectorAll('#tbody-itens input, #tbody-itens select').forEach(el => el.disabled = disabled);
  const chkAll = document.getElementById('chk-all');
  if (chkAll) chkAll.disabled = disabled;
}

function onDuplicar() {
  // guarda a tabela de ORIGEM para poder voltar na hora do Cancelar
  sourceTabelaId = currentTabelaId ? String(currentTabelaId) : null;
  if (sourceTabelaId) sessionStorage.setItem('TP_SOURCE_ID', sourceTabelaId);
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
  if (currentTabelaId) sessionStorage.setItem('TP_LAST_VIEW_ID', String(currentTabelaId));
  setMode(MODE.EDIT);
}

// Atalhos
function setMode(mode) {
  currentMode = mode;
  setFormDisabled(mode === 'view');
  toggleToolbarByMode();
  enforceIvaLockByCliente?.();
}

// === Utils ===
const fmtMoney = (v) => (Number(v || 0)).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmt4 = (v) => (Number(v || 0)).toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
const fmtPct = (v) => (Number(v || 0)).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 4 });

function calcularLinha(item, fator, taxaCond, freteKg) {
  const valor = Number(item.valor || 0);
  const peso  = Number(item.peso_liquido || 0);

  // 1) DESCONTO/FATOR → base líquida
  const descontoValor = valor * Number(fator || 0);
  const liquido       = Math.max(0, valor - descontoValor);

  // 2) Condição SOBRE o líquido
  const acrescimoCond = liquido * Number(taxaCond || 0);

  // 3) Frete (continua por KG — só soma no total)
  const freteValor    = (Number(freteKg || 0) / 1000) * peso;

  // 4) Preço comercial sem impostos (líquido + condição)
  const precoBase     = liquido + acrescimoCond;

  return { acrescimoCond, freteValor, descontoValor, precoBase, liquido }
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

// formata CNPJ/CPF para exibir bonito
function fmtDoc(s){
  const d = String(s||'').replace(/\D/g,'');
  if (d.length===14) return d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,'$1.$2.$3/$4-$5');
  if (d.length===11) return d.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/,'$1.$2.$3-$4');
  return s||'';
}

// chamada única ao backend (aceita q= ou query=)
async function buscarClientes(term){
  const q = (term || '').trim();
  if (q.length < 2) return [];

  const api = API_BASE.replace(/\/$/, '');
  const bases = [
    `${api}/tabela_preco/busca_cliente`,
    `${api}/tabela_preco/busca_cliente/`,
  ];
  const params = ['q','query','nome','term','busca'];

  // tenta GET com várias chaves (?q=, ?query=, etc) e normaliza a resposta
  for (const base of bases){
    for (const k of params){
      try{
        const r = await fetch(`${base}?${k}=${encodeURIComponent(q)}`, { cache: 'no-store' });
        if (!r.ok) continue;

        const data = await r.json();
        const arr =
          Array.isArray(data)             ? data :
          Array.isArray(data?.results)    ? data.results :
          Array.isArray(data?.clientes)   ? data.clientes :
          Array.isArray(data?.items)      ? data.items :
          (data && (data.nome || data.cnpj)) ? [data] : [];

        if (arr.length) return arr;
      }catch{/* tenta próximo */}
    }
  }

  // fallback: GET sem query e filtro no front (SÓ por nome/CNPJ)
  try{
    const r2 = await fetch(bases[0], { cache: 'no-store' });
    if (!r2.ok) return [];
    const all = await r2.json();

    const nq   = normaliza(q);
    const qCnj = q.replace(/\D/g, '');
    return (all || []).filter(c => {
      const nome = normaliza(c.nome_cliente || c.razao || c.razao_social || c.fantasia || c.NOME || '');
      const cnpj = String(c.cnpj || c.CNPJ || '').replace(/\D/g, '');
      return (nome.includes(nq) || (qCnj && cnpj.includes(qCnj)));
    });
  }catch{ return []; }
}

function setupClienteAutocomplete(){
  const input = document.getElementById('cliente_nome');
  const box   = document.getElementById('cliente_suggestions');
  if (!input || !box) return;

  let items=[], idx=-1, timer=null;

  function render(){
    box.innerHTML = items.map((c,i)=>{
      if (c.__raw){
        return `<div class="suggest ${i===idx?'active':''}" data-i="${i}" style="padding:6px 8px;cursor:pointer">
                  <div>Usar: <strong>"${c.nome}"</strong></div>
                  <small style="opacity:.7">não encontrado — gravar como texto</small>
                </div>`;
      }
      const linha = [fmtDoc(c.cnpj), c.nome].filter(Boolean).join(' - ');
      return `<div class="suggest ${i===idx?'active':''}" data-i="${i}" style="padding:6px 8px;cursor:pointer">
                <div>${linha}</div>
              </div>`;
    }).join('');
    box.style.display = items.length ? 'block' : 'none';
  }

  function selectItem(i){
  const c = items[i]; if (!c) return;

  const nomeEl = document.getElementById('cliente_nome');
  const codEl  = document.getElementById('codigo_cliente');
  const ramoEl = document.getElementById('ramo_juridico');
  const ivaChk = document.getElementById('iva_st_toggle');
  if (ivaChk) { ivaChk.checked = false; ivaChk.disabled = true; window.ivaStAtivo = false; }
  window.isClienteLivreSelecionado = false;

  enforceIvaLockByCliente();

  if (c.__raw){
  // cliente “livre” (gravar como texto)
  if (nomeEl) nomeEl.value = c.nome;
  if (codEl)  codEl.value  = '';          // sem código
  if (ramoEl) ramoEl.value = '';

  window.isClienteLivreSelecionado = true;
  if (ivaChk){
    ivaChk.disabled = false;              // ✅ habilita para você decidir
    // não marco/desmarco aqui — decisão manual
  }
  saveHeaderSnapshot?.();

} else {
  // cliente cadastrado
  if (nomeEl) nomeEl.value = [fmtDoc(c.cnpj), c.nome].filter(Boolean).join(' - ');
  if (codEl)  codEl.value  = c.codigo ?? '';
  if (ramoEl) ramoEl.value = c.ramo_juridico ?? c.ramo ?? '';

  // aplica preferência vinda do cadastro, mas TRAVADO
  const pref = c.iva_st ?? c.usa_iva_st ?? c.st ?? c.calcula_st ?? null;
  if (ivaChk){
    if (pref != null) ivaChk.checked = parseBool(pref);
    ivaChk.disabled = true;              // 🔒 travado para cliente cadastrado
  }
  window.isClienteLivreSelecionado = false;
  saveHeaderSnapshot?.();
}

function ensureHasId(){
  if (!currentTabelaId) {
    const q = new URLSearchParams(location.search);
    const idUrl = q.get('id');
    const cand = idUrl || sourceTabelaId;
    if (cand) currentTabelaId = String(cand);
  }
}

// fecha sugestões e recalcula
box.innerHTML = '';
box.style.display = 'none';
Promise.resolve(recalcTudo()).catch(() => {});}


  async function doSearch(q){
  const typed = (q || '').trim();
  if (typed.length < 2){ items = []; render(); return; }

  const data = await buscarClientes(typed);

  // mapeia campos do back
// mapeia campos do back (pega várias chaves possíveis)
const mapped = (data || []).map(c => ({
  // captura o código do cliente com várias variações comuns
  codigo: c.codigo ?? c.id ?? c.id_cliente ?? c.codigo_cliente ?? c.codigoCliente ?? c.CODIGO ?? c.COD_CLIENTE ?? c.cod ?? null,
  nome:   c.nome_cliente ?? c.nomeCliente ?? c.NOME_CLIENTE ?? c.nome ?? c.razao ?? c.razao_social ?? c.razaoSocial ?? c.fantasia ?? '',
  cnpj:   c.cnpj ?? c.CNPJ ?? c.cnpj_cpf ?? c.cnpjCpf ?? '',
  ramo_juridico: c.ramo_juridico ?? ''
})).filter(c => (c.nome || c.cnpj));

  // 🔎 filtro FINAL no front (sempre), por nome ou CNPJ
  const nq   = normaliza(typed);
  const qCnj = typed.replace(/\D/g, '');
  items = mapped.filter(c => {
    const nomeNorm    = normaliza(c.nome || '');
    const cnpjDigits  = String(c.cnpj || '').replace(/\D/g, '');
    return (nomeNorm.includes(nq) || (qCnj && cnpjDigits.includes(qCnj)));
  });

  if (!items.length){
    // nada casou → oferece “usar o que digitei”
    items = [{ __raw:true, nome: typed }];
  }

  idx = -1;
  render();
}

  input.addEventListener('input', ()=>{
    clearTimeout(timer);
    timer = setTimeout(()=>{ doSearch(input.value); }, 250);
  });
  input.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowDown' && items.length){ idx = (idx + 1) % items.length; render(); e.preventDefault(); }
  else if (e.key === 'ArrowUp'   && items.length){ idx = (idx - 1 + items.length) % items.length; render(); e.preventDefault(); }
  else if (e.key === 'Enter'){
    e.preventDefault();
    if (items.length && idx >= 0){
      selectItem(idx);
    } else {
      // aceita o que foi digitado
      const val = (input.value || '').trim();
      if (!val) return;
      items = [{ __raw:true, nome: val }];
      selectItem(0);
    }
  } else if (e.key === 'Escape'){
    box.innerHTML = ''; box.style.display = 'none';
  }
});
  box.addEventListener('mousedown', e=>{
    const el = e.target.closest('.suggest'); if (!el) return;
    selectItem(Number(el.dataset.i)||0);
  });
  input.addEventListener('blur', ()=> setTimeout(()=>{ box.innerHTML=''; box.style.display='none'; }, 150));
}

// PATCH: bloqueio/controle do IVA_ST conforme cliente (livre x cadastrado)
function enforceIvaLockByCliente(){
  const ivaChk  = document.getElementById('iva_st_toggle');
  const codigo  = (document.getElementById('codigo_cliente')?.value || '').trim();
  if (!ivaChk) return;

  if (codigo){                         // cliente cadastrado
    ivaChk.disabled = true;            // 🔒 travado
    // não muda o checked aqui (pode já ter vindo do cadastro)
  } else {
    // sem código: só habilita se já selecionou “Usar: ...”
    ivaChk.disabled = !window.isClienteLivreSelecionado;
  }
  window.ivaStAtivo = !!ivaChk.checked;
}



// --- Persistência compacta ---
async function salvarTabelaPreco(payload) {
  const isEdicao = (currentMode === MODE.EDIT) && !!currentTabelaId;

  const url = isEdicao
    ? `${API_BASE}/tabela_preco/${encodeURIComponent(currentTabelaId)}`
    : `${API_BASE}/tabela_preco/salvar`;

  const method = isEdicao ? 'PUT' : 'POST';

  const resp = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const raw = await resp.text();
  let data = null; try { data = JSON.parse(raw); } catch {}

  if (!resp.ok) {
    // trata 422 bonitinho, se vier
    try {
      const j = JSON.parse(raw);
      if (j?.detail) throw new Error(typeof j.detail === 'string' ? j.detail
                             : j.detail.map(d => `• ${d.loc?.join('.')}: ${d.msg}`).join('\n'));
    } catch {}
    throw new Error(`Falha ao salvar (${resp.status}). ${raw}`);
  }
  return data;
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
  const el = document.getElementById('pill-taxa');
  if (!el) return;
  el.textContent = (taxa != null && !isNaN(taxa))
    ? `${(Number(taxa) * 100).toFixed(2)} %` : '—';
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
      document.getElementById('codigo_cliente').value = t.codigo_cliente || '';
      document.getElementById('ramo_juridico').value = t.ramo_juridico || '';

      // >>> NOVO: preencher frete/condição (se existirem) e inferir do item[0] se faltar
      const first = (Array.isArray(t.produtos) && t.produtos.length) ? t.produtos[0] : null;
      const freteInput = document.getElementById('frete_kg');
      const planoSel = document.getElementById('plano_pagamento');
      if (planoSel) {
        const planoVal = t.codigo_plano_pagamento ?? first?.codigo_plano_pagamento ?? '';
        if (planoVal) {
          const opt = Array.from(planoSel.options)
            .find(o => (o.textContent || '').trim() === String(planoVal).trim() || o.value === String(planoVal));
          if (opt) planoSel.value = opt.value;
        } else {
          planoSel.value = '';
        }
      }

      if (freteInput) {
        const freteVal = first?.frete_kg ?? 0;
        freteInput.value = String(freteVal);
      }
      
     itens = (t.produtos || []).map(p => ({
      // chaves que a grade espera:
      id_linha:           p.id_linha ?? p.idLinha ?? null, 
      codigo_tabela:      p.codigo_produto_supra ?? p.codigo_tabela ?? '',
      descricao:          p.descricao_produto    ?? p.descricao     ?? '',
      embalagem:          p.embalagem            ?? '',
      peso_liquido:       Number(p.peso_liquido ?? 0),
      valor:              Number(p.valor_produto ?? p.valor ?? 0),

      // comerciais/fiscais
      desconto:           Number(p.comissao_aplicada ?? 0),      // mantém em R$ pra exibir
      acrescimo:          Number(p.ajuste_pagamento  ?? 0),      // mantém em R$ pra exibir
      plano_pagamento:    p.codigo_plano_pagamento   ?? p.plano_pagamento ?? null,
      frete_kg:           Number(p.frete_kg ?? 0),
      ipi:                Number(p.ipi     ?? 0),
      icms_st:            Number(p.icms_st ?? 0),
      iva_st:             Number(p.iva_st  ?? 0),
      grupo:              p.grupo ?? null,
      departamento:       p.departamento ?? null,

      // totais que você já exibe na tela
      total_sem_frete:    Number(p.valor_s_frete ?? p.total_sem_frete ?? 0),

      // guarda para reaproveitar na hora do POST
      __descricao_fator_label:    p.descricao_fator_comissao || null,
      __plano_pagto_label:        p.codigo_plano_pagamento   || null, // já vem "COD - desc" às vezes
      fornecedor: t.fornecedor || ''
      }));
      
     itens = itens.map(p => ({...p,peso_liquido: Number(p.peso_liquido ?? p.peso ??  p.peso_kg ?? p.pesoLiquido ??  0 ),
                                 tipo: p.tipo ?? p.grupo ?? p.departamento ?? null
     
     }));
      renderTabela();
     
      
      // Atualiza a pill e recálculo
      atualizarPillTaxa();
      

      // >>> NOVO: fator global (se todos iguais)
      const dg = document.getElementById('desconto_global');
      if (dg) {
        const fatores = (itens || [])
          .map(x => (x.fator_comissao != null ? Number(x.fator_comissao) : null))
          .filter(v => v != null && !isNaN(v));

        let fatorGlobal = null;
        if (fatores.length) {
          const base = fatores[0], tol = 1e-4;
          const unico = fatores.every(f => Math.abs(Number(f) - Number(base)) < tol);
          if (unico) fatorGlobal = Number(base);
        }

        if (fatorGlobal != null) {
          const match = Object.entries(mapaDescontos || {})
            .find(([, frac]) => Math.abs(Number(frac) - fatorGlobal) < 1e-4);
          dg.value = match ? match[0] : '';
        } else {
          dg.value = '';
        }
        atualizarPillDesconto?.();
      }

      // >>> Entrar em visualização
      currentTabelaId = id;
      setMode('view');
      return;
    }
  }

  const novos = obterItensDaSessao();              // o que veio do picker nesta volta
  itens = mergeItensExistentesENovos(itens, novos); // ✅ MESCLA em vez de substituir
  itens = itens.map(p => ({ ...p, ipi: Number(p.ipi ?? 0), iva_st: Number(p.iva_st ?? 0) }));
  itens = itens.map(p => ({...p,peso_liquido: Number(p.peso_liquido ?? p.peso ??  p.peso_kg ?? p.pesoLiquido ??  0 ),
                                tipo: p.tipo ?? p.grupo ?? p.departamento ?? null
                              }));
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

  // % (Fator/Desconto) — COLUNA ÚNICA por linha (override quando alterado)
  const tdPercent = document.createElement('td');
  const selPercent = document.createElement('select');
  selPercent.appendChild(option('—', ''));

  // popula com o mesmo dicionário do cabeçalho (mapaDescontos: {codigo -> fração 0..1})
  Object.entries(mapaDescontos).forEach(([cod, frac]) => {
    selPercent.appendChild(option(`${cod} - ${(Number(frac)*100).toFixed(2)}`, cod));
});


(() => {
  // 1) Se veio um label do back (ex.: "15 - 0"), priorize-o, mesmo se o percentual for 0
  const lbl = (item.__descricao_fator_label || '').trim();
  if (lbl) {
    const codeFromLbl = lbl.split(' - ')[0].trim(); // "15" em "15 - 0"
    if (codeFromLbl && Object.prototype.hasOwnProperty.call(mapaDescontos, codeFromLbl)) {
      selPercent.value = codeFromLbl;
    }
  }

  // 2) Se não marcou ainda, tente pelo valor numérico do fator (aceitando 0)
  if (!selPercent.value && item.fator_comissao != null && !isNaN(item.fator_comissao)) {
    const match = Object.entries(mapaDescontos).find(([, f]) => Number(f) === Number(item.fator_comissao));
    if (match) selPercent.value = match[0];
  }

  // 3) Último fallback: inferir por razão desconto/valor (aceitando 0)
  if (!selPercent.value && Number(item.valor || 0) >= 0) {
    const fatorInferido = Number(item.desconto || 0) / Number(item.valor || 1);
    const match = Object.entries(mapaDescontos).find(([, f]) =>
      Math.abs(Number(f) - fatorInferido) < 1e-6
    );
    if (match) selPercent.value = match[0];
  }
})();

selPercent.addEventListener('change', () => {
  const code  = selPercent.value || '';
  const frac  = (Object.prototype.hasOwnProperty.call(mapaDescontos, code) ? Number(mapaDescontos[code]) : 0);
  itens[idx].fator_comissao = (!isNaN(frac) ? frac : 0);
  itens[idx].__fator_codigo = code; // <-- guarda o código (ex.: "15")
  itens[idx].__descricao_fator_label = selPercent.options[selPercent.selectedIndex]?.textContent?.trim() || '';
  itens[idx].__overridePercent = true;
  recalcLinha(tr);
});

tdPercent.appendChild(selPercent);

 // Condição por linha (código) — NOVO
  const tdCondCod = document.createElement('td');
  const selCond   = document.createElement('select');
  selCond.appendChild(option('—', ''));
    
  //código + descrição (igual ao cabeçalho)---------------
  const selHdr = document.getElementById('plano_pagamento');
    Array.from(selHdr?.options || []).forEach(o => {
  if (o.value) selCond.appendChild(option(o.textContent, o.value));
  });
  
  //só a descrição-----------
//  const selHdr = document.getElementById('plano_pagamento');
//  Array.from(selHdr?.options || []).forEach(o => {
//  if (!o.value) return; // pula "Selecione…"
//  const partes = (o.textContent || '').split(' - ');
//  const desc   = partes.slice(1).join(' - ') || o.textContent; // robusto
//  selCond.appendChild(option(desc, o.value));
//  });


     //Só o codigo ----------
  //Object.keys(mapaCondicoes).forEach(cod => {
  //selCond.appendChild(option(cod, cod));
//});
    
  const codCondLinha = String(item.plano_pagamento || '').split(' - ')[0].trim();
  selCond.value = codCondLinha || '';
  
  tdCondCod.appendChild(selCond);

  selCond.addEventListener('change', () => {
  itens[idx].plano_pagamento = selCond.value || null;
  recalcLinha(tr);
  });

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
  const tdFinal = document.createElement('td'); tdFinal.className = 'num col-total'; tdFinal.textContent = fmtMoney(item.valor || 0);tr.appendChild(tdFinal);
  const tdTotalSemFrete = document.createElement('td');tdTotalSemFrete.className = 'num col-total-sem-frete';tdTotalSemFrete.textContent = '0,00';tr.appendChild(tdTotalSemFrete);
  
  tr.append(
  tdSel, tdCod, tdDesc, tdEmb, tdGrupo,
  tdPeso, tdValor, tdPercent,tdDescAplic,
  tdCondCod, tdCondVal, tdFrete, 
  tdIpiR$, tdBaseStR$, tdIcmsProp$, tdIcmsCheio$, tdIcmsReter$, tdFinal, tdTotalSemFrete
);
  return tr;
}

async function recalcularLinhaComFiscal(item, codigo_cliente, forcarST, frete_linha) {
  const payload = {
    codigo_cliente: codigo_cliente ?? null,
    forcar_iva_st: !!forcarST,
    produto_id: item.codigo_tabela,
    tipo: (item.tipo || "").toLowerCase(),
    peso_kg: Number(item.peso_liquido || 0),
    preco_unit: Number(item.valor || 0),
    quantidade: 1,
    desconto_linha: Number(item.desconto || 0),
    frete_linha: Number(frete_linha || 0),
  };

  const r = await fetch(`${API_BASE}/fiscal/preview-linha`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  const out = await r.json();

  // use o que fizer sentido: total sem ST ou COM ST
  item.valor_liquido = out.total_linha;          // ou: out.total_linha_com_st
  item._motivos_iva = out.motivos_iva_st;        // útil pra debug na UI
  return item;
}

function buildFiscalInputsFromRow(tr) {
  const idx  = Number(tr.dataset.idx);
  const item = (itens || [])[idx] || {};

  // DOM: fator por linha e condição (código)
  const fatorPct = Number(tr.querySelector('td:nth-child(8) select')?.value || 0);
  const fator    = fatorPct / 100;
  const codCond  = tr.querySelector('td:nth-child(10) select')?.value || '';
  const taxaCond = (window.mapaCondicoes && window.mapaCondicoes[codCond]) ?? 0;

  // DOM: frete global e toggles
  const freteKg       = Number(document.getElementById('frete_kg')?.value || 0); // R$/kg
  const codigo_cliente = (document.getElementById('codigo_cliente')?.value || '').trim() || null;
  const ramoJuridico  = (document.getElementById('ramo_juridico')?.value || '').trim() || null;
  const forcarST      = !!document.getElementById('iva_st_toggle')?.checked;

  // Item básico
  const produtoId = (tr.querySelector('td:nth-child(2)')?.textContent || '').trim();
  const tipo = String(item?.tipo || item?.grupo || item?.departamento || '').trim();
  const peso_kg   = Number(item?.peso_liquido ?? item?.peso ?? item?.peso_kg ?? item?.pesoLiquido ?? 0);

  // Preço base (espelha sua lógica da tela): valor + acrescimo(condição) - desconto(fator)
  const valor           = Number(item?.valor || 0);
  const descontoValor   = valor * Number(fator || 0);
  const liquido       = Math.max(0, valor - descontoValor);
  const acrescimoCond   = liquido * Number(taxaCond || 0);
  
  const precoBase       = liquido + acrescimoCond;

  // Frete por linha (usando kg diretamente)
  const frete_linha = Number(freteKg || 0) * Number(peso_kg || 0); 

  const payload = {
  codigo_cliente: codigo_cliente,
  forcar_iva_st: forcarST,
  produto_id: produtoId,
  ramo_juridico: ramoJuridico,
  peso_kg: Number(peso_kg || 0),
  tipo: tipo,
  preco_unit: Number(liquido  || 0),
  quantidade: 1,
  desconto_linha: 0,
  frete_linha: Number(frete_linha || 0),
};

  return {
    produto_id: produtoId,
    tipo, peso_kg, ramo_juridico: ramoJuridico, forcar_iva_st: forcarST,
    preco_unit: payload.preco_unit, frete_linha: payload.frete_linha,
    fator_percent: fatorPct, condicao_codigo: codCond, taxa_condicao: taxaCond,
    payload, precoBase, liquido
  };
}

function renderTabela() {
  const tbody = document.getElementById('tbody-itens');
  tbody.innerHTML = '';
  itens.forEach((it, i) => tbody.appendChild(criarLinha(it, i)));
  if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
}

async function recalcLinha(tr) {
    
  const idx  = Number(tr.dataset.idx);
  const item = itens[idx]; if (!item) return;

  const nextId = (Number(tr.dataset.reqId || 0) + 1);
  tr.dataset.reqId = String(nextId);
  const myId = String(nextId);

  const selPct   = tr.querySelector('td:nth-child(8) select');
  const codePct  = selPct ? (selPct.value || '') : '';
  const fator    = (mapaDescontos[codePct] != null) ? Number(mapaDescontos[codePct]) : 0;

  const freteKg  = Number(document.getElementById('frete_kg').value || 0);

  // Condição por linha → taxa
  const selCond  = tr.querySelector('td:nth-child(10) select');
  const codCond  = selCond ? selCond.value : '';
  const taxaCond = mapaCondicoes[codCond] ?? 0;

  // base comercial (sem imposto)
  const { acrescimoCond, freteValor, descontoValor, liquido  } =
    calcularLinha(item, fator, taxaCond, freteKg);

  // pinta colunas comerciais
  tr.querySelector('td:nth-child(9)').textContent = fmtMoney(descontoValor); // Desc. aplicado
  tr.querySelector('td:nth-child(11)').textContent = fmtMoney(acrescimoCond); // Cond. (R$)
  tr.querySelector('td:nth-child(12)').textContent = fmtMoney(freteValor);    // Frete (R$)
  

  
  try {
    const built = buildFiscalInputsFromRow(tr);

    // usa exatamente o que JÁ calculamos nesta função
    built.payload.preco_unit  = liquido;   // já calculado acima
    built.payload.frete_linha = freteValor;  // já calculado acima

    const f = await previewFiscalLinha(built.payload);
   item.ipi     = Number((f.ipi          ?? 0).toFixed(2));
   item.iva_st  = Number((f.base_st      ?? 0).toFixed(2));
   item.icms_st = Number((f.icms_proprio ?? 0).toFixed(2));
    
   if (tr.dataset.reqId !== myId) return;
   
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

    const totalFiscal = Number(f.total_linha_com_st ?? f.total_linha ?? 0);

    // ✅ aplica CONDIÇÃO (R$) sobre o líquido e soma no total final exibido
    const totalComercial = totalFiscal + Number(acrescimoCond || 0);
    
    const totalSemFrete = totalComercial - Number(freteValor || 0);
    const tdSemFrete = tr.querySelector('.col-total-sem-frete');
    if (tdSemFrete) tdSemFrete.textContent = fmtMoney(totalSemFrete);

    setCell('.col-total', totalComercial);
    item._freteValor = Number(freteValor || 0);
    item._totalComercial = Number(totalComercial || 0);
    item.total_sem_frete = Math.max(0, item._totalComercial - item._freteValor);

    const td = tr.querySelector('.col-total-sem-frete');
      if (td) td.textContent = fmtMoney(item.total_sem_frete || 0);

  } catch (e) {
  if (tr.dataset.reqId === myId && tr.isConnected) {
    const msg = String(e && (e.name || e.message || e));
    const isAbort = /abort|aborted|cancel|canceled|cancelled/i.test(msg);

    if (!isAbort) {
      console.warn('[Fiscal ERROR ignorado]', msg);
      // ⚠️ Não zera mais os valores já exibidos
    }
    }
  }
}


async function recalcTudo() {
  if (__recalcRunning) {           // já tem uma rodada em andamento?
    __recalcPending = true;        // marca que ficou pendente rodar de novo
    return;                        // deixa a rodada atual terminar
  }
  __recalcRunning = true;

  try {
    do {
      __recalcPending = false;     // vamos processar o "snapshot" atual
      const rows = Array.from(document.querySelectorAll('#tbody-itens tr'));
      for (const tr of rows) {
        // eslint-disable-next-line no-await-in-loop
        await recalcLinha(tr);     // 1 a 1, na ordem, para estabilidade visual
      }
      // Se, enquanto rodávamos, alguém pediu outra rodada, repete o laço
    } while (__recalcPending);
  } finally {
    __recalcRunning = false;
  }
}

async function aplicarFatorGlobal() {
  const selGlobal = document.getElementById('desconto_global');
  const code = selGlobal?.value || '';
  const fator = mapaDescontos[code];

  if (fator == null || isNaN(fator)) {
    alert('Escolha um desconto válido.');
    return;
  }

  // Aplica em cada linha e sincroniza o select da linha
  document.querySelectorAll('#tbody-itens tr').forEach(tr => {
    const sel = tr.querySelector('td:nth-child(8) select'); // coluna unificada
    if (!sel) return;
    sel.value = code;
    // 🔑 dispara o mesmo fluxo do usuário (atualiza itens[idx] e recalcula)
    sel.dispatchEvent(new Event('change', { bubbles: true }));
  });
  await Promise.resolve(recalcTudo()).catch(()=>{});
  atualizarPillDesconto();
  snapshotSelecionadosParaPicker?.();

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

function inferirFornecedorDaGrade() {
  const lista = Array.from(new Set((itens || []).map(x => x.fornecedor).filter(Boolean)));
  return lista.length === 1 ? lista[0] : (lista[0] || '');
}

async function salvarTabela() {
  const linhas = document.querySelectorAll('#tbody-itens tr');
  if (linhas.length === 0) {
    alert('Adicione pelo menos 1 produto à tabela antes de salvar.');
    // foca em algo útil da sua UI (ajuste se tiver um botão/field específico)
    document.querySelector('#busca_produto, #nome_tabela')?.focus();
    return;
  }
  
  const { ok } = RequiredValidator.check(RequiredValidator.REQUIRED_FIELDS, document);
  if (!ok) {
    alert('Existem campos obrigatórios pendentes. Corrija os destaques em vermelho.');
    return;
  } 
  
  const nome_tabela   = document.getElementById('nome_tabela').value.trim();
  const cliente       = document.getElementById('cliente_nome').value.trim();
  const frete_kg      = Number(document.getElementById('frete_kg').value || 0);
  const ramo_juridico = document.getElementById('ramo_juridico').value || null;

  const produtos = Array.from(document.querySelectorAll('#tbody-itens tr'))
  .map(tr => {
    const idx  = Number(tr.dataset.idx);
    const item = itens[idx];

    const selPct  = tr.querySelector('td:nth-child(8) select');
    const codePct = selPct ? selPct.value : '';
    const fator   = (mapaDescontos[codePct] != null) ? Number(mapaDescontos[codePct]) : 0;
    
    const selCond   = tr.querySelector('td:nth-child(10) select');
    const codCond   = selCond ? (selCond.value || '') : '';
    const condLabel = (selCond?.options[selCond.selectedIndex]?.textContent || '').trim();

    const taxaCond = mapaCondicoes[codCond] || 0;
    const { acrescimoCond, freteValor, descontoValor } =
      calcularLinha(item, fator, taxaCond, frete_kg /* ivaStAtivo é ignorado aqui */);

    const fatorLabel = selPct ? (selPct.options[selPct.selectedIndex]?.textContent || '').trim() : '';
    
    let planoToSave = condLabel || '';
    if (codCond) {
      if (!planoToSave || !planoToSave.startsWith(codCond)) {
        planoToSave = planoToSave ? `${codCond} - ${planoToSave}` : codCond;
      }
    }
    // objeto do item (NÃO coloque nome_tabela/cliente/fornecedor aqui)
    const produto = {
      codigo_produto_supra: item.codigo_tabela,
      descricao_produto:    item.descricao,
      embalagem:            item.embalagem || '',
      peso_liquido:         Number(item.peso_liquido ?? 0),

      valor_produto:            Number(item.valor || 0),
      comissao_aplicada:        Number(descontoValor.toFixed(2)),
      ajuste_pagamento:         Number(acrescimoCond.toFixed(2)),
      descricao_fator_comissao: fatorLabel,
      codigo_plano_pagamento:  planoToSave,                 

      valor_frete_aplicado:     Number(freteValor.toFixed(2)),
      frete_kg:                 Number(frete_kg || 0),
      valor_frete:              Number((item._totalComercial || 0).toFixed(2)),
      valor_s_frete:            Number((item.total_sem_frete || 0).toFixed(2)),

      grupo:        item.grupo || null,
      departamento: item.departamento || null,
      ipi:          Number(item.ipi     || 0),
      icms_st:      Number(item.icms_st || 0),
      iva_st:       Number(item.iva_st  || 0)
    };

    // id_linha: DOM primeiro; fallback pro array
    if (tr.dataset.idLinha) {
      produto.id_linha = Number(tr.dataset.idLinha);
    } else if (itens[idx]?.id_linha != null) {
      produto.id_linha = itens[idx].id_linha;
    }

    return produto; // ✅ dentro do map
  })
  .filter(p => p.codigo_produto_supra && p.descricao_produto);

  console.table(produtos.map(p => ({ id_linha: p.id_linha, codigo: p.codigo_produto_supra, valor: p.valor_produto, plano: p.codigo_plano_pagamento})));

  const fornecedorHeader = inferirFornecedorDaGrade();
  const codigo_cliente = (document.getElementById('codigo_cliente')?.value || '').trim() || null;
  const payload = {nome_tabela, cliente, codigo_cliente: (codigo_cliente || "Não cadastrado"), ramo_juridico,fornecedor: fornecedorHeader, produtos};
  try {
    const resp = await salvarTabelaPreco(payload);
    return resp;                                     // <<<<<< FUNDAMENTAL
  } catch (e) {
    console.error(e);
    alert(e.message || 'Erro ao salvar a tabela.');
    return null;
  }}
  

 function validarCabecalhoMinimo() {
  const nome   = document.getElementById('nome_tabela')?.value?.trim();
  const cliente = document.getElementById('cliente_nome')?.value?.trim();
  
  if (!nome || !cliente ) return false;

  // valida ordem das datas (se ambos presentes)
 
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
  document.getElementById('codigo_cliente').value = '';

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

function getIdFromUrl() {
  try {
    const id = new URLSearchParams(window.location.search).get('id');
    return id ? String(id) : null;
  } catch {
    return null;
  }
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
  if (!currentTabelaId) {
    const idUrl = getIdFromUrl();
    const mem   = sessionStorage.getItem('TP_LAST_VIEW_ID');
    const ctx   = sessionStorage.getItem('TP_CTX_ID');
    const cand  = idUrl || (mem && mem !== 'new' ? mem : null) || (ctx && ctx !== 'new' ? ctx : null);
    if (cand) currentTabelaId = String(cand);
  }
  setMode(MODE.VIEW);
  if (typeof setFormDisabled === 'function') setFormDisabled(true);
  if (typeof toggleToolbarByMode === 'function') toggleToolbarByMode();
  if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
  sessionStorage.removeItem('TP_LAST_VIEW_ID');
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
          document.getElementById('codigo_cliente').value = t.codigo_cliente || '';
          
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
    
   if (!currentTabelaId) {
     const srcMem = sessionStorage.getItem('TP_SOURCE_ID');
     const last   = sessionStorage.getItem('TP_LAST_VIEW_ID');
     const url    = getIdFromUrl();
     const ctx    = sessionStorage.getItem('TP_CTX_ID');
     const cand   = sourceTabelaId || (srcMem && srcMem !== 'new' ? srcMem : null)
                   || (last && last !== 'new' ? last : null)
                   || url || (ctx && ctx !== 'new' ? ctx : null);
     if (cand) currentTabelaId = String(cand);
   }
   sourceTabelaId = null;
   sessionStorage.removeItem('TP_SOURCE_ID');

    
    // trava e mostra botões de decisão (Editar/Duplicar)
    setMode(MODE.VIEW);
    if (typeof setFormDisabled === 'function') setFormDisabled(true);
    if (typeof toggleToolbarByMode === 'function') toggleToolbarByMode();
    if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
    return;
  }

  if (currentMode === MODE.VIEW) {
    if (currentTabelaId) {
      currentTabelaId = null; sourceTabelaId = null;
      limparFormularioCabecalho?.(); limparGradeProdutos?.();
    return setMode(MODE.NEW);
    }
  
  // Sem id (tela em branco) → aí sim limpa para NEW
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

async function atualizarValidadeCabecalhoGlobal() {
  try {
    const r = await fetch(ENDPOINT_VALIDADE, { cache: 'no-store' });
    if (!r.ok) return;
    const data = await r.json();

    const elDate = document.getElementById('validade_tabela');
    const elDias = document.getElementById('dias_restantes');

    if (elDate) elDate.value = data.validade_tabela_br || '';
    if (elDias) {
      const n = data.dias_restantes;
      if (n == null) { elDias.value = '—'; elDias.dataset.status = 'nao_definida'; }
      else if (n >= 0) { elDias.value = `Faltam ${n} dia${n===1?'':'s'}`; elDias.dataset.status = n<=7?'alerta':'ok'; }
      else { const k = Math.abs(n); elDias.value = `Expirada há ${k} dia${k===1?'':'s'}`; elDias.dataset.status = 'expirada'; }
    }
  } catch (e) {
    console.error('validade_global:', e);
  }
}

// === Bootstrap ===
document.addEventListener('DOMContentLoaded', () => {
  // Eventos globais
  setMode(MODE.NEW);
  document.getElementById('btn-listar')?.addEventListener('click', () => { goToListarTabelas(); });
  
  document.getElementById('btn-aplicar-todos')?.addEventListener('click', aplicarFatorGlobal);
  
  document.getElementById('plano_pagamento')?.addEventListener('change', () => { atualizarPillTaxa(); recalcTudo(); refreshToolbarEnablement();saveHeaderSnapshot();  
    });
  document.getElementById('frete_kg')?.addEventListener('input', () => {
    recalcTudo();
    refreshToolbarEnablement();  
        
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

 atualizarValidadeCabecalhoGlobal();

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
    snapshotSelecionadosParaPicker();
  });

  // handler único (sem aninhar addEventListener dentro de outro)
(() => {
  const btn = document.getElementById('btn-salvar');
  if (!btn) return;

  btn.type = 'button';
  let saving = false;

  btn.addEventListener('click', async (e) => {
    e.preventDefault();
    if (saving) return;
    saving = true;
    btn.disabled = true;

    try {
      const resp = await salvarTabela(); // agora retorna JSON
      if (!resp) return;
      const qtd = resp?.itens_inseridos ?? resp?.qtd_produtos ?? itens.length;
      alert(`Tabela salva! ${qtd} produtos incluídos.`);
      

      // pegue o ID
      const tabelaId = resp?.tabela_id || resp?.id_tabela || resp?.id || window.currentTabelaId;
      if (!tabelaId) {
        alert("Tabela salva, mas o ID não veio no retorno do backend. Ajuste o /tabela_preco/salvar para devolver o id.");
        return;
      }

      // pergunta de decisão
      const querEnviar = confirm("Deseja mandar o link do orçamento?");
       if (querEnviar) {
        if (typeof window.__showGerarLinkModal === "function") {
         window.__showGerarLinkModal({
         tabelaId,
         pedidoClientePath: "/tabela_preco/pedido_cliente.html",
         });
          } else {
    alert("Módulo de gerar link não carregado (../js/gerar_link_pedido.js).");
  }
} else {
  // >>> Cancelou o envio do link: volta ao estado inicial (sem id, modo original)
  currentTabelaId = '';
  sourceTabelaId  = '';
  window.currentTabelaId = '';
  window.sourceTabelaId  = '';

  // limpa URL (?id=)
  try {
    const u = new URL(location.href);
    u.searchParams.delete('id');
    history.replaceState(null, '', u.toString());
  } catch {}

  // limpa cabeçalho + grade e volta pro modo original (inputs habilitados)
  if (typeof limparFormularioCabecalho === 'function') limparFormularioCabecalho();
  if (typeof limparGradeProdutos === 'function') limparGradeProdutos();

  if (typeof setMode === 'function') setMode(MODE.NEW); // ou o seu "modo inicial" da tela
  if (typeof setFormDisabled === 'function') setFormDisabled(false);

  if (typeof toggleToolbarByMode === 'function') toggleToolbarByMode();
  if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();

}

      } catch (err) {
      // mostra 422 legível, se vier no formato FastAPI
      const msg = (err && err.message) ? err.message : 'Erro ao salvar a tabela.';
      alert(msg);
      console.error(err);
    } finally {
      saving = false;
      btn.disabled = false;
      toggleToolbarByMode?.();
      refreshToolbarEnablement?.();
    }
  });
})();
  
  document.getElementById('btn-cancelar')?.addEventListener('click', onCancelar);
  document.getElementById('btn-editar')?.addEventListener('click', onEditar);
  document.getElementById('btn-duplicar')?.addEventListener('click', onDuplicar); 
  
  // Init
  (async function init(){
    await Promise.all([carregarCondicoes(), carregarDescontos()]);
    
    if (__IS_RELOAD) {
    // F5: deixa tudo zerado
    limparFormularioCabecalho?.();
  } else {
    // navegação normal: restaura cabeçalho salvo
    restoreHeaderSnapshotIfNew?.();
  }

   await carregarItens();                       // carrega itens salvos/edição
   if (!__IS_RELOAD) await mergeBufferFromPickerIfAny?.();

   setupClienteAutocomplete();
   enforceIvaLockByCliente();
       
   // —— quando o usuário editar manualmente o NOME do cliente ——
   const inpNome   = document.getElementById('cliente_nome');
   const hidCodigo = document.getElementById('codigo_cliente');
   const hidRamo   = document.getElementById('ramo_juridico');

   inpNome?.addEventListener('input', () => {
   // Se o campo ficar vazio, não considere mais “cliente cadastrado”
   if (!inpNome.value.trim()) {
     if (hidCodigo) hidCodigo.value = '';
     if (hidRamo)   hidRamo.value   = '';
    recalcTudo();                         // dispara o preview em todas as linhas
   }
     enforceIvaLockByCliente();
     saveHeaderSnapshot?.();  
   });

   // Se algum outro código limpar/alterar esses campos, recalcule também
   hidCodigo?.addEventListener('change', () => {
    enforceIvaLockByCliente();   // 👈 acrescenta
    saveHeaderSnapshot?.();      // 👈 acrescenta
    recalcTudo();
     });

   hidRamo?.addEventListener('change', () => {
    saveHeaderSnapshot?.();      // 👈 opcional
    recalcTudo();
    });

   // Se vier com ação na URL (?action=edit|duplicate), respeitar:
    const q = new URLSearchParams(location.search);
    const action = q.get('action') || q.get('mode') || q.get('modo');
    
    let modeRestored = false;
    
    if (!action) {
    const ctx = sessionStorage.getItem('TP_CTX_ID') || getCtxId();
    const ret = sessionStorage.getItem(`TP_RETURN_MODE:${ctx}`);
     if (ret) {
      if (ret === MODE.EDIT)      setMode(MODE.EDIT);
      else if (ret === MODE.DUP)  setMode(MODE.DUP);
      else if (ret === MODE.NEW)  setMode(MODE.NEW);
      sessionStorage.removeItem(`TP_RETURN_MODE:${ctx}`);
      modeRestored = true;
  }
}

  if (!modeRestored) {
    if (currentTabelaId) {
      if (action === 'edit') setMode(MODE.EDIT);
      else if (action === 'duplicate') onDuplicar(); // usa o fluxo que guarda a origem
      else setMode(MODE.VIEW);
    } else {
      setMode(MODE.NEW);
    }
   
  }
    refreshToolbarEnablement();
    await Promise.resolve(recalcTudo()).catch(()=>{});
  })();
 });
 

 document.getElementById('btn-aplicar-condicao-todos')?.addEventListener('click', () => {
  const cod = document.getElementById('plano_pagamento')?.value || '';
  document.querySelectorAll('#tbody-itens tr').forEach(tr => {
    const sel = tr.querySelector('td:nth-child(10) select');
    if (!sel) return;
    sel.value = cod;
    // 🔑 garante persistência em itens[idx] + recálculo
    sel.dispatchEvent(new Event('change', { bubbles: true }));
  });
    setTimeout(() => {
    Promise.resolve(recalcTudo()).catch(()=>{});
  }, 0);
    snapshotSelecionadosParaPicker?.();
 });
 document.getElementById('iva_st_toggle')?.addEventListener('change', (e) => {
  ivaStAtivo = !!e.target.checked;
  Promise.resolve(recalcTudo()).catch(err => console.debug('recalcTudo falhou:', err));
   });

 document.getElementById('desconto_global')?.addEventListener('change', () => {
  atualizarPillDesconto();
  saveHeaderSnapshot();                      // << acrescentar
 });

 window.addEventListener('pageshow', () => {
  if (typeof recalcTudo === 'function') {
      queueMicrotask(() => Promise.resolve(recalcTudo()).catch(() => {}));  }
});

document.addEventListener('input', handleFieldChange, true);
document.addEventListener('change', handleFieldChange, true);

function handleFieldChange(e) {
  const el = e.target;
  if (!el || !(el instanceof HTMLElement)) return;

  // Se o campo estava marcado com erro, limpamos
  if (el.classList.contains('field-error')) {
    el.classList.remove('field-error');
    const msg = el.nextElementSibling;
    if (msg && msg.classList.contains('field-error-msg')) {
      msg.remove();
    }
  }
}