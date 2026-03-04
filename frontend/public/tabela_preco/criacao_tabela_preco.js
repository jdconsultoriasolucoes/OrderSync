// === Config ===
// Config is now imported via config.js
const API_BASE = window.API_BASE || "https://ordersync-backend-edjq.onrender.com"; // Restored & Safe
// window.API_BASE already set by config.js
const ENDPOINT_VALIDADE = `${API_BASE}/tabela_preco/meta/validade_global`;

// === Estado ===
const MODE = { NEW: 'new', VIEW: 'view', EDIT: 'edit', DUP: 'duplicate' };
let mapaCondicoes = {}; // { codigo: taxa }
let mapaDescontos = {}; // { codigo: fator }
let itens = []; // itens carregados
let currentMode = 'new';       // 'new' | 'view' | 'edit' | 'duplicate'
let currentTabelaId = null;
let sourceTabelaId = null;
window.currentClientMarkup = 0; // Expose globally for snapshot
let ivaStAtivo = !!document.getElementById('iva_st_toggle')?.checked;
let __recalcRunning = false;
let __recalcPending = false;

// ===================================
// CUSTOM OS MODALS
// ===================================
function showOsModal(options) {
  return new Promise((resolve) => {
    const backdrop = document.createElement('div');
    backdrop.className = 'os-modal-backdrop active';

    const dialog = document.createElement('div');
    dialog.className = 'os-modal-dialog';
    dialog.style.maxWidth = '400px';

    const header = document.createElement('div');
    header.className = 'os-modal-header';
    header.innerHTML = `<h3 class="os-modal-title">${options.title}</h3>
                      <button class="os-modal-close">&times;</button>`;

    const body = document.createElement('div');
    body.className = 'os-modal-body';
    body.innerHTML = `<p style="margin:0;">${options.message}</p>`;

    const footer = document.createElement('div');
    footer.className = 'os-modal-footer';

    if (options.type === 'confirm') {
      const btnCancel = document.createElement('button');
      btnCancel.className = 'os-btn os-btn-secondary';
      btnCancel.textContent = 'Cancelar';

      const btnOk = document.createElement('button');
      btnOk.className = 'os-btn os-btn-primary';
      btnOk.textContent = 'OK';

      footer.appendChild(btnCancel);
      footer.appendChild(btnOk);

      btnCancel.onclick = () => { document.body.removeChild(backdrop); resolve(false); };
      btnOk.onclick = () => { document.body.removeChild(backdrop); resolve(true); };
    } else {
      const btnOk = document.createElement('button');
      btnOk.className = 'os-btn os-btn-primary';
      btnOk.textContent = 'OK';
      footer.appendChild(btnOk);
      btnOk.onclick = () => { document.body.removeChild(backdrop); resolve(true); };
    }

    header.querySelector('.os-modal-close').onclick = () => {
      document.body.removeChild(backdrop);
      resolve(options.type === 'confirm' ? false : true);
    };

    dialog.appendChild(header);
    dialog.appendChild(body);
    dialog.appendChild(footer);
    backdrop.appendChild(dialog);
    document.body.appendChild(backdrop);
  });
}

// ✅ Se a página for recarregada (F5), zera o buffer legado
const __IS_RELOAD = (() => {
  try {
    const nav = performance.getEntriesByType('navigation')[0];
    return !!(nav && nav.type === 'reload');
  } catch { return false; }
})();

if (__IS_RELOAD) {
  try { sessionStorage.removeItem('criacao_tabela_preco_produtos'); } catch { }
  // limpe também snapshots/ponte por contexto, se usar TP_CTX_ID
  Object.keys(sessionStorage).forEach(k => {
    if (k.startsWith('TP_HEADER_SNAPSHOT:')) sessionStorage.removeItem(k);
    if (k.startsWith('TP_ATUAL:')) sessionStorage.removeItem(k);
    if (k.startsWith('TP_BUFFER:')) sessionStorage.removeItem(k);
  });
}

window.isClienteLivreSelecionado = false;

function parseBool(v) {
  if (typeof v === 'boolean') return v;
  if (typeof v === 'number') return v === 1;
  if (typeof v === 'string') return ['s', 'sim', 'true', '1', 'y', 'yes'].includes(v.trim().toLowerCase());
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

  function clear(root = document) {
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
    '#nome_tabela': 'Informe o nome da tabela.',
    '#cliente_nome': 'Informe/selecione o cliente.',
    '#tbody-itens tr td:nth-child(8) select': 'Selecione a classificação para todos os itens.',
    '#tbody-itens tr td:nth-child(10) select': 'Selecione a condição de pagamento para todos os itens.'
  };

  function check(config = REQUIRED_FIELDS, root = document) {
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
  const on = (id) => !!$(`${id}`)?.checked;

  return {
    // visuais
    nome_tabela: val("nome_tabela"),
    cliente: val("cliente_nome"),   // texto mostrado no input
    // ocultos/importantes
    codigo_cliente: val("codigo_cliente"),
    ramo_juridico: val("ramo_juridico"),

    // toggles/parametrizações
    iva_st: on("iva_st_toggle"),
    frete_kg: val("frete_kg") || "0",
    plano_pagamento: val("plano_pagamento"),
    desconto_global: val("desconto_global"),
    markup_global: val("markup_global"), // ✅ Persist Markup Global Field
    cliente_livre: !!window.isClienteLivreSelecionado,
    cliente_livre: !!window.isClienteLivreSelecionado,
    iva_enabled: !$("iva_st_toggle")?.disabled,
    currentClientMarkup: window.currentClientMarkup || 0 // ✅ Persist Markup
  };
}

function saveHeaderSnapshot() {
  const ctx = getCtxId();
  sessionStorage.setItem(`TP_HEADER_SNAPSHOT:${ctx}`, JSON.stringify(getHeaderSnapshot()));
}

function restoreHeaderSnapshotIfNew(force = false) {
  // Só restaura em NEW (sem id na URL) para não sujar edição/visualização
  // EXCETO se 'force' for true (usado ao voltar do picker)
  if (currentTabelaId && !force) return;

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
    set('nome_tabela', snap.nome_tabela);
    set('cliente_nome', snap.cliente);
    set('codigo_cliente', snap.codigo_cliente);
    set('ramo_juridico', snap.ramo_juridico);
    set('frete_kg', snap.frete_kg);

    // ---- Selects (este método deve ser chamado DEPOIS de carregarCondicoes/Descontos)
    set('plano_pagamento', snap.plano_pagamento || '');
    set('desconto_global', snap.desconto_global || '');
    set('markup_global', snap.markup_global || ''); // ✅ Restore Markup Global

    // ---- IVA_ST e flags do cliente livre
    const ivaChk = document.getElementById('iva_st_toggle');
    if (ivaChk) {
      ivaChk.checked = !!snap.iva_st;
      ivaChk.disabled = !snap.iva_enabled;   // se estava habilitado, volta habilitado
      window.ivaStAtivo = ivaChk.checked;
    }
    window.isClienteLivreSelecionado = !!snap.cliente_livre;
    window.currentClientMarkup = Number(snap.currentClientMarkup || 0); // ✅ Restore Markup

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
  try { sessionStorage.removeItem(`TP_ATUAL:${ctx}`); } catch { }
  try { sessionStorage.removeItem(`TP_BUFFER:${ctx}`); } catch { }
}

function clearFullSnapshot() {
  const ctx = getCtxId();
  try { sessionStorage.removeItem(`TP_HEADER_SNAPSHOT:${ctx}`); } catch { }
  try { sessionStorage.removeItem(`TP_RETURN_MODE:${ctx}`); } catch { }
  clearPickerBridgeFor(ctx);
}

function preparePickerBridgeBeforeNavigate() {
  const ctx = getCtxId();
  sessionStorage.setItem('TP_CTX_ID', ctx);
  sessionStorage.setItem(`TP_RETURN_MODE:${ctx}`, currentMode);
  try { sessionStorage.removeItem(`TP_BUFFER:${ctx}`); } catch { }
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
    // descarte só se estiver em VIEW e NÃO houver intenção de editar/duplicar
    const retMode = sessionStorage.getItem(`TP_RETURN_MODE:${ctx || 'new'}`);
    const pretendEdit = (retMode === MODE.EDIT || retMode === MODE.DUP || retMode === MODE.NEW);
    if (currentMode === MODE.VIEW && !pretendEdit) {
      sessionStorage.removeItem(`TP_BUFFER:${ctx}`);
      return;
    }
    const recebidos = JSON.parse(raw) || [];

    // Auto-apply Globals to New Items
    const mkGlobalRaw = document.getElementById('markup_global')?.value || '0';
    const mkGlobal = parseFloat(mkGlobalRaw.replace(',', '.')) || 0;

    const descCode = document.getElementById('desconto_global')?.value || '';
    const condCode = document.getElementById('plano_pagamento')?.value || '';
    const fatorGlobal = (descCode && mapaDescontos[descCode] != null) ? Number(mapaDescontos[descCode]) : null;

    const map = new Map((itens || []).map(x => [x.codigo_tabela, x]));
    for (const p of recebidos) {
      // 1) Apply Markup
      if (mkGlobal > 0) {
        p.markup = mkGlobal;
      } else if (!p.markup && currentClientMarkup) {
        p.markup = currentClientMarkup;
      }

      // 2) Apply Discount (Factor)
      if (fatorGlobal != null) {
        p.fator_comissao = fatorGlobal;
      }

      // 3) Apply Condition
      if (condCode) {
        p.plano_pagamento = condCode;
      }

      map.set(p.codigo_tabela, { ...(map.get(p.codigo_tabela) || {}), ...p });
    }
    itens = Array.from(map.values());
    renderTabela();

    await atualizarPrecosAtuais();
    queueMicrotask(() => Promise.resolve(recalcTudo()).catch(() => { }));
  } catch { }
  finally {
    try { sessionStorage.removeItem(`TP_BUFFER:${ctx}`); } catch { }
  }
}

async function atualizarPrecosAtuais() {
  // Normaliza os códigos da tabela
  const codigos = Array.from(
    new Set(
      (itens || [])
        .map(x => x.codigo_tabela)
        .filter(Boolean)
        .map(c => String(c).trim())
    )
  );

  if (!codigos.length) return;

  const codigosSet = new Set(codigos);
  const mapa = {}; // codigo_tabela -> valor_atual
  const PAGE_SIZE = 1000; // igual ou maior que 25, só que "turbinado"
  let page = 1;
  let total = null;

  while (true) {
    let url;
    try {
      url = new URL(`${API_BASE}/tabela_preco/produtos_filtro`);
    } catch (e) {
      console.error("atualizarPrecosAtuais URL inválida:", e);
      break;
    }

    url.searchParams.set("page", String(page));
    url.searchParams.set("page_size", String(PAGE_SIZE));

    let resp;
    try {
      resp = await fetch(url.toString(), { cache: "no-store" });
    } catch (e) {
      console.error("atualizarPrecosAtuais fetch erro:", e);
      break;
    }

    if (!resp.ok) {
      console.error("atualizarPrecosAtuais resposta não OK:", resp.status);
      break;
    }

    let raw;
    try {
      raw = await resp.json();
    } catch (e) {
      console.error("atualizarPrecosAtuais json erro:", e);
      break;
    }

    const paginado = !Array.isArray(raw) && Array.isArray(raw.items);
    const arr = paginado ? (raw.items || []) : (Array.isArray(raw) ? raw : []);

    if (paginado) {
      total = typeof raw.total === "number" ? raw.total : arr.length;
    }

    // Varre a página e amarra cada código ao seu preço atual
    for (const p of arr) {
      const cands = [
        p.codigo_tabela,
        p.codigo,
        p.codigo_produto_supra,
        p.CODIGO
      ].map(v => String(v ?? "").trim());

      const chave = cands.find(c => codigosSet.has(c));
      if (!chave) continue;

      // não sobrescrever se já pegamos esse código de uma página anterior
      if (Object.prototype.hasOwnProperty.call(mapa, chave)) continue;

      const valorNum = Number(
        p.valor ??
        p.preco ??
        p.preco_venda ??
        p.valor_produto ??
        0
      );

      if (!Number.isNaN(valorNum) && valorNum > 0) {
        mapa[chave] = {
          valor: valorNum,
          peso_bruto: Number(p.peso_bruto || 0)
        };
      }
    }

    // Se já encontramos todos os códigos, podemos parar
    if (Object.keys(mapa).length >= codigosSet.size) {
      break;
    }

    // Se não for paginação (array simples), para na primeira
    if (!paginado) break;

    const ja = page * PAGE_SIZE;
    if (total != null && ja >= total) {
      // já varremos todas as páginas
      break;
    }

    page += 1;

    // trava de segurança pra não entrar em loop insano
    if (page > 50) {
      console.warn("atualizarPrecosAtuais: limite de páginas excedido");
      break;
    }
  }

  // Se não achamos nenhum preço, não mexe em nada
  if (!Object.keys(mapa).length) {
    return;
  }

  // Aplica os preços encontrados nos itens
  let mudou = false;
  itens = (itens || []).map(it => {
    const key = String(it.codigo_tabela ?? "").trim();
    const data = key && Object.prototype.hasOwnProperty.call(mapa, key)
      ? mapa[key]
      : null;

    if (data) {
      // Se tivermos dados novos...
      const novoValor = data.valor;
      const novoPesoBruto = data.peso_bruto;

      let mudouItem = false;

      // Atualiza valor se mudou
      if (novoValor != null && !Number.isNaN(novoValor) && Number(novoValor) !== Number(it.valor)) {
        it.valor = Number(novoValor);
        mudouItem = true;
      }

      // Atualiza peso_bruto se mudou (ou se não tinha)
      if (novoPesoBruto != null && Number(novoPesoBruto) !== Number(it.peso_bruto || 0)) {
        it.peso_bruto = Number(novoPesoBruto);
        mudouItem = true;
      }

      if (mudouItem) mudou = true;
      return it;
    }
    return it;
  });

  if (!mudou) return;

  // Atualiza a coluna de valor na grade (7ª coluna) e recalcula totais
  const rows = Array.from(document.querySelectorAll("#tbody-itens tr"));
  rows.forEach((tr, i) => {
    const tdValor = tr.querySelector("td:nth-child(7)");
    if (!tdValor) return;
    const v = itens[i] ? (itens[i].valor || 0) : 0;
    tdValor.textContent = fmtMoney(v);
  });

  await recalcTudo();
}
// Habilita/desabilita todos os campos e a grade
function setFormDisabled(disabled) {
  // topo
  document.querySelectorAll('input, select').forEach(el => {
    // não travar o botão, só inputs/selects
    if (['BUTTON', 'A'].includes(el.tagName)) return;
    if (el.id === 'iva_st_toggle' && !disabled) return;
    el.disabled = disabled;
  });

  // grade
  document.querySelectorAll('#tbody-itens input, #tbody-itens select').forEach(el => el.disabled = disabled);
  const chkAll = document.getElementById('chk-all');
  if (chkAll) chkAll.disabled = disabled;
}

// Função auxiliar para mapear item do backend para o formato do frontend
function mapBackendItemToFrontend(p, t) {
  return {
    // chaves que a grade espera:
    id_linha: p.id_linha ?? p.idLinha ?? null,
    codigo_tabela: p.codigo_produto_supra ?? p.codigo_tabela ?? '',
    descricao: p.descricao_produto ?? p.descricao ?? '',
    embalagem: p.embalagem ?? '',
    peso_liquido: Number(p.peso_liquido ?? 0),
    valor: Number(p.valor_produto ?? p.valor ?? 0),

    // comerciais/fiscais
    desconto: Number(p.comissao_aplicada ?? 0),      // mantém em R$ pra exibir
    acrescimo: Number(p.ajuste_pagamento ?? 0),      // mantém em R$ pra exibir
    plano_pagamento: p.codigo_plano_pagamento ?? p.plano_pagamento ?? null,
    frete_kg: Number(p.frete_kg ?? 0),
    ipi: Number(p.ipi ?? 0),
    icms_st: Number(p.icms_st ?? 0),
    iva_st: Number(p.iva_st ?? 0),
    grupo: p.grupo ?? null,
    departamento: p.departamento ?? null,

    // totais que você já exibe na tela
    total_sem_frete: Number(p.valor_s_frete ?? p.total_sem_frete ?? 0),

    // Markup (carregar do backend)
    markup: Number(p.markup ?? 0),
    valor_final_markup: Number(p.valor_final_markup ?? 0),
    valor_s_frete_markup: Number(p.valor_s_frete_markup ?? 0),

    // guarda para reaproveitar na hora do POST
    __descricao_fator_label: p.descricao_fator_comissao || null,
    __plano_pagto_label: p.codigo_plano_pagamento || null, // já vem "COD - desc" às vezes
    fornecedor: t.fornecedor || '',
    status_atual: p.status_atual ?? 'ATIVO', // <--- Mapeia status

    // Complementos finais
    peso_liquido: Number(p.peso_liquido ?? p.peso ?? p.peso_kg ?? p.pesoLiquido ?? 0),
    peso_bruto: Number(p.peso_bruto ?? 0),
    tipo: p.tipo ?? p.grupo ?? p.departamento ?? null
  };
}

function onDuplicar() {
  // guarda a tabela de ORIGEM para poder voltar na hora do Cancelar
  sourceTabelaId = currentTabelaId ? String(currentTabelaId) : null;
  if (sourceTabelaId) sessionStorage.setItem('TP_SOURCE_ID', sourceTabelaId);

  // entra em duplicação: libera campos e garante que será POST
  setMode(MODE.DUP);
  currentTabelaId = null;      // POST

  // 🧽 Limpa TODO o cabeçalho (nome e cliente)
  const nome = document.getElementById('nome_tabela');
  const cli = document.getElementById('cliente_nome');
  const cod = document.getElementById('codigo_cliente');
  const ramo = document.getElementById('ramo_juridico');
  const frete = document.getElementById('frete_kg');
  const cond = document.getElementById('plano_pagamento');
  const desc = document.getElementById('desconto_global');

  if (nome) nome.value = '';
  if (cli) cli.value = '';
  if (cod) cod.value = '';
  if (ramo) ramo.value = '';

  // if (frete) frete.value = 0; // KEEP
  // if (cond) cond.value = '';
  // duplicado if (cond) cond.value = ''; // clean up
  // if (desc) desc.value = '';
  console.log("onDuplicar: Preservando Frete, Condição e Desconto.");

  const mk = document.getElementById('markup_global');
  // if (mk) mk.value = ''; // KEEP

  // flags de cliente “livre” e travas do IVA
  window.isClienteLivreSelecionado = false;
  const iva = document.getElementById('iva_st_toggle');
  if (iva) { iva.checked = false; iva.disabled = true; }
  enforceIvaLockByCliente?.();

  atualizarPillTaxa?.();
  atualizarPillDesconto?.();
  refreshToolbarEnablement?.();

  // Renderiza IMEDIATAMENTE para não dar delay visual (mostra dados preservados)
  renderTabela();

  // Atualiza preços ao entrar no modo duplicar (em background)
  atualizarPrecosAtuais()
    .then(() => recalcTudo())
    .catch(err => console.error("Erro ao atualizar preços em onDuplicar:", err));
}

// MOSTRAR/OCULTAR botões corretamente em todos os modos
function toggleToolbarByMode() {
  const show = (id, visible) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.toggle('hidden', !visible);
  };

  const hasId = !!currentTabelaId;
  const isView = currentMode === MODE.VIEW;
  const isEditLike = currentMode === MODE.EDIT || currentMode === MODE.DUP || currentMode === MODE.NEW;
  const isEditOrDup = currentMode === MODE.EDIT || currentMode === MODE.DUP;

  // Listar: APENAS quando NÃO há id (tela nova)
  show('btn-listar', currentMode === MODE.NEW);

  // Buscar: em NEW/EDIT/DUP (quando mexendo)
  show('btn-buscar', isEditLike);

  // Editar/Duplicar: apenas em VIEW com id
  show('btn-editar', isView && hasId);
  show('btn-duplicar', isView && hasId);

  // Remover/Salvar: em NEW/EDIT/DUP
  show('btn-remover-selecionados', isEditLike);
  show('btn-salvar', isEditLike);

  // Cancelar:
  //  - visível em EDIT/DUP
  //  - e também em VIEW com id (atua como voltar pra lista)
  show('btn-cancelar', isEditOrDup || (isView && hasId));
}

// AÇÕES DE BOTÃO
function onEditar() {
  if (currentTabelaId) sessionStorage.setItem('TP_LAST_VIEW_ID', String(currentTabelaId));
  setMode(MODE.EDIT);
  // Atualiza preços ao entrar no modo edição
  atualizarPrecosAtuais()
    .then(() => recalcTudo())
    .catch(err => console.error("Erro ao atualizar preços em onEditar:", err));
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
  const peso = Number(item.peso_liquido || 0);
  const pesoBruto = Number(item.peso_bruto || 0);

  // 1) DESCONTO/FATOR → base líquida
  const descontoValor = valor * Number(fator || 0);
  const liquido = Math.max(0, valor - descontoValor);

  // 2) Condição SOBRE o líquido
  const acrescimoCond = liquido * Number(taxaCond || 0);

  // 3) Frete (agora usa Peso Bruto se disponível, senão Liquido)
  const pesoParaFrete = (pesoBruto > 0) ? pesoBruto : peso;
  const freteValor = (Number(freteKg || 0) / 1000) * pesoParaFrete;

  // 4) Preço comercial sem impostos (líquido + condição)
  const precoBase = liquido + acrescimoCond;

  return { acrescimoCond, freteValor, descontoValor, precoBase, liquido }
}


async function previewFiscalLinha(payload) {
  const r = await fetch(`${API_BASE}/fiscal/preview-linha`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const txt = await r.text().catch(() => '');
    throw new Error(txt || 'Falha ao calcular preview fiscal');
  }
  return r.json();
}

function normaliza(s) { return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }

// formata CNPJ/CPF para exibir bonito
function fmtDoc(s) {
  const d = String(s || '').replace(/\D/g, '');
  if (d.length === 14) return d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
  if (d.length === 11) return d.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
  return s || '';
}

// chamada única ao backend (aceita q= ou query=)
async function buscarClientes(term) {
  const q = (term || '').trim();
  if (q.length < 2) return [];

  const api = API_BASE.replace(/\/$/, '');
  const bases = [
    `${api}/tabela_preco/busca_cliente`,
    `${api}/tabela_preco/busca_cliente/`,
  ];
  const params = ['q', 'query', 'nome', 'term', 'busca'];

  // tenta GET com várias chaves (?q=, ?query=, etc) e normaliza a resposta
  for (const base of bases) {
    for (const k of params) {
      try {
        const r = await fetch(`${base}?${k}=${encodeURIComponent(q)}`, { cache: 'no-store' });
        if (!r.ok) continue;

        const data = await r.json();
        const arr =
          Array.isArray(data) ? data :
            Array.isArray(data?.results) ? data.results :
              Array.isArray(data?.clientes) ? data.clientes :
                Array.isArray(data?.items) ? data.items :
                  (data && (data.nome || data.cnpj)) ? [data] : [];

        if (arr.length) return arr;
      } catch {/* tenta próximo */ }
    }
  }

  // fallback: GET sem query e filtro no front (SÓ por nome/CNPJ)
  try {
    const r2 = await fetch(bases[0], { cache: 'no-store' });
    if (!r2.ok) return [];
    const all = await r2.json();

    const nq = normaliza(q);
    const qCnj = q.replace(/\D/g, '');
    return (all || []).filter(c => {
      const nome = normaliza(c.nome_cliente || c.razao || c.razao_social || c.fantasia || c.NOME || '');
      const cnpj = String(c.cnpj || c.CNPJ || '').replace(/\D/g, '');
      return (nome.includes(nq) || (qCnj && cnpj.includes(qCnj)));
    });
  } catch { return []; }
}

function setupClienteAutocomplete() {
  const input = document.getElementById('cliente_nome');
  const box = document.getElementById('cliente_suggestions');
  if (!input || !box) return;

  let items = [], idx = -1, timer = null;

  function render() {
    box.innerHTML = items.map((c, i) => {
      if (c.__raw) {
        return `<div class="suggest ${i === idx ? 'active' : ''}" data-i="${i}" style="padding:6px 8px;cursor:pointer">
                  <div>Usar: <strong>"${c.nome}"</strong></div>
                  <small style="opacity:.7">não encontrado — gravar como texto</small>
                </div>`;
      }
      const linha = [fmtDoc(c.cnpj), c.nome].filter(Boolean).join(' - ');
      return `<div class="suggest ${i === idx ? 'active' : ''}" data-i="${i}" style="padding:6px 8px;cursor:pointer">
                <div>${linha}</div>
              </div>`;
    }).join('');
    box.style.display = items.length ? 'block' : 'none';
  }

  function selectItem(i) {
    const c = items[i]; if (!c) return;

    const nomeEl = document.getElementById('cliente_nome');
    const codEl = document.getElementById('codigo_cliente');
    const ramoEl = document.getElementById('ramo_juridico');
    const ivaChk = document.getElementById('iva_st_toggle');
    if (ivaChk) { ivaChk.checked = false; ivaChk.disabled = true; window.ivaStAtivo = false; }
    window.isClienteLivreSelecionado = false;

    enforceIvaLockByCliente();

    if (c.__raw) {
      // cliente “livre” (gravar como texto)
      if (nomeEl) nomeEl.value = c.nome;
      if (codEl) codEl.value = '';          // sem código
      if (ramoEl) ramoEl.value = '';

      window.isClienteLivreSelecionado = true;
      window.currentClientMarkup = 0; // ✅ Reset markup for free/manual client
      if (ivaChk) {
        ivaChk.disabled = false;              // ✅ habilita para você decidir
        // não marco/desmarco aqui — decisão manual
      }
      saveHeaderSnapshot?.();

    } else {
      // cliente cadastrado
      if (nomeEl) nomeEl.value = [fmtDoc(c.cnpj), c.nome].filter(Boolean).join(' - ');
      if (codEl) codEl.value = c.codigo ?? '';
      if (ramoEl) ramoEl.value = c.ramo_juridico ?? c.ramo ?? '';
      window.currentClientMarkup = Number(c.markup || 0); // Sets default markup global

      // Apply markup to all existing items
      if (itens && itens.length > 0) {
        itens.forEach(it => {
          it.markup = currentClientMarkup;
        });
        renderTabela();
      }

      // aplica preferência vinda do cadastro, mas TRAVADO
      const pref = c.iva_st ?? c.usa_iva_st ?? c.st ?? c.calcula_st ?? null;
      if (ivaChk) {
        if (pref != null) {
          ivaChk.checked = parseBool(pref);
        } else {
          // Null preference fallback: check Ramo
          const r = (c.ramo_juridico || c.ramo || '').toLowerCase();
          if (r.includes('revenda')) {
            ivaChk.checked = true;
          } else {
            ivaChk.checked = false;
          }
        }
        ivaChk.disabled = true;              // 🔒 travado para cliente cadastrado
      }
      window.isClienteLivreSelecionado = false;
      saveHeaderSnapshot?.();
    }

    function ensureHasId() {
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
    Promise.resolve(recalcTudo()).catch(() => { });
  }


  async function doSearch(q) {
    const typed = (q || '').trim();
    if (typed.length < 2) { items = []; render(); return; }

    const data = await buscarClientes(typed);

    // mapeia campos do back
    // mapeia campos do back (pega várias chaves possíveis)
    const mapped = (data || []).map(c => ({
      // captura o código do cliente com várias variações comuns
      codigo: c.codigo ?? c.id ?? c.id_cliente ?? c.codigo_cliente ?? c.codigoCliente ?? c.CODIGO ?? c.COD_CLIENTE ?? c.cod ?? null,
      nome: c.nome_cliente ?? c.nomeCliente ?? c.NOME_CLIENTE ?? c.nome ?? c.razao ?? c.razao_social ?? c.razaoSocial ?? c.fantasia ?? '',
      cnpj: c.cnpj ?? c.CNPJ ?? c.cnpj_cpf ?? c.cnpjCpf ?? '',
      ramo_juridico: c.ramo_juridico ?? '',
      markup: c.cadastro_markup ?? 0 // Map markup from backend
    })).filter(c => (c.nome || c.cnpj));

    // 🔎 filtro FINAL no front (sempre), por nome ou CNPJ
    const nq = normaliza(typed);
    const qCnj = typed.replace(/\D/g, '');
    items = mapped.filter(c => {
      const nomeNorm = normaliza(c.nome || '');
      const cnpjDigits = String(c.cnpj || '').replace(/\D/g, '');
      return (nomeNorm.includes(nq) || (qCnj && cnpjDigits.includes(qCnj)));
    });

    if (!items.length) {
      // nada casou → oferece “usar o que digitei”
      items = [{ __raw: true, nome: typed }];
    }

    idx = -1;
    render();
  }

  input.addEventListener('input', () => {
    // 🧹 Limpa ID se digitar algo novo (assume novo/livre até selecionar)
    const codEl = document.getElementById('codigo_cliente');
    if (codEl && codEl.value) codEl.value = '';

    const ramoEl = document.getElementById('ramo_juridico');
    if (ramoEl) ramoEl.value = '';

    window.isClienteLivreSelecionado = false; // Reset flag, rely on text presence
    enforceIvaLockByCliente();

    clearTimeout(timer);
    timer = setTimeout(() => { doSearch(input.value); }, 250);
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' && items.length) { idx = (idx + 1) % items.length; render(); e.preventDefault(); }
    else if (e.key === 'ArrowUp' && items.length) { idx = (idx - 1 + items.length) % items.length; render(); e.preventDefault(); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      if (items.length && idx >= 0) {
        selectItem(idx);
      } else if (items.length) {
        // Auto-select first item if list exists but nothing highlighted
        selectItem(0);
      } else {
        // aceita o que foi digitado (raw text)
        const val = (input.value || '').trim();
        if (!val) return;
        items = [{ __raw: true, nome: val }];
        selectItem(0);
      }
    } else if (e.key === 'Escape') {
      box.innerHTML = ''; box.style.display = 'none';
    }
  });
  box.addEventListener('mousedown', e => {
    const el = e.target.closest('.suggest'); if (!el) return;
    selectItem(Number(el.dataset.i) || 0);
  });
  input.addEventListener('blur', () => {
    // --- AUTO-RECOVER on Blur ---
    // Se o usuário saiu do campo e o código ficou vazio (porque editou o nome),
    // tenta achar correspondência EXATA no que foi carregado/buscado para restaurar o código.
    const codEl = document.getElementById('codigo_cliente');
    if (codEl && !codEl.value && items.length > 0) {
      const currentVal = (input.value || '').trim();
      if (currentVal) {
        // Procura match exato por NOME (case insensitive)
        const matchIdx = items.findIndex(item =>
          !item.__raw && (item.nome || '').toLowerCase() === currentVal.toLowerCase()
        );

        if (matchIdx >= 0) {
          console.log("Auto-recovering client code for:", currentVal);
          selectItem(matchIdx);
        }
      }
    }

    setTimeout(() => { box.innerHTML = ''; box.style.display = 'none'; }, 150);
  });
}

// PATCH: bloqueio/controle do IVA_ST conforme cliente (livre x cadastrado)
function enforceIvaLockByCliente() {
  const ivaChk = document.getElementById('iva_st_toggle');
  const codigo = (document.getElementById('codigo_cliente')?.value || '').trim();
  const nome = (document.getElementById('cliente_nome')?.value || '').trim();

  if (!ivaChk) return;

  // Regra Ajustada:
  // - Tem Código? => Travado (Vem do cadastro, e usamos a pref do cliente).
  // - Não tem Código mas tem Nome? => Liberado (Cliente avulso).
  // - Sem Nome? => Travado (ainda não informou cliente).

  if (codigo) {
    ivaChk.disabled = true;
  } else if (nome) {
    ivaChk.disabled = false;
  } else {
    // Nada digitado
    ivaChk.disabled = true;
    ivaChk.checked = false;
  }

  window.ivaStAtivo = !!ivaChk.checked;
}



// --- Persistência compacta ---
// Função de salvar removida daqui (duplicada).
// Veja implementação unificada no final do arquivo.


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
    sel.appendChild(option(`${d.codigo} - ${(frac * 100).toFixed(2)}`, d.codigo));
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
  if (el) el.textContent = (fator != null && !isNaN(fator)) ? `${(Number(fator) * 100).toFixed(2)}` : '—';
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
  let id = urlParams.get('id'); // ← troque const por let

  // Fallback quando você voltou do "Buscar produto" sem ?id= na URL
  if (!id) {
    const ctx = sessionStorage.getItem('TP_CTX_ID');
    // Só usa o ctx se ele parecer um id real e se o modo anterior era edit/view/duplicate
    const retMode = sessionStorage.getItem(`TP_RETURN_MODE:${ctx || 'new'}`);
    if (ctx && ctx !== 'new' && (retMode === 'edit' || retMode === 'view' || retMode === 'duplicate')) {
      id = String(ctx);
    }
  }
  if (id) {
    const r = await fetch(`${API_BASE}/tabela_preco/${id}`);
    if (r.ok) {
      const t = await r.json();
      document.getElementById('nome_tabela').value = t.nome_tabela || '';
      document.getElementById('cliente_nome').value = t.cliente_nome || t.cliente || '';
      document.getElementById('ramo_juridico').value = t.ramo_juridico || '';

      // --- ROBUST SAFETY NET (GLOBAL VAULT) ---
      window.__clientState = {
        originalName: (t.cliente_nome || t.cliente || '').trim(),
        originalCode: (t.codigo_cliente || '').trim()
      };
      // Also update dataset for backwards compatibility/inspection
      const elNome = document.getElementById('cliente_nome');
      if (elNome) {
        elNome.dataset.originalName = window.__clientState.originalName;
        elNome.dataset.originalCode = window.__clientState.originalCode;
      }
      // --- END VAULT ---

      // NOVO: aplicar flag de ST que veio do backend
      const ivaChk = document.getElementById('iva_st_toggle');
      const flagSt = !!t.calcula_st;

      if (ivaChk) {
        ivaChk.checked = flagSt;
        window.ivaStAtivo = flagSt;
      }

      // NOVO: marcar cliente livre x cadastrado para o lock do checkbox
      if (t.codigo_cliente) {
        // tem código → tratamos como cadastrado
        window.isClienteLivreSelecionado = false;
      } else {
        // sem código → cliente livre (flag vem da tabela)
        window.isClienteLivreSelecionado = true;
      }

      // NOVO: aplica a regra de travar/destravar conforme tipo de cliente
      if (typeof enforceIvaLockByCliente === 'function') {
        enforceIvaLockByCliente();
      }

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
        id_linha: p.id_linha ?? p.idLinha ?? null,
        codigo_tabela: p.codigo_produto_supra ?? p.codigo_tabela ?? '',
        descricao: p.descricao_produto ?? p.descricao ?? '',
        embalagem: p.embalagem ?? '',
        peso_liquido: Number(p.peso_liquido ?? 0),
        valor: Number(p.valor_produto ?? p.valor ?? 0),

        // comerciais/fiscais
        desconto: Number(p.comissao_aplicada ?? 0),      // mantém em R$ pra exibir
        acrescimo: Number(p.ajuste_pagamento ?? 0),      // mantém em R$ pra exibir
        plano_pagamento: p.codigo_plano_pagamento ?? p.plano_pagamento ?? null,
        frete_kg: Number(p.frete_kg ?? 0),
        ipi: Number(p.ipi ?? 0),
        icms_st: Number(p.icms_st ?? 0),
        iva_st: Number(p.iva_st ?? 0),
        grupo: p.grupo ?? null,
        departamento: p.departamento ?? null,

        // totais que você já exibe na tela
        total_sem_frete: Number(p.valor_s_frete ?? p.total_sem_frete ?? 0),

        // Markup (carregar do backend)
        markup: Number(p.markup ?? 0),
        valor_final_markup: Number(p.valor_final_markup ?? 0),
        valor_s_frete_markup: Number(p.valor_s_frete_markup ?? 0),

        // guarda para reaproveitar na hora do POST
        __descricao_fator_label: p.descricao_fator_comissao || null,
        __plano_pagto_label: p.codigo_plano_pagamento || null, // já vem "COD - desc" às vezes
        fornecedor: t.fornecedor || '',
        status_atual: p.status_atual ?? 'ATIVO' // <--- Mapeia status
      }));

      itens = itens.map(p => ({
        ...p, peso_liquido: Number(p.peso_liquido ?? p.peso ?? p.peso_kg ?? p.pesoLiquido ?? 0),
        tipo: p.tipo ?? p.grupo ?? p.departamento ?? null

      }));
      renderTabela();
      // Removido bloqueio do recálculo para renderização instantânea
      // if (typeof recalcTudo === 'function') {
      //   await Promise.resolve(recalcTudo()).catch(() => { });
      // }

      // Atualiza a pill e recálculo
      atualizarPillTaxa();

      // Checa por inativos
      const inativos = itens.filter(i => i.status_atual && i.status_atual !== 'ATIVO');
      if (inativos.length > 0) {
        // setTimeout para não bloquear a renderização inicial
        setTimeout(() => showOsModal({ title: 'Atenção', message: `⚠️ ATENÇÃO: Existem ${inativos.length} produtos com status INATIVO nesta tabela.<br>Por favor, remova-os.`, type: 'alert' }), 500);
      }


      // >>> NOVO: fator global (se todos iguais)
      const dg = document.getElementById('desconto_global');
      if (dg) {
        const fatores = (itens || []).map(x => {
          if (x.fator_comissao != null && !isNaN(x.fator_comissao)) return Number(x.fator_comissao);
          // Fallback: tentar pelo label "COD - xx,yy"
          const lbl = (x.__descricao_fator_label || x.descricao_fator_comissao || '').trim();
          if (!lbl) return null;
          const code = lbl.split(' - ')[0].trim();
          const frac = Object.prototype.hasOwnProperty.call(mapaDescontos, code)
            ? Number(mapaDescontos[code]) : null;
          return Number.isFinite(frac) ? frac : null;
        }).filter(v => v != null && !isNaN(v));

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
      const __ctx = sessionStorage.getItem('TP_CTX_ID');
      const __ret = sessionStorage.getItem(`TP_RETURN_MODE:${__ctx || 'new'}`);
      if (__ret === MODE.EDIT || __ret === MODE.DUP) {
        // não muda o modo aqui; o init restaura já já
      } else {
        setMode('view');
      }
      return;
    }
  }

  const novos = obterItensDaSessao();              // o que veio do picker nesta volta
  itens = mergeItensExistentesENovos(itens, novos); // ✅ MESCLA em vez de substituir
  itens = itens.map(p => ({ ...p, ipi: Number(p.ipi ?? 0), iva_st: Number(p.iva_st ?? 0) }));
  itens = itens.map(p => ({
    ...p, peso_liquido: Number(p.peso_liquido ?? p.peso ?? p.peso_kg ?? p.pesoLiquido ?? 0),
    peso_bruto: Number(p.peso_bruto ?? 0),
    tipo: p.tipo ?? p.grupo ?? p.departamento ?? null
  }));
  // (opcional, mas recomendado) já limpa o buffer legado para não reaplicar depois
  try { sessionStorage.removeItem('criacao_tabela_preco_produtos'); } catch { }
  renderTabela();
  setMode('new');
}

// --- Shared Logic for Fator/Condição Determination ---
function determineFatorCode(item) {
  // 0) Priority: Persisted/Explicit Code
  if (item.__fator_codigo && mapaDescontos && Object.prototype.hasOwnProperty.call(mapaDescontos, item.__fator_codigo)) {
    return item.__fator_codigo;
  }

  // 1) Backend Label (e.g., "15 - 0")
  const lbl = (item.__descricao_fator_label || '').trim();
  if (lbl) {
    const codeFromLbl = lbl.split(' - ')[0].trim();
    if (codeFromLbl && mapaDescontos && Object.prototype.hasOwnProperty.call(mapaDescontos, codeFromLbl)) {
      return codeFromLbl;
    }
  }

  // 2) Numeric Match
  if (item.fator_comissao != null && !isNaN(item.fator_comissao) && mapaDescontos) {
    const match = Object.entries(mapaDescontos).find(([, f]) => Math.abs(Number(f) - Number(item.fator_comissao)) < 0.0001);
    if (match) return match[0];
  }

  // 3) Inference from Discount/Value
  if (Number(item.valor || 0) > 0 && mapaDescontos) {
    const fatorInferido = Number(item.desconto || 0) / Number(item.valor || 1);
    if (fatorInferido > 1e-6) {
      const match = Object.entries(mapaDescontos).find(([, f]) => Math.abs(Number(f) - fatorInferido) < 1e-6);
      if (match) return match[0];
    }
  }

  return '';
}

function determineCondicaoCode(item) {
  // 0) Priority: Persisted Code
  if (item.plano_pagamento_cod) return item.plano_pagamento_cod;

  // 1) Text matching or extraction
  if (item.plano_pagamento) {
    // Try extracting "001" from "001 - Vista"
    const parts = String(item.plano_pagamento).split(' - ');
    const potentialCode = parts[0].trim();

    // Validation? We assume if it looks like a code, it is.
    if (potentialCode) return potentialCode;
  }

  return '';
}

function criarLinha(item, idx) {
  const tr = document.createElement('tr');
  tr.dataset.idx = idx;

  const tdSel = document.createElement('td');
  const chk = document.createElement('input'); chk.type = 'checkbox'; chk.className = 'chk-linha';
  tdSel.appendChild(chk);

  const tdCod = document.createElement('td'); tdCod.textContent = item.codigo_tabela || '';
  const tdDesc = document.createElement('td');

  if (item.status_atual && item.status_atual !== 'ATIVO') {
    tr.classList.add('row-inactive');
    tdDesc.innerHTML = `<span class="badge-inactive">INATIVO</span> ${item.descricao || ''}`;
    tr.title = `Produto com status: ${item.status_atual}`;
  } else {
    tdDesc.textContent = item.descricao || '';
  }

  const tdEmb = document.createElement('td'); tdEmb.textContent = item.embalagem || '';
  const tdPeso = document.createElement('td'); tdPeso.className = 'num'; tdPeso.textContent = fmt4(item.peso_liquido || 0);
  const tdValor = document.createElement('td'); tdValor.className = 'num'; tdValor.textContent = fmtMoney(item.valor || 0);

  // % (Fator/Desconto) — COLUNA ÚNICA por linha (override quando alterado)
  const tdPercent = document.createElement('td');
  const selPercent = document.createElement('select');
  selPercent.appendChild(option('—', ''));

  // popula com o mesmo dicionário do cabeçalho (mapaDescontos: {codigo -> fração 0..1})
  Object.entries(mapaDescontos).forEach(([cod, frac]) => {
    selPercent.appendChild(option(`${cod} - ${(Number(frac) * 100).toFixed(2)}`, cod));
  });

  // USE SHARED HELPER
  selPercent.value = determineFatorCode(item);

  // PERSIST INITIAL VALUE immediately (Sync State)
  if (selPercent.value) {
    item.__fator_codigo = selPercent.value;
    item.fator_comissao = Number(mapaDescontos[selPercent.value] || 0);
  }

  selPercent.addEventListener('change', () => {
    const code = selPercent.value || '';
    const frac = (Object.prototype.hasOwnProperty.call(mapaDescontos, code) ? Number(mapaDescontos[code]) : 0);
    itens[idx].fator_comissao = (!isNaN(frac) ? frac : 0);
    itens[idx].__fator_codigo = code; // <-- guarda o código (ex.: "15")
    itens[idx].__descricao_fator_label = selPercent.options[selPercent.selectedIndex]?.textContent?.trim() || '';
    itens[idx].__overridePercent = true;
    recalcLinha(tr);

    try {
      const selsPct = Array.from(document.querySelectorAll('#tbody-itens tr td:nth-child(8) select'));
      const vals = new Set(selsPct.map(s => (s.value || '').trim()).filter(v => v !== ''));
      const hdr = document.getElementById('desconto_global');
      if (hdr && hdr.dataset.userEdited !== '1') {
        hdr.value = (vals.size === 1) ? [...vals][0] : '';
        atualizarPillDesconto?.();
        saveHeaderSnapshot?.();
      }
    } catch { }
  });

  tdPercent.appendChild(selPercent);

  const tdDescAplic = document.createElement('td'); tdDescAplic.className = 'num'; tdDescAplic.textContent = '0,00';

  // Condição por linha (código) — NOVO
  const tdCondCod = document.createElement('td');
  const selCond = document.createElement('select');
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


  // 1) Fallback: Text matching or code extraction
  if (!selCond.value) {
    const codCondLinha = String(item.plano_pagamento || '').split(' - ')[0].trim();
    selCond.value = codCondLinha || '';
  }

  // PERSIST INITIAL VALUE immediately (Sync State)
  if (selCond.value) {
    item.plano_pagamento_cod = selCond.value;
    // Also sync text description if missing
    if (!item.plano_pagamento) {
      item.plano_pagamento = selCond.options[selCond.selectedIndex]?.textContent || '';
    }
  }

  tdCondCod.appendChild(selCond);

  selCond.addEventListener('change', () => {
    itens[idx].plano_pagamento_cod = selCond.value || null; // Persist Code
    // Also save text for legacy support
    const opt = selCond.options[selCond.selectedIndex];
    itens[idx].plano_pagamento = opt ? opt.textContent : (selCond.value || null);

    recalcLinha(tr);

    try {
      const sels = Array.from(document.querySelectorAll('#tbody-itens tr td:nth-child(10) select'));
      const vals = new Set(sels.map(s => (s.value || '').trim()).filter(v => v !== ''));
      const hdr = document.getElementById('plano_pagamento');
      if (hdr && hdr.dataset.userEdited !== '1') {
        hdr.value = (vals.size === 1) ? [...vals][0] : '';
        atualizarPillTaxa?.();
        saveHeaderSnapshot?.();
      }
    } catch { }
  });

  const tdCondVal = document.createElement('td'); tdCondVal.className = 'num'; tdCondVal.textContent = '0,00';

  // MARKUP Input
  const tdMarkup = document.createElement('td');
  const inpMarkup = document.createElement('input');
  inpMarkup.type = 'number'; inpMarkup.step = '0.01'; inpMarkup.className = 'field-markup num';
  // Use existing item markup or fallback to client default
  const mVal = (item.markup != null) ? Number(item.markup) : currentClientMarkup;
  item.markup = mVal; // Sync item
  inpMarkup.value = mVal.toFixed(2); // Format for display? Or raw? input type=number needs dot. 
  // Wait, local String uses comma? step 0.01. Input number usually requires dot.
  // fmtMoney uses comma.
  // Let's use clean input
  inpMarkup.style.width = '70px';
  inpMarkup.addEventListener('change', () => {
    let v = parseFloat(inpMarkup.value.replace(',', '.')); // Fix potential comma issue
    if (isNaN(v)) v = 0;
    itens[idx].markup = v;
    recalcLinha(tr); // FIXED: Trigger recalculation
  });
  tdMarkup.appendChild(inpMarkup);

  // -- NOVAS COLUNAS DE MARKUP (exibição calculada)
  // Serão preenchidas em recalcLinha
  const tdFinalMarkup = document.createElement('td');
  tdFinalMarkup.className = 'num col-mk-derived';
  tdFinalMarkup.textContent = '0,00';

  const tdSemFreteMarkup = document.createElement('td');
  tdSemFreteMarkup.className = 'num col-mk-derived';
  tdSemFreteMarkup.textContent = '0,00';

  const tdFrete = document.createElement('td'); tdFrete.className = 'num'; tdFrete.textContent = '0,00';


  // IPI e IVA_ST (%) — Inicializar com o valor salvo no item, se houver
  const tdIpiR$ = document.createElement('td'); tdIpiR$.className = 'num col-ipi'; tdIpiR$.textContent = fmtMoney(item.ipi || 0);
  const tdBaseStR$ = document.createElement('td'); tdBaseStR$.className = 'num col-base-st'; tdBaseStR$.textContent = fmtMoney(item.iva_st || 0);
  const tdIcmsProp$ = document.createElement('td'); tdIcmsProp$.className = 'num col-icms-proprio'; tdIcmsProp$.textContent = fmtMoney(item.icms_st || 0); // Nota: icms_st aqui mapeia para col-icms-proprio no backend? Revisar se necessário, mantendo compatibilidade
  const tdIcmsCheio$ = document.createElement('td'); tdIcmsCheio$.className = 'num col-icms-st-cheio'; tdIcmsCheio$.textContent = '0,00'; // Cheio/Reter geralmente não salvos individualmente no item simples, recalculados
  const tdIcmsReter$ = document.createElement('td'); tdIcmsReter$.className = 'num col-icms-st-reter'; tdIcmsReter$.textContent = '0,00';


  const tdGrupo = document.createElement('td'); tdGrupo.textContent = [item.grupo, item.departamento].filter(Boolean).join(' / ');
  const tdFinal = document.createElement('td'); tdFinal.className = 'num col-total'; tdFinal.textContent = fmtMoney(item.valor || 0); tr.appendChild(tdFinal);
  const tdTotalSemFrete = document.createElement('td'); tdTotalSemFrete.className = 'num col-total-sem-frete'; tdTotalSemFrete.textContent = '0,00'; tr.appendChild(tdTotalSemFrete);

  tr.append(
    tdSel, tdCod, tdDesc, tdEmb, tdGrupo,
    tdPeso, tdValor, tdPercent, tdDescAplic,
    tdCondCod, tdCondVal,
    tdFrete,
    tdIpiR$, tdBaseStR$, tdIcmsProp$, tdIcmsCheio$, tdIcmsReter$, tdFinal, tdTotalSemFrete,
    tdMarkup, // <--- MOVED TO END
    tdFinalMarkup, tdSemFreteMarkup // <--- ALREADY AT END
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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const out = await r.json();

  // use o que fizer sentido: total sem ST ou COM ST
  item.valor_liquido = out.total_linha;          // ou: out.total_linha_com_st
  item._motivos_iva = out.motivos_iva_st;        // útil pra debug na UI
  return item;
}

function buildFiscalInputsFromRow(tr, fallbackItem = null, idx = -1) {
  const item = fallbackItem || (itens || [])[idx] || (tr ? (itens || [])[Number(tr.dataset.idx)] : {}) || {};

  // DOM: fator por linha e condição (código)
  let fatorPct = 0;
  let codCond = '';
  if (tr) {
    fatorPct = Number(tr.querySelector('td:nth-child(8) select')?.value || 0);
    codCond = tr.querySelector('td:nth-child(10) select')?.value || '';
  } else {
    // Mobile writes to item.__fator_codigo and item.plano_pagamento_cod
    const cPct = item.__fator_codigo || '';
    fatorPct = (window.mapaDescontos && window.mapaDescontos[cPct] != null) ? Number(window.mapaDescontos[cPct]) * 100 : 0;
    codCond = item.plano_pagamento_cod || (item.plano_pagamento ? String(item.plano_pagamento).split(' - ')[0].trim() : '');
  }
  const fator = fatorPct / 100;
  const taxaCond = (window.mapaCondicoes && window.mapaCondicoes[codCond]) ?? 0;

  // DOM: frete global e toggles
  const freteKg = Number(document.getElementById('frete_kg')?.value || 0); // R$/kg
  const codigo_cliente = (document.getElementById('codigo_cliente')?.value || '').trim() || null;
  const ramoJuridico = (document.getElementById('ramo_juridico')?.value || '').trim() || null;
  const forcarST = !!document.getElementById('iva_st_toggle')?.checked;

  // Item básico
  const produtoId = tr ? (tr.querySelector('td:nth-child(2)')?.textContent || '').trim() : (item.codigo || item.codigo_tabela || '').trim();
  const tipo = String(item?.tipo || item?.grupo || item?.departamento || '').trim();
  const peso_bruto = Number(item?.peso_bruto || 0);
  const peso_liq = Number(item?.peso_liquido ?? item?.peso ?? item?.peso_kg ?? item?.pesoLiquido ?? 0);
  const peso_kg = (peso_bruto > 0) ? peso_bruto : peso_liq;

  // Preço base (espelha sua lógica da tela): valor + acrescimo(condição) - desconto(fator)
  const valor = Number(item?.valor || 0);
  const descontoValor = valor * Number(fator || 0);
  const liquido = Math.max(0, valor - descontoValor);
  const acrescimoCond = liquido * Number(taxaCond || 0);

  const precoBase = liquido + acrescimoCond;

  // Frete por linha (usando kg diretamente)
  const frete_linha = Number(freteKg || 0) * Number(peso_kg || 0);

  const payload = {
    codigo_cliente: codigo_cliente,
    forcar_iva_st: forcarST,
    produto_id: produtoId,
    ramo_juridico: ramoJuridico,
    peso_kg: Number(peso_kg || 0),
    tipo: tipo,
    preco_unit: Number(precoBase || 0),
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

  // === Inferir cabeçalho a partir da grade (uniformidade) ===
  try {
    const selsPct = Array.from(document.querySelectorAll('#tbody-itens tr td:nth-child(8) select'));
    const selsCond = Array.from(document.querySelectorAll('#tbody-itens tr td:nth-child(10) select'));

    // Fator (%)
    const valsPct = new Set(selsPct.map(s => (s.value || '').trim()).filter(v => v !== ''));
    const hdrPct = document.getElementById('desconto_global');
    if (hdrPct && hdrPct.dataset.userEdited !== '1') {
      hdrPct.value = (valsPct.size === 1) ? [...valsPct][0] : '';
      atualizarPillDesconto?.();
    }

    // Condição de pagamento
    const valsCond = new Set(selsCond.map(s => (s.value || '').trim()).filter(v => v !== ''));
    const hdrCond = document.getElementById('plano_pagamento');
    if (hdrCond && hdrCond.dataset.userEdited !== '1') {
      hdrCond.value = (valsCond.size === 1) ? [...valsCond][0] : '';
      atualizarPillTaxa?.();
    }
  } catch { }
  // Mobile Render Hook
  if (typeof renderMobileCards === 'function') renderMobileCards();
}

async function recalcLinha(tr) {

  const idx = Number(tr.dataset.idx);
  const item = itens[idx]; if (!item) return;

  const nextId = (Number(tr.dataset.reqId || 0) + 1);
  tr.dataset.reqId = String(nextId);
  const myId = String(nextId);

  const selPct = tr.querySelector('td:nth-child(8) select');
  let codePct = selPct ? (selPct.value || '') : '';

  // Fallback: se DOM vazio, tenta pegar do item
  if (!codePct && item.__fator_codigo) codePct = item.__fator_codigo;

  let fator = (mapaDescontos[codePct] != null) ? Number(mapaDescontos[codePct]) : 0;
  if (fator === 0 && item.fator_comissao) fator = Number(item.fator_comissao);

  const freteKg = Number(document.getElementById('frete_kg').value || 0);

  // Condição por linha → taxa
  const selCond = tr.querySelector('td:nth-child(10) select');
  let codCond = selCond ? selCond.value : '';

  // Fallback
  if (!codCond && item.plano_pagamento) {
    codCond = String(item.plano_pagamento).split(' - ')[0].trim();
  }

  const taxaCond = mapaCondicoes[codCond] ?? 0;

  // base comercial (sem imposto)
  const { acrescimoCond, freteValor, descontoValor, precoBase, liquido } =
    calcularLinha(item, fator, taxaCond, freteKg);

  // pinta colunas comerciais
  tr.querySelector('td:nth-child(9)').textContent = fmtMoney(descontoValor); // Desc. aplicado
  tr.querySelector('td:nth-child(11)').textContent = fmtMoney(acrescimoCond); // Cond. (R$)
  tr.querySelector('td:nth-child(12)').textContent = fmtMoney(freteValor);    // Frete (R$)



  try {
    const built = buildFiscalInputsFromRow(tr);

    // usa exatamente o que JÁ calculamos nesta função
    built.payload.preco_unit = precoBase;   // já calculado acima
    built.payload.frete_linha = freteValor;  // já calculado acima

    const f = await previewFiscalLinha(built.payload);
    item.ipi = Number((f.ipi ?? 0).toFixed(2));
    item.iva_st = Number((f.base_st ?? 0).toFixed(2));

    // Fix: Save correct fields for mobile display
    item._icmsProprio = Number((f.icms_proprio ?? 0).toFixed(2));
    item._stReter = Number((f.icms_st_reter ?? 0).toFixed(2));

    item.icms_st = Number((f.icms_proprio ?? 0).toFixed(2)); // Legacy (keep for safety)

    if (tr.dataset.reqId !== myId) return;

    const setCell = (sel, val) => {
      const el = tr.querySelector(sel);
      if (el) el.textContent = fmtMoney(val);
    };

    setCell('.col-ipi', f.ipi);
    setCell('.col-base-st', f.base_st);
    setCell('.col-icms-proprio', f.icms_proprio);
    setCell('.col-icms-st-cheio', f.icms_st_cheio);
    setCell('.col-icms-st-reter', f.icms_st_reter);
    setCell('.col-total', f.total_linha_com_st); // ou total_linha

    const totalFiscal = Number(f.total_linha_com_st ?? f.total_linha ?? 0);

    // ✅ aplica CONDIÇÃO (R$) sobre o líquido e soma no total final exibido
    const totalComercial = totalFiscal;

    const totalSemFrete = totalComercial - Number(freteValor || 0);
    const tdSemFrete = tr.querySelector('.col-total-sem-frete');
    if (tdSemFrete) tdSemFrete.textContent = fmtMoney(totalSemFrete);

    // --- CÁLCULO DAS COLUNAS DE MARKUP ---
    // Calcula SEMPRE para garantir que o item tenha os valores corretos para o Save
    const mkPct = Number(item.markup || 0);
    const factor = 1 + (mkPct / 100);

    const valFinMk = Number((totalComercial * factor).toFixed(2));
    const valSemMk = Number((totalSemFrete * factor).toFixed(2));

    // Persiste no objeto item
    item.valor_final_markup = valFinMk;
    item.valor_s_frete_markup = valSemMk;

    // Atualiza DOM se as colunas existirem
    const tdsMk = tr.querySelectorAll('.col-mk-derived');
    if (tdsMk.length === 2) {
      tdsMk[0].textContent = fmtMoney(valFinMk);
      tdsMk[1].textContent = fmtMoney(valSemMk);
    }

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


async function previewFiscalBatch(payload) {
  const r = await fetch(`${API_BASE}/fiscal/preview-batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const txt = await r.text().catch(() => '');
    throw new Error(txt || 'Falha ao calcular preview batch');
  }
  return r.json();
}

function applyFiscalToRow(tr, f, fallbackItem = null) {
  const item = fallbackItem || (tr ? itens[Number(tr.dataset.idx)] : null);
  if (!item) return;

  item.ipi = Number((f.ipi ?? 0).toFixed(2));
  item.iva_st = Number((f.base_st ?? 0).toFixed(2));
  item.icms_st = Number((f.icms_proprio ?? 0).toFixed(2));

  // Fix: Save correct fields for mobile display
  item._icmsProprio = Number((f.icms_proprio ?? 0).toFixed(2));
  item._stReter = Number((f.icms_st_reter ?? 0).toFixed(2));

  const setCell = (sel, val) => {
    if (!tr) return;
    const el = tr.querySelector(sel);
    if (el) el.textContent = fmtMoney(val);
  };

  setCell('.col-ipi', f.ipi);
  setCell('.col-base-st', f.base_st);
  setCell('.col-icms-proprio', f.icms_proprio);
  setCell('.col-icms-st-cheio', f.icms_st_cheio);
  setCell('.col-icms-st-reter', f.icms_st_reter);
  setCell('.col-total', f.total_linha_com_st);

  const totalFiscal = Number(f.total_linha_com_st ?? f.total_linha ?? 0);
  const totalComercial = totalFiscal;

  // Recalculo reverso do sem frete
  const freteValor = item._freteValor || 0; // Salvo no passo comercial
  const totalSemFrete = totalComercial - Number(freteValor || 0);

  if (tr) {
    const tdSemFrete = tr.querySelector('.col-total-sem-frete');
    if (tdSemFrete) tdSemFrete.textContent = fmtMoney(totalSemFrete);
  }

  // --- CÁLCULO DAS COLUNAS DE MARKUP ---
  const mkPct = Number(item.markup || 0);
  const factor = 1 + (mkPct / 100);

  const valFinMk = Number((totalComercial * factor).toFixed(2));
  const valSemMk = Number((totalSemFrete * factor).toFixed(2));

  item.valor_final_markup = valFinMk;
  item.valor_s_frete_markup = valSemMk;

  if (tr) {
    const tdsMk = tr.querySelectorAll('.col-mk-derived');
    if (tdsMk.length === 2) {
      tdsMk[0].textContent = fmtMoney(valFinMk);
      tdsMk[1].textContent = fmtMoney(valSemMk);
    }
    setCell('.col-total', totalComercial);
  }

  item._totalComercial = Number(totalComercial || 0);
  item.total_sem_frete = Math.max(0, item._totalComercial - freteValor);

  if (tr) {
    const td = tr.querySelector('.col-total-sem-frete');
    if (td) td.textContent = fmtMoney(item.total_sem_frete || 0);
  }

  // Sync missing fields
  item.valor_liquido = f.total_linha; // Compatibilidade
  item._motivos_iva = f.motivos_iva_st;
}

async function recalcTudo() {
  if (__recalcRunning) {
    __recalcPending = true;
    return;
  }
  __recalcRunning = true;
  document.body.style.cursor = 'wait'; // Feedback visual

  try {
    do {
      __recalcPending = false;
      const desktopRows = Array.from(document.querySelectorAll('#tbody-itens tr'));

      // 1. Coletar payloads (Commercial Calc)
      const batchItems = [];
      const rowMap = []; // { tr, item }

      for (let idx = 0; idx < itens.length; idx++) {
        const item = itens[idx];
        if (!item) continue;

        let tr = null;
        if (desktopRows.length > 0) {
          tr = desktopRows.find(r => Number(r.dataset.idx) === idx);
          if (tr && !tr.isConnected) continue;
        }

        // --- Lógica Comercial (Adapted to fallback to the item object for mobile) ---
        let codePct = '';
        if (tr) {
          const selPct = tr.querySelector('td:nth-child(8) select');
          if (selPct) codePct = selPct.value || '';
        }
        if (!codePct && item.__fator_codigo) codePct = item.__fator_codigo;

        let fator = (window.mapaDescontos && window.mapaDescontos[codePct] != null) ? Number(window.mapaDescontos[codePct]) : 0;
        if (fator === 0 && item.fator_comissao) fator = Number(item.fator_comissao);

        const freteKg = Number(document.getElementById('frete_kg')?.value || 0);

        let codCond = '';
        if (tr) {
          const selCond = tr.querySelector('td:nth-child(10) select');
          if (selCond) codCond = selCond.value;
        }
        if (!codCond && item.plano_pagamento) {
          codCond = String(item.plano_pagamento).split(' - ')[0].trim();
        }
        if (!codCond && item.plano_pagamento_cod) {
          codCond = item.plano_pagamento_cod;
        }

        const taxaCond = window.mapaCondicoes ? (window.mapaCondicoes[codCond] ?? 0) : 0;

        const { acrescimoCond, freteValor, descontoValor, precoBase } =
          calcularLinha(item, fator, taxaCond, freteKg);

        // Atualiza DOM Comercial
        if (tr) {
          const setTxt = (nth, v) => { const cel = tr.querySelector(`td:nth-child(${nth})`); if (cel) cel.textContent = fmtMoney(v); };
          setTxt(9, descontoValor);
          setTxt(11, acrescimoCond);
          setTxt(12, freteValor);
        }

        // Build Payload
        const built = buildFiscalInputsFromRow(tr, item, idx);
        built.payload.preco_unit = precoBase;
        built.payload.frete_linha = freteValor;

        // Save state for update step
        item._freteValor = Number(freteValor || 0);

        batchItems.push(built.payload);
        rowMap.push({ tr: tr, item: item });
      }

      if (batchItems.length === 0) continue;

      // 2. Batch Request
      const codigo_cliente = (document.getElementById('codigo_cliente')?.value || '').trim() || null;
      const ramoJuridico = (document.getElementById('ramo_juridico')?.value || '').trim() || null;
      const forcarST = !!document.getElementById('iva_st_toggle')?.checked;

      const batchPayload = {
        cliente_codigo: codigo_cliente,
        forcar_iva_st: forcarST,
        ramo_juridico: ramoJuridico,
        itens: batchItems
      };

      try {
        const resp = await previewFiscalBatch(batchPayload);
        const results = resp.results || [];

        // 3. Apply Results
        results.forEach((res, i) => {
          const mapData = rowMap[i];
          applyFiscalToRow(mapData.tr, res, mapData.item);
        });

      } catch (err) {
        console.error("Batch recalc failed:", err);
        // Feedback para o user não salvar dados incompletos
        showOsModal({ title: 'Erro', message: "Erro de conexão ao calcular impostos. Verifique sua internet e tente novamente.", type: 'alert' });
      }

    } while (__recalcPending);
  } finally {
    __recalcRunning = false;
    document.body.style.cursor = 'default';
    if (typeof renderMobileCards === 'function') renderMobileCards();
  }
}

async function aplicarFatorGlobal() {
  const selGlobal = document.getElementById('desconto_global');
  const code = selGlobal?.value || '';
  const fator = mapaDescontos[code];

  if (fator == null || isNaN(fator)) {
    showOsModal({ title: 'Aviso', message: 'Escolha um desconto válido.', type: 'alert' });
    return;
  }

  // Aplica em cada linha e sincroniza o select da linha
  document.querySelectorAll('#tbody-itens tr').forEach(tr => {
    const sel = tr.querySelector('td:nth-child(8) select'); // coluna unificada
    if (!sel) return;
    sel.value = code;
    // 🔑 dispara o mesmo fluxo do usuário (atualiza itens[idx] e recalcula)
    console.log(`Aplicando Fator Global: ${code} na linha com select`, sel);
    sel.dispatchEvent(new Event('change', { bubbles: true }));
  });
  await Promise.resolve(recalcTudo()).catch(() => { });
  const hdr = document.getElementById('desconto_global');
  if (hdr) { hdr.dataset.userEdited = ''; } // destrava
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
  if (__recalcRunning || __recalcPending) {
    await showOsModal({ title: 'Aviso', message: 'Aguarde o término do cálculo de impostos para salvar.', type: 'alert' });
    return;
  }

  const linhas = document.querySelectorAll('#tbody-itens tr');
  if (linhas.length === 0) {
    await showOsModal({ title: 'Aviso', message: 'Adicione pelo menos 1 produto à tabela antes de salvar.', type: 'alert' });
    // foca em algo útil da sua UI (ajuste se tiver um botão/field específico)
    document.querySelector('#busca_produto, #nome_tabela')?.focus();
    return;
  }

  // On mobile the desktop row selects don't exist — only validate header fields
  const isMobile = window.innerWidth <= 768;
  const fieldsToCheck = isMobile
    ? { '#nome_tabela': 'Informe o nome da tabela.', '#cliente_nome': 'Informe/selecione o cliente.' }
    : RequiredValidator.REQUIRED_FIELDS;

  const { ok, missing } = RequiredValidator.check(fieldsToCheck, document);
  if (!ok) {
    // If a header field failed and the header is collapsed, expand it first so the user can see
    const headerArea = document.getElementById('header-collapsible-area');
    const headerHasInvalid = missing.some(m => ['#nome_tabela', '#cliente_nome'].some(s => m.el === document.querySelector(s)));
    if (headerHasInvalid && headerArea?.classList.contains('collapsed')) {
      headerArea.classList.remove('collapsed');
      const btn = document.getElementById('btn-toggle-header');
      if (btn) btn.classList.remove('rotated');
    }
    // Build a helpful list of missing field names
    const fieldNames = missing.map(m => {
      if (m.selector.includes('nome_tabela')) return '• Nome da tabela';
      if (m.selector.includes('cliente_nome')) return '• Cliente';
      if (m.selector.includes('nth-child(8)')) return '• Classificação/Fator (algum item)';
      if (m.selector.includes('nth-child(10)')) return '• Condição de pagamento (algum item)';
      return '• Campo obrigatório';
    }).join('<br>');
    await showOsModal({ title: 'Aviso', message: `Preencha os campos obrigatórios:<br><br>${fieldNames}`, type: 'alert' });
    setTimeout(() => missing[0]?.el?.scrollIntoView?.({ behavior: 'smooth', block: 'center' }), 200);
    return;
  }

  const nome_tabela = document.getElementById('nome_tabela').value.trim();
  const cliente = document.getElementById('cliente_nome').value.trim();
  const frete_kg = Number(document.getElementById('frete_kg').value || 0);
  const ramo_juridico = document.getElementById('ramo_juridico').value || null;

  const produtos = Array.from(document.querySelectorAll('#tbody-itens tr'))
    .map(tr => {
      const idx = Number(tr.dataset.idx);
      const item = itens[idx];

      const selPct = tr.querySelector('td:nth-child(8) select');
      // On mobile, selects don't exist in the table — fall back to saved values in itens[]
      const codePct = selPct ? selPct.value : (item.__fator_codigo || '');
      const fator = (mapaDescontos[codePct] != null) ? Number(mapaDescontos[codePct]) : Number(item.fator_comissao || 0);

      const selCond = tr.querySelector('td:nth-child(10) select');
      // On mobile, fall back to plano_pagamento_cod saved by mobile card event handler
      const codCond = selCond ? (selCond.value || '') : (item.plano_pagamento_cod || String(item.plano_pagamento || '').split(' - ')[0].trim());
      const condLabel = selCond
        ? (selCond.options[selCond.selectedIndex]?.textContent || '').trim()
        : (item.plano_pagamento || codCond || '');

      const taxaCond = mapaCondicoes[codCond] || 0;
      const { acrescimoCond, freteValor, descontoValor } =
        calcularLinha(item, fator, taxaCond, frete_kg /* ivaStAtivo é ignorado aqui */);

      // On mobile, build fatorLabel from the saved code
      const fatorLabel = selPct
        ? (selPct.options[selPct.selectedIndex]?.textContent || '').trim()
        : (codePct ? `${codePct} - ${((Number(mapaDescontos[codePct] || 0)) * 100).toFixed(2)}` : (item.__descricao_fator_label || ''));


      let planoToSave = condLabel || '';
      if (codCond) {
        if (!planoToSave || !planoToSave.startsWith(codCond)) {
          planoToSave = planoToSave ? `${codCond} - ${planoToSave}` : codCond;
        }
      }
      // objeto do item (NÃO coloque nome_tabela/cliente/fornecedor aqui)
      const produto = {
        codigo_produto_supra: item.codigo_tabela,
        descricao_produto: item.descricao,
        embalagem: item.embalagem || '',
        peso_liquido: Number(item.peso_liquido ?? 0),
        peso_bruto: Number(item.peso_bruto ?? 0),

        valor_produto: Number(item.valor || 0),
        comissao_aplicada: Number(descontoValor.toFixed(2)),
        ajuste_pagamento: Number(acrescimoCond.toFixed(2)),
        descricao_fator_comissao: fatorLabel,
        codigo_plano_pagamento: planoToSave,

        valor_frete_aplicado: Number(freteValor.toFixed(2)),
        frete_kg: Number(frete_kg || 0),
        valor_frete: Number((item._totalComercial || 0).toFixed(2)),
        valor_s_frete: Number((item.total_sem_frete || 0).toFixed(2)),

        // Novos campos de Markup
        markup: Number(item.markup || 0),
        valor_final_markup: Number(item.valor_final_markup || 0),
        valor_s_frete_markup: Number(item.valor_s_frete_markup || 0),

        grupo: item.grupo || null,
        departamento: item.departamento || null,
        ipi: Number(item.ipi || 0),
        icms_st: Number(item.icms_st || 0),
        iva_st: Number(item.iva_st || 0)
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

  console.table(produtos.map(p => ({ id_linha: p.id_linha, codigo: p.codigo_produto_supra, valor: p.valor_produto, plano: p.codigo_plano_pagamento })));

  const fornecedorHeader = inferirFornecedorDaGrade();
  let codigo_cliente = (document.getElementById('codigo_cliente')?.value || '').trim() || null;

  // --- SAFETY NET CHECK (GLOBAL VAULT) ---
  if (!codigo_cliente && window.__clientState && window.__clientState.originalCode) {
    const elNome = document.getElementById('cliente_nome');
    const curName = (elNome?.value || '').trim();

    // Se o nome atual é igual ao original (guardado no cofre), restaura o código
    if (curName && curName === window.__clientState.originalName) {
      console.warn("Global Vault: Restaurando código do cliente perdido na edição.");
      codigo_cliente = window.__clientState.originalCode;

      // Visual feedback
      const elCode = document.getElementById('codigo_cliente');
      if (elCode) elCode.value = codigo_cliente;
    }
  }

  const calcula_st = !!document.getElementById('iva_st_toggle')?.checked;
  // Se codigo_cliente for nulo, mande null (não grave "Não cadastrado" string)
  const payload = { nome_tabela, cliente, codigo_cliente, ramo_juridico, fornecedor: fornecedorHeader, calcula_st, produtos };

  // --- SAFETY CHECK FOR EMAIL ---
  // Se tem nome mas não tem código, o e-mail não vai funcionar.
  if (cliente && !codigo_cliente) {
    const confirmMsg = "⚠️ ATENÇÃO:<br><br>" +
      "O cliente informado NÃO foi vinculado ao cadastro (está sem código).<br>" +
      "Isso significa que o sistema NÃO conseguirá enviar o e-mail de confirmação automaticamente.<br><br>" +
      "Deseja salvar mesmo assim?";
    const proceed = await showOsModal({ title: 'Confirmação', message: confirmMsg, type: 'confirm' });
    if (!proceed) {
      // Usuário cancelou para corrigir
      document.getElementById('cliente_nome')?.focus();
      return;
    }
  }
  try {
    console.log("Payload enviando para salvarTabelaPreco:", JSON.stringify(payload, null, 2));
    const resp = await salvarTabelaPreco(payload);
    return resp;
  } catch (e) {
    console.error(e);
    await showOsModal({ title: 'Erro', message: e.message || 'Erro ao salvar a tabela.', type: 'alert' });
    return null;
  }
}


function validarCabecalhoMinimo() {
  const nome = document.getElementById('nome_tabela')?.value?.trim();
  const cliente = document.getElementById('cliente_nome')?.value?.trim();

  if (!nome || !cliente) return false;

  // valida ordem das datas (se ambos presentes)

  return true;
}

// Habilitar/desabilitar (Salvar e Remover) conforme conteúdo
function refreshToolbarEnablement() {
  const temLinhas = document.querySelectorAll('#tbody-itens tr').length > 0;
  const algumaMarcada = document.querySelectorAll('#tbody-itens .chk-linha:checked').length > 0;
  const cabecalhoOk = validarCabecalhoMinimo();

  const btnsSalvar = [
    document.getElementById('btn-salvar'),
    document.getElementById('btn-mobile-save')
  ].filter(Boolean);

  const btnRemover = document.getElementById('btn-remover-selecionados');

  // Usa classe visual em vez de disabled nativo: assim o clique ainda dispara
  // e salvarTabela() pode mostrar os campos faltantes ao usuário.
  const podeSalvar = temLinhas && cabecalhoOk;
  btnsSalvar.forEach(btn => {
    btn.disabled = false; // Garante que o clique sempre dispara
    btn.classList.toggle('visual-disabled', !podeSalvar);
  });
  if (btnRemover) btnRemover.disabled = !algumaMarcada;
}
function limparFormularioCabecalho() {
  clearFullSnapshot();
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
  const mk = document.getElementById('markup_global');
  if (mk) mk.value = '';

  const pill = document.getElementById('pill-taxa');
  if (pill) pill.textContent = '—';

  // Recalcula estado/habilitação
  if (typeof recalcTudo === 'function') recalcTudo();
  if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
}

function limparGradeProdutos() {
  try { sessionStorage.removeItem('criacao_tabela_preco_produtos'); } catch (e) { }

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
      const mem = sessionStorage.getItem('TP_LAST_VIEW_ID');
      const ctx = sessionStorage.getItem('TP_CTX_ID');
      const cand = idUrl || (mem && mem !== 'new' ? mem : null) || (ctx && ctx !== 'new' ? ctx : null);
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
          document.getElementById('nome_tabela').value = t.nome_tabela || '';
          document.getElementById('cliente_nome').value = t.cliente_nome || t.cliente || '';
          document.getElementById('codigo_cliente').value = t.codigo_cliente || '';
          document.getElementById('ramo_juridico').value = t.ramo_juridico || '';

          // RESTORE GLOBAL FIELDS
          const first = (Array.isArray(t.produtos) && t.produtos.length) ? t.produtos[0] : null;

          const freteInput = document.getElementById('frete_kg');
          if (freteInput) freteInput.value = String(first?.frete_kg ?? 0);

          // Markup Global (inferir do primeiro item ou usar o que estava salvo se tiver campo na tabela)
          const mkInput = document.getElementById('markup_global');
          if (mkInput) {
            const mkVal = first?.markup ?? 0;
            mkInput.value = Number(mkVal).toFixed(2);
          }

          // Condição Pagamento
          // Condição Pagamento
          await carregarCondicoes();
          const planoSel = document.getElementById('plano_pagamento');
          if (planoSel) {
            const planoVal = t.codigo_plano_pagamento ?? first?.codigo_plano_pagamento ?? '';
            if (planoVal) {
              const opt = Array.from(planoSel.options).find(o => (o.textContent || '').trim() === String(planoVal).trim() || o.value === String(planoVal));
              if (opt) planoSel.value = opt.value;
            } else {
              planoSel.value = '';
            }
            atualizarPillTaxa?.();
          }

          // Fator Global
          await carregarDescontos();
          // Lógica de inferência do fator global igual ao carregarItens
          const dg = document.getElementById('desconto_global');
          if (dg) {
            const fatores = (t.produtos || []).map(x => {
              const c = x.descricao_fator_comissao || '';
              const code = c.split(' - ')[0].trim();
              return code;
            }).filter(Boolean);

            // Se todos forem iguais
            if (fatores.length > 0 && fatores.every(f => f === fatores[0])) {
              dg.value = fatores[0];
            } else {
              dg.value = '';
            }
            atualizarPillDesconto?.();
          }


          // repõe itens e re-renderiza grade
          itens = Array.isArray(t.produtos) ? t.produtos.map(p => mapBackendItemToFrontend(p, t)) : [];
          if (typeof renderTabela === 'function') renderTabela();
          if (typeof recalcTudo === 'function') recalcTudo().catch(() => { });

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
      const last = sessionStorage.getItem('TP_LAST_VIEW_ID');
      const url = getIdFromUrl();
      const ctx = sessionStorage.getItem('TP_CTX_ID');
      const cand = sourceTabelaId || (srcMem && srcMem !== 'new' ? srcMem : null)
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
    sourceTabelaId = null;


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
      else if (n >= 0) { elDias.value = `Faltam ${n} dia${n === 1 ? '' : 's'}`; elDias.dataset.status = n <= 7 ? 'alerta' : 'ok'; }
      else { const k = Math.abs(n); elDias.value = `Expirada há ${k} dia${k === 1 ? '' : 's'}`; elDias.dataset.status = 'expirada'; }
    }
  } catch (e) {
    console.error('validade_global:', e);
  }
}

// Carrega itens: da memória (prioridade) ou do backend
async function carregarItens() {
  const ctx = getCtxId();

  // 1) Tenta recuperar da memória local (TP_ATUAL)
  // Isso garante que, ao voltar do "Adicionar Produto", não perderemos o que já estava na tela.
  const memoria = sessionStorage.getItem(`TP_ATUAL:${ctx}`);
  if (memoria) {
    try {
      const saved = JSON.parse(memoria);
      if (Array.isArray(saved) && saved.length > 0) {
        console.log("carregarItens: Usando memória local (TP_ATUAL)", saved.length, "itens.");
        itens = saved;
        renderTabela();
        return;
      }
    } catch (e) { console.warn("Erro ao ler TP_ATUAL", e); }
  }

  // 2) Se não tiver memória, busca do banco (Apenas se tiver ID e não for DUP "limpo")
  if (!currentTabelaId) {
    itens = [];
    renderTabela();
    return;
  }

  try {
    const r = await fetch(`${API_BASE}/tabela_preco/${currentTabelaId}`, { cache: 'no-store' });
    if (!r.ok) {
      if (r.status === 404) {
        console.warn("Tabela não encontrada no banco (404). Iniciando vazia.");
        itens = [];
        renderTabela();
        return;
      }
      throw new Error(`Erro ${r.status}`);
    }
    const t = await r.json();

    // --- RESTORE HEADER FIELDS ---
    // Recupera os dados do cabeçalho que vieram do backend
    const nomeEl = document.getElementById('nome_tabela');
    const cliEl = document.getElementById('cliente_nome');
    const codEl = document.getElementById('codigo_cliente');
    const ramoEl = document.getElementById('ramo_juridico');
    const freteEl = document.getElementById('frete_kg');
    const validadeEl = document.getElementById('validade_tabela');
    const diasEl = document.getElementById('dias_restantes');

    if (nomeEl) nomeEl.value = t.nome_tabela || '';
    if (cliEl) cliEl.value = t.cliente_nome || t.cliente || '';
    if (codEl) codEl.value = t.codigo_cliente || '';
    if (ramoEl) ramoEl.value = t.ramo_juridico || '';

    // Frete: se tiver no header da resposta ou inferir do primeiro item?
    // Geralmente vem nos itens, mas se tiver 'frete_kg' no T, usa.
    // Se não, tenta pegar do primeiro item.
    if (freteEl) {
      if (t.frete_kg != null) freteEl.value = Number(t.frete_kg);
      else if (t.produtos && t.produtos.length > 0) freteEl.value = Number(t.produtos[0].frete_kg || 0);
    }

    // Configurações globais (IVA, Markup) se disponíveis no objeto T
    const ivaChk = document.getElementById('iva_st_toggle');
    if (ivaChk) {
      ivaChk.checked = !!(t.calcula_st ?? t.iva_st ?? false);
      window.ivaStAtivo = ivaChk.checked;
      // Se é edição, geralmente o IVA vem travado conforme cadastro do cliente?
      // Vamos manter a lógica de 'enforceIvaLockByCliente' depois se necessário.
    }

    // Map backend -> frontend
    itens = (t.produtos || []).map(p => mapBackendItemToFrontend(p, t));

    // Se for modo DUP, talvez queiramos reprocessar IDs?
    // mapBackendItemToFrontend já lida bem.

    renderTabela();

    // Atualiza UI baseada no cabeçalho carregado
    if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
    if (typeof enforceIvaLockByCliente === 'function') enforceIvaLockByCliente();

  } catch (err) {
    console.error("Falha ao carregar itens do backend:", err);
    showOsModal({ title: 'Aviso', message: "Não foi possível carregar os itens da tabela. Verifique a conexão.", type: 'alert' });
  }
}

// === Bootstrap ===
document.addEventListener('DOMContentLoaded', () => {
  // Config Mobile
  if (typeof setupMobileToolbar === 'function') setupMobileToolbar();

  // Eventos globais
  setMode(MODE.NEW);
  document.getElementById('btn-listar')?.addEventListener('click', () => { goToListarTabelas(); });

  // Disparar validação do botão salvar ao digitar nos campos obrigatórios
  ['nome_tabela', 'cliente_nome'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', () => {
      if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
    });
  });

  // Atalho ENTER para aplicar a todos
  document.getElementById('plano_pagamento')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      document.getElementById('btn-aplicar-condicao-todos')?.click();
    }
  });
  document.getElementById('desconto_global')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      document.getElementById('btn-aplicar-todos')?.click();
    }
  });
  document.getElementById('markup_global')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      document.getElementById('btn-aplicar-markup-todos')?.click();
    }
  });

  document.getElementById('btn-aplicar-todos')?.addEventListener('click', aplicarFatorGlobal);

  document.getElementById('plano_pagamento')?.addEventListener('change', (e) => {
    e.currentTarget.dataset.userEdited = '1';
    atualizarPillTaxa();
    document.getElementById('btn-aplicar-condicao-todos')?.click();
    refreshToolbarEnablement(); saveHeaderSnapshot();
  });
  document.getElementById('frete_kg')?.addEventListener('input', () => {
    recalcTudo();
    refreshToolbarEnablement();
  });

  // Limpar "0" ao focar e restaurar ao sair
  const freteInput = document.getElementById('frete_kg');
  if (freteInput) {
    freteInput.addEventListener('focus', function () {
      if (this.value === '0' || Number(this.value) === 0) {
        this.value = '';
      }
    });
    freteInput.addEventListener('blur', function () {
      if (this.value.trim() === '') {
        this.value = '0';
        recalcTudo();
        refreshToolbarEnablement();
      }
    });
  }

  document.getElementById('tbody-itens')?.addEventListener('change', (e) => {
    if (e.target && e.target.classList.contains('chk-linha')) {
      if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
      const all = document.querySelectorAll('#tbody-itens .chk-linha');
      const marked = document.querySelectorAll('#tbody-itens .chk-linha:checked');
      const chkAll = document.getElementById('chk-all');
      if (chkAll) chkAll.checked = (all.length > 0 && marked.length === all.length);
    }
  });

  atualizarValidadeCabecalhoGlobal();

  (function bindChkAll() {
    const chkAll = document.getElementById('chk-all');
    if (!chkAll) return;
    const toggleAll = (e) => {
      const checked = (e && e.currentTarget) ? !!e.currentTarget.checked : !!chkAll.checked;
      document.querySelectorAll('#tbody-itens .chk-linha').forEach(cb => { cb.checked = checked; });
      if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
    };
    chkAll.addEventListener('click', toggleAll);
    chkAll.addEventListener('change', toggleAll);
  })();

  document.getElementById('btn-buscar')?.addEventListener('click', () => {
    saveHeaderSnapshot();
    preparePickerBridgeBeforeNavigate();
    snapshotSelecionadosParaPicker();
    window.location.href = 'tabela_preco.html';
  });

  document.getElementById('btn-remover-selecionados')?.addEventListener('click', () => {
    removerSelecionados();
    refreshToolbarEnablement();
    snapshotSelecionadosParaPicker();
  });

  // ===================================
  // CUSTOM OS MODALS
  // ===================================


  // handler único (sem aninhar addEventListener dentro de outro)
  (() => {
    const btnsSalvar = [
      document.getElementById('btn-salvar'),
      document.getElementById('btn-mobile-save')
    ].filter(Boolean);

    if (btnsSalvar.length === 0) return;

    let saving = false;

    btnsSalvar.forEach(btn => {
      btn.type = 'button';
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (saving) return;
        saving = true;

        // Desabilita todos os botões de salvar
        btnsSalvar.forEach(b => b.disabled = true);

        try {
          const resp = await salvarTabela(); // agora retorna JSON
          if (!resp) return;
          const qtd = resp?.itens_inseridos ?? resp?.qtd_produtos ?? itens.length;

          await showOsModal({
            title: 'ordersync-y7kg.onrender.com diz',
            message: `Tabela salva! ${qtd} produtos incluídos.`,
            type: 'alert'
          });

          // pegue o ID
          const tabelaId = resp?.tabela_id || resp?.id_tabela || resp?.id || window.currentTabelaId;
          if (!tabelaId) {
            await showOsModal({ title: 'Aviso', message: "Tabela salva, mas o ID não veio no retorno do backend. Ajuste o /tabela_preco/salvar para devolver o id.", type: 'alert' });
            return;
          }

          // Sucesso absoluto: limpa snapshot para não voltar sujeira se recarregar
          clearFullSnapshot();

          // pergunta de decisão
          const querEnviar = await showOsModal({
            title: 'ordersync-y7kg.onrender.com diz',
            message: `Deseja mandar o link do orçamento?`,
            type: 'confirm'
          });

          // CAPTURA ESTADO ANTES DO RESET
          const freteKgParaModal = Number(document.getElementById('frete_kg')?.value || 0);

          // RESET COMPLETO (VOLTAR A TELA ZERADA)
          currentTabelaId = '';
          sourceTabelaId = '';
          window.currentTabelaId = '';
          window.sourceTabelaId = '';

          try { history.replaceState(null, '', location.pathname); } catch { }

          // limpa cabeçalho + grade e volta pro modo original (inputs habilitados)
          if (typeof limparFormularioCabecalho === 'function') limparFormularioCabecalho();
          if (typeof limparGradeProdutos === 'function') limparGradeProdutos();

          if (typeof setMode === 'function') setMode(MODE.NEW);
          if (typeof setFormDisabled === 'function') setFormDisabled(false);
          if (typeof toggleToolbarByMode === 'function') toggleToolbarByMode();
          if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();

          if (querEnviar) {
            if (typeof window.__showGerarLinkModal === "function") {
              window.__showGerarLinkModal({
                tabelaId,
                freteKg: freteKgParaModal, // Passa o frete capturado
                pedidoClientePath: "/tabela_preco/pedido_cliente.html",
              });
            } else {
              await showOsModal({ title: 'Erro', message: "Módulo de gerar link não carregado (../js/gerar_link_pedido.js).", type: 'alert' });
            }
          }

          // Se NÃO quiser enviar, já está resetado.

        } catch (err) {
          // mostra 422 legível, se vier no formato FastAPI
          const msg = (err && err.message) ? err.message : 'Erro ao salvar a tabela.';
          await showOsModal({ title: 'Erro', message: msg, type: 'alert' });
          console.error(err);
        } finally {
          saving = false;
          btnsSalvar.forEach(b => b.disabled = false);
          toggleToolbarByMode?.();
          refreshToolbarEnablement?.();
        }
      });
    });
  })();

  document.getElementById('btn-cancelar')?.addEventListener('click', onCancelar);
  document.getElementById('btn-editar')?.addEventListener('click', onEditar);
  document.getElementById('btn-duplicar')?.addEventListener('click', onDuplicar);

  // Init
  (async function init() {
    setupClienteAutocomplete(); // ✅ Fix: Initialize autocomplete
    await Promise.all([carregarCondicoes(), carregarDescontos()]);

    // 1. Garante ID a partir da URL (Essencial para EDIT/VIEW)
    const idUrl = new URLSearchParams(location.search).get('id');
    if (idUrl) {
      setTabelaIds(idUrl);
    } else {
      // Se não veio na URL, verifica se estamos voltando de uma operação (Picker)
      // Recupera o contexto salvo
      const pendingCtx = sessionStorage.getItem('TP_CTX_ID');
      if (pendingCtx && pendingCtx !== 'new') {
        // Só restaura o ID se tivermos um 'Modo de Retorno' setado,
        // indicando que saímos intencionalmente desta tela e estamos voltando.
        const retMode = sessionStorage.getItem(`TP_RETURN_MODE:${pendingCtx}`);
        if (retMode) {
          console.log("Restaurando contexto pendente (voltou do picker):", pendingCtx);
          setTabelaIds(pendingCtx);
        }
      }
    }

    // 2. Verifica se estamos "Voltando" do Picker (agora com ID correto setado se aplicável)
    const ctx = getCtxId();
    const returnMode = sessionStorage.getItem(`TP_RETURN_MODE:${ctx}`);

    // Se NÃO estivermos voltando do picker (e não for Reload), é uma entrada fresca (ex: vindo da lista)
    // Então limpamos qualquer memória "curta" antiga para não carregar lixo.
    // Isso atende ao pedido: "não carregue cache desnecessário".
    if (!returnMode && !__IS_RELOAD) {
      console.log("Entrada fresca. Limpando cache de sessão para:", ctx);
      sessionStorage.removeItem(`TP_ATUAL:${ctx}`);
      sessionStorage.removeItem(`TP_BUFFER:${ctx}`);
      // Se for contexto 'new', limpa snapshots também para garantir limpeza
      if (ctx === 'new') {
        sessionStorage.removeItem(`TP_HEADER_SNAPSHOT:${ctx}`);
      }
    }

    const temIdNaUrl = !!idUrl;

    // 🔒 Se tem id na URL (edição/visualização), NÃO limpe/restaure snapshot agora
    // EXCETO se estivermos VOLTANDO do picker (returnMode existe) -> aí queremos restaurar o estado visual anterior
    if (!temIdNaUrl || returnMode) {
      if (__IS_RELOAD) {
        // Se for reload, talvez não devêssemos limpar se tiver returnMode? 
        // Por segurança, se for reload real, limpa. Mas se for navegação, restaura.
        // O __IS_RELOAD detecta F5. Se for F5, ok limpar.
        if (!__IS_RELOAD) restoreHeaderSnapshotIfNew(true);
      } else {
        restoreHeaderSnapshotIfNew(true);
      }
    }

    // Se tem id, NÃO limpa cabeçalho antes de carregar
    if (!temIdNaUrl) {
      if (__IS_RELOAD) {
        limparFormularioCabecalho?.();
      } else {
        restoreHeaderSnapshotIfNew?.();
      }
    }

    await carregarItens();                       // carrega itens salvos/edição
    const q = new URLSearchParams(location.search);
    const action = q.get('action') || q.get('mode') || q.get('modo');
    let modeRestored = false;
    if (!action) {
      const ctx = sessionStorage.getItem('TP_CTX_ID') || getCtxId();
      const ret = sessionStorage.getItem(`TP_RETURN_MODE:${ctx}`);
      if (ret) {
        if (ret === MODE.EDIT) setMode(MODE.EDIT);
        else if (ret === MODE.DUP) setMode(MODE.DUP);
        else if (ret === MODE.NEW) setMode(MODE.NEW);
        sessionStorage.removeItem(`TP_RETURN_MODE:${ctx}`);
        modeRestored = true;
      }
    }
    if (!modeRestored) {
      if (currentTabelaId) {
        if (action === 'edit') setMode(MODE.EDIT);
        else if (action === 'duplicate') onDuplicar();
        else setMode(MODE.VIEW);
      } else {
        setMode(MODE.NEW);
      }
    }

    // ✅ agora sim, com o modo correto, mescla o buffer do picker
    if (!__IS_RELOAD) await mergeBufferFromPickerIfAny?.();

    // SE for modo Edição ou Duplicação, atualiza preços com o cadastro atual
    // (mas não bloqueia a UI totalmente, deixa rodar)
    if (currentMode === MODE.EDIT || currentMode === MODE.DUP) {
      // Dispara atualização de preços E recálculo em background
      // O usuário já vê a tabela com valores antigos/salvos imediatamente
      atualizarPrecosAtuais()
        .then(() => recalcTudo())
        .catch(err => console.error("Erro ao atualizar preços/recalcular em background:", err));
    } else {
      // Se for View ou New (sem buffer), roda um recalcTudo "fire-and-forget" 
      // para garantir totais visuais, mas renderTabela já deve ter mostrado algo.
      Promise.resolve(recalcTudo()).catch(() => { });
    }

    refreshToolbarEnablement();
  })();
});


document.getElementById('btn-aplicar-condicao-todos')?.addEventListener('click', () => {
  const cod = document.getElementById('plano_pagamento')?.value || '';
  document.querySelectorAll('#tbody-itens tr').forEach(tr => {
    const sel = tr.querySelector('td:nth-child(10) select');
    if (!sel) return;
    sel.value = cod;
    // 🔑 garante persistência em itens[idx] + recálculo
    console.log(`Aplicando Condição Global: ${cod} na linha com select`, sel);
    sel.dispatchEvent(new Event('change', { bubbles: true }));
  });
  setTimeout(() => {
    Promise.resolve(recalcTudo()).catch(() => { });
  }, 0);
  const hdr = document.getElementById('plano_pagamento');
  if (hdr) hdr.dataset.userEdited = '';
  snapshotSelecionadosParaPicker?.();
});

document.getElementById('btn-aplicar-markup-todos')?.addEventListener('click', () => {
  const mkInput = document.getElementById('markup_global');
  // replace comma with dot for parsing
  let raw = mkInput?.value || '';
  raw = raw.replace(',', '.');

  // Se estiver vazio, assumir 0? O usuário disse "se colocar 0".
  // Mas se parseFloat falhar em string vazia, retorna NaN.
  if (raw.trim() === '') {
    // Opção: ou alerta ou considera 0. Vamos manter alerta se vazio, 
    // mas garantir que '0' passe.
  }

  const val = parseFloat(raw);

  if (isNaN(val)) {
    showOsModal({ title: 'Aviso', message: 'Informe um valor de Markup válido.', type: 'alert' });
    return;
  }

  // Format consistent to 2 decimal places for input value
  if (mkInput) mkInput.value = val.toFixed(2);

  document.querySelectorAll('#tbody-itens tr').forEach(tr => {
    const inp = tr.querySelector('.field-markup');
    if (inp) {
      // Set value and trigger change to calc
      inp.value = val.toFixed(2);
      inp.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });



  // Save snapshot of header field
  saveHeaderSnapshot();
});

document.getElementById('markup_global')?.addEventListener('change', () => {
  // Auto-apply immediately on change/blur
  document.getElementById('btn-aplicar-markup-todos')?.click();
  saveHeaderSnapshot();
});

document.getElementById('iva_st_toggle')?.addEventListener('change', (e) => {
  ivaStAtivo = !!e.target.checked;
  Promise.resolve(recalcTudo()).catch(err => console.debug('recalcTudo falhou:', err));
});

document.getElementById('desconto_global')?.addEventListener('change', (e) => {
  // 👇 marca que o usuário editou manualmente o header
  e.currentTarget.dataset.userEdited = '1';
  atualizarPillDesconto();
  // Auto-apply immediately on change
  document.getElementById('btn-aplicar-todos')?.click();
  saveHeaderSnapshot();
});

window.addEventListener('pageshow', () => {
  if (typeof recalcTudo === 'function') {
    queueMicrotask(() => Promise.resolve(recalcTudo()).catch(() => { }));
  }
});

document.addEventListener('input', handleFieldChange, true);
document.addEventListener('change', handleFieldChange, true);

// =========================================================
// CORREÇÃO DE AUTENTICAÇÃO (401)
// Reescrevendo/definindo explicitamente a função de salvar
// para garantir o envio do token.
// =========================================================
// =========================================================
// FUNÇÃO DE SALVAR UNIFICADA (CRIAÇÃO E EDIÇÃO)
// =========================================================
async function salvarTabelaPreco(payload) {
  const token = localStorage.getItem("ordersync_token");

  // A lógica de "Edição" depende se temos um ID de tabela carregado E se o modo é compatível (não DUP/NEW)
  // Mas se tivermos ID e o usuário clicou em salvar, assumimos que é update daquele ID,
  // exceto se mode for DUP (nesse caso ID é null).
  const idParaSalvar = (currentMode !== MODE.DUP && currentMode !== MODE.NEW) ? currentTabelaId : null;
  // Fallback: se window.currentTabelaId existir e não for DUP, usa ele.
  // (Pode ocorrer se o modo visual não atualizou, mas temos ID no contexto)
  const finalId = idParaSalvar || ((currentMode !== MODE.DUP && currentMode !== MODE.NEW) ? window.currentTabelaId : null);

  let url, method;

  if (finalId) {
    // UPDATE
    url = `${API_BASE}/tabela_preco/${finalId}`;
    method = "PUT";
    console.log("Salvando tabela (UPDATE):", finalId);
  } else {
    // CREATE
    url = `${API_BASE}/tabela_preco/salvar`;
    method = "POST";
    console.log("Salvando tabela (CREATE)");
  }

  const r = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });

  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    if (r.status === 401) throw new Error("Tempo expirado: faça o login");
    // Tenta parsear erro estruturado
    try {
      const j = JSON.parse(txt);
      if (j.detail) throw new Error(typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail));
    } catch (e) { /* ignora erro de parse */ }
    throw new Error(`Falha ao salvar (${r.status}). ${txt}`);
  }

  return await r.json();
}

function handleFieldChange(e) {
  const el = e.target;
  if (!el || !(el instanceof HTMLElement)) return;

  // Se o campo estava marcado com erro, limpamos
  if (el.classList.contains('field-error')) {
    el.classList.remove('field-error');
    const msg = el.nextElementSibling;
  }
}

// =========================================
// MOBILE LOGIC RESTORATION
// =========================================

function toggleHeader() {
  const content = document.getElementById('header-content');
  const header = document.getElementById('toggle-header');
  if (!content) return;
  content.classList.toggle('expanded');
}

function setupMobileToolbar() {
  // Bind Toolbar Buttons
  document.getElementById('btn-mobile-list')?.addEventListener('click', () => goToListarTabelas());

  document.getElementById('btn-mobile-cancel')?.addEventListener('click', (e) => {
    onCancelar(e);
    // Force mobile refresh
    setTimeout(renderMobileCards, 50);
  });

  document.getElementById('btn-mobile-edit')?.addEventListener('click', () => {
    onEditar();
    setTimeout(renderMobileCards, 50);
  });

  document.getElementById('btn-mobile-dup')?.addEventListener('click', () => {
    onDuplicar();
    setTimeout(renderMobileCards, 50);
  });

  document.getElementById('btn-mobile-save')?.addEventListener('click', () => salvarTabela());

  // Add/Initial Add - Focus on search or open modal if needed
  const focusSearch = () => {
    // Scroll to top or search
    window.scrollTo({ top: 0, behavior: 'smooth' });
    const btn = document.getElementById('btn-buscar');
    if (btn && !btn.classList.contains('hidden')) btn.click();
  };
  document.getElementById('btn-mobile-add')?.addEventListener('click', focusSearch);
  document.getElementById('btn-mobile-add-initial')?.addEventListener('click', focusSearch);
}

function renderMobileCards() {
  const container = document.getElementById('mobile-card-container');
  if (!container) return;

  // Preservar estado de expansão (quais cards estão abertos) antes de os recriar
  const expandedSet = new Set();
  container.querySelectorAll('.mobile-card').forEach(card => {
    const content = card.querySelector('.header-content');
    if (content && content.classList.contains('expanded')) {
      expandedSet.add(card.dataset.idx);
    }
  });

  // Sync toolbar totals
  const totalItens = (itens || []).length;
  const totalValor = itens.reduce((acc, it) => acc + (it._totalComercial || 0), 0);

  const elItens = document.getElementById('mobile-total-itens');
  if (elItens) elItens.textContent = `${totalItens} item(s)`;

  const elValor = document.getElementById('mobile-total-valor');
  if (elValor) elValor.textContent = fmtMoney(totalValor);

  // If empty
  if (itens.length === 0) {
    container.innerHTML = `
        <div class="empty-state-mobile">
          <p>Nenhum produto selecionado.</p>
          <button id="btn-mobile-add-initial-2" class="btn btn-primary btn-sm">Adicionar Produtos</button>
        </div>`;
    document.getElementById('btn-mobile-add-initial-2')?.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      const btn = document.getElementById('btn-buscar');
      if (btn) btn.click();
    });
    return;
  }

  // Check if editing is allowed
  const isEditable = (currentMode === MODE.NEW || currentMode === MODE.EDIT || currentMode === MODE.DUP);
  const markupDisabled = !isEditable;

  // Render List
  container.innerHTML = '';
  itens.forEach((item, idx) => {
    const card = document.createElement('div');
    card.className = 'mobile-card';
    card.dataset.idx = idx;

    // Basic Data
    const desc = item.descricao || 'Produto sem nome';
    const codigo = item.codigo_tabela || '';
    const emb = item.embalagem || '';
    const total = item._totalComercial || 0; // Valor Final (R$)
    const isInactive = item.status_atual === 'INATIVO';
    const statusBadge = isInactive ? '<span class="badge-inactive">INATIVO</span>' : '';

    // Calculation Fields
    const valorUnit = item.valor || 0;
    const fator = item._fatorApplied || 0; // Need to ensure this is saved/avail
    // Fallback if _fatorApplied not set: assume from global/item logic
    // Actually, let's use what we have. 
    // Markup
    const markupVal = item.markup || 0;

    // Frete
    const freteVal = item._freteValor || 0;
    const semFrete = item.total_sem_frete || 0;

    // Card Content
    // Select Options Generators
    const genFatorOptions = (selectedVal) => {
      let opts = `<option value="">—</option>`;
      if (mapaDescontos) {
        // FORCE SAME LOGIC
        let targetCode = determineFatorCode(item);

        Object.entries(mapaDescontos).forEach(([cod, frac]) => {
          const isSel = String(cod) === targetCode;
          opts += `<option value="${cod}" ${isSel ? 'selected' : ''}>${cod} - ${(Number(frac) * 100).toFixed(2)}</option>`;
        });
      }
      return opts;
    };

    const genCondOptions = (selectedVal) => {
      let opts = `<option value="">—</option>`;
      const selHdr = document.getElementById('plano_pagamento');
      if (selHdr) {
        // FORCE SAME LOGIC
        let targetCode = determineCondicaoCode(item);

        Array.from(selHdr.options).forEach(o => {
          if (o.value) {
            let isSel = (String(o.value) === targetCode);
            opts += `<option value="${o.value}" ${isSel ? 'selected' : ''}>${o.textContent}</option>`;
          }
        });
      }
      return opts;
    };

    // Card Content
    card.innerHTML = `
      <div class="mobile-card-item">
        <!-- Header: Code/Desc (Left) vs Totals (Right) -->
        <div class="mobile-card-header clickable-header">
           <div class="d-flex justify-content-between align-items-start w-100">
              <!-- Left: Code & Desc -->
              <div style="flex: 1; padding-right: 8px;">
                  <div class="fw-bold text-dark" style="font-size: 0.95rem;">${item.codigo_tabela} - ${item.descricao}</div>
                  <div class="text-muted" style="font-size: 0.8rem;">${item.embalagem || ''}</div>
              </div>

              <!-- Right: Totals Stacked -->
              <div class="d-flex flex-column align-items-end" style="min-width: 100px;">
                  <div style="font-size: 0.75rem; color: #666; margin-bottom: -2px;">Total c/ Frete</div>
                  <div style="font-size: 1rem; font-weight: 700; color: #16a34a;">${fmtMoney(total)}</div>
                  
                  <div style="font-size: 0.75rem; color: #999; margin-top: 4px; margin-bottom: -2px;">Total s/ Frete</div>
                  <div style="font-size: 0.9rem; font-weight: 600; color: #333;">${fmtMoney(semFrete)}</div>
              </div>
              
               <!-- Chevron -->
               <span class="chevron-header" style="margin-left: 8px; margin-top: 4px;">▼</span>
           </div>
        </div>

        <div class="header-content ${expandedSet.has(String(idx)) ? 'expanded' : 'collapsed'}">
         <div style="padding-top: 12px;">
            <!-- Row 1: Vlr Unit | Markup % -->
            <div class="mobile-grid-2col" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="card-field">
                    <label>Valor Unit.</label>
                    <input type="text" value="${fmtMoney(item.valor)}" disabled style="background: #f8fafc;">
                </div>
                <div class="card-field">
                    <label>Markup %</label>
                    <input type="number" class="mobile-input-markup" value="${item.markup || 0}" step="0.01" ${markupDisabled ? 'disabled' : ''}>
                </div>
            </div>

            <!-- Row 2: Fator % | Condição -->
            <div class="mobile-grid-2col" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="card-field">
                    <label>Fator %</label>
                    ${markupDisabled
        ? (() => {
          const _cod = determineFatorCode(item) || item.__fator_codigo || '';
          const _frac = (_cod && mapaDescontos[_cod] != null) ? mapaDescontos[_cod] : null;
          const _label = _frac != null ? `${_cod} - ${(Number(_frac) * 100).toFixed(2)}` : (_cod || '');
          return `<input type="text" value="${_label}" disabled>`;
        })()
        : `<select class="form-select mobile-fator-select">${genFatorOptions(item.__fator_codigo)}</select>`
      }
                </div>
                <div class="card-field">
                    <label>Condição (R$)</label> <!-- Label per user request, but functionality is select -->
                    ${markupDisabled
        ? `<input type="text" value="${item.plano_pagamento || ''}" disabled style="background:#f9f9f9; color:#666">`
        : `<select class="form-select mobile-cond-select">${genCondOptions(item.plano_pagamento_cod || item.plano_pagamento)}</select>`
      }
                </div>
            </div>

            <!-- Row 3: Frete (Full width) -->
            <div class="card-field" style="margin-bottom: 16px;">
                 <label>Frete (R$)</label>
                 <input type="text" value="${fmtMoney(freteVal)}" disabled style="background: #f8fafc;">
            </div>

            <!-- Row 4: Fiscal Details (Styled Block) -->
            <div class="fiscal-block" style="background: #f8fafc; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                 <div style="font-size: 0.85rem; font-weight: 600; color: #333; margin-bottom: 8px;">Detalhes Fiscais</div>
                 <div class="d-flex justify-content-between text-center" style="font-size: 0.8rem;">
                     <div>
                        <div class="text-muted" style="font-size: 0.7rem;">IPI</div>
                        <div class="fw-bold">${fmtMoney(item.ipi || 0)}</div>
                     </div>
                     <div>
                        <div class="text-muted" style="font-size: 0.7rem;">ICMS ST</div>
                        <div class="fw-bold">${fmtMoney(item._icmsProprio || 0)}</div> 
                     </div>
                     <div>
                        <div class="text-muted" style="font-size: 0.7rem;">IVA_ST</div>
                        <div class="fw-bold">${fmtMoney(item._stReter || 0)}</div>
                     </div>
                 </div>
            </div>

            <!-- Card Actions -->
            <div class="card-actions" style="border-top: none; padding-top: 0;">
                <button class="btn-card-action btn-card-remove" ${markupDisabled ? 'disabled style="opacity:0.5"' : ''} style="color: #ef4444; font-size: 0.9rem;">Remover item</button>
            </div>
         </div>
      </div>
    </div>
    `;

    // Events

    // Toggle Expand
    const header = card.querySelector('.clickable-header');
    header.addEventListener('click', () => {
      const content = card.querySelector('.header-content');
      content.classList.toggle('expanded');
      // Rotate chevron
      const chev = header.querySelector('.chevron-header');
      if (chev) chev.style.transform = content.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
    });

    // Remove
    const btnRem = card.querySelector('.btn-card-remove');
    if (!markupDisabled) {
      btnRem.addEventListener('click', (e) => {
        e.stopPropagation();
        itens.splice(idx, 1);
        renderTabela();
        snapshotSelecionadosParaPicker();
        refreshToolbarEnablement();
      });
    }

    // Markup Change
    const mkInput = card.querySelector('.mobile-input-markup');
    if (!markupDisabled) {
      mkInput.addEventListener('change', (e) => {
        e.stopPropagation();
        const val = parseFloat(e.target.value);
        if (!isNaN(val)) {
          item.markup = val;
          // Force global recalc to update all fields
          renderTabela();
          recalcTudo();
        }
      });
      mkInput.addEventListener('click', (e) => e.stopPropagation());
    }

    // Event: Fator Change
    const selFator = card.querySelector('.mobile-fator-select');
    if (selFator) {
      selFator.addEventListener('change', (e) => {
        e.stopPropagation();
        const code = e.target.value;
        const frac = (window.mapaDescontos && window.mapaDescontos[code] != null) ? Number(window.mapaDescontos[code]) : 0;
        item.fator_comissao = frac;
        item.__fator_codigo = code;
        item.__overridePercent = true;
        // Trigger update
        recalcTudo(); // This will re-render table and thus re-render mobile cards
      });
      selFator.addEventListener('click', (e) => e.stopPropagation());
    }

    // Event: Condição Change
    const selCond = card.querySelector('.mobile-cond-select');
    if (selCond) {
      selCond.addEventListener('change', (e) => {
        e.stopPropagation();
        const val = e.target.value;
        item.plano_pagamento_cod = val;
        // Try to find text
        const opt = e.target.options[e.target.selectedIndex];
        item.plano_pagamento = opt ? opt.textContent : val;
        recalcTudo();
      });
      selCond.addEventListener('click', (e) => e.stopPropagation());
    }

    container.appendChild(card);
  });
}

// Hook into toggleToolbarByMode to sync mobile buttons
const _originalToggleToolbar = toggleToolbarByMode;
toggleToolbarByMode = function () {
  if (typeof _originalToggleToolbar === 'function') _originalToggleToolbar();

  // Mobile logic mirror
  const show = (id, visible) => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('hidden', !visible);
  };

  const hasId = !!currentTabelaId;
  const isView = currentMode === MODE.VIEW;
  const isEditLike = currentMode === MODE.EDIT || currentMode === MODE.DUP || currentMode === MODE.NEW;
  const isEditOrDup = currentMode === MODE.EDIT || currentMode === MODE.DUP;

  show('btn-mobile-list', currentMode === MODE.NEW);
  show('btn-mobile-cancel', isEditOrDup || (isView && hasId));
  show('btn-mobile-edit', isView && hasId);
  show('btn-mobile-dup', isView && hasId);
  show('btn-mobile-save', isEditLike);
  show('btn-mobile-add', isEditLike);
};

// === Header Collapse Logic (Robust) ===
// === Header Collapse Logic (Simplified & Robust) ===
(function setupHeaderCollapse() {
  const attach = () => {
    const btn = document.getElementById('btn-toggle-header');
    const area = document.getElementById('header-collapsible-area');
    const summary = document.getElementById('header-collapsed-summary');
    const lblNome = document.getElementById('summary-nome');
    const lblCli = document.getElementById('summary-cliente');

    if (btn && area) {
      // Use onclick to avoid multiple listeners
      btn.onclick = (e) => {
        e.preventDefault();
        const isCollapsed = area.classList.toggle('collapsed');
        btn.classList.toggle('rotated', isCollapsed);

        // Toggle Summary
        if (summary) {
          if (isCollapsed) {
            const nome = document.getElementById('nome_tabela')?.value || 'Sem Nome';
            const cli = document.getElementById('cliente_nome')?.value || 'Sem Cliente';
            if (lblNome) lblNome.textContent = nome;
            if (lblCli) lblCli.textContent = cli;

            summary.classList.remove('hidden');
            requestAnimationFrame(() => summary.classList.add('visible'));
          } else {
            summary.classList.remove('visible');
            setTimeout(() => summary.classList.add('hidden'), 300);
          }
        }
      };
    } else {
      // Retry if DOM not ready
      setTimeout(attach, 500);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attach);
  } else {
    attach();
  }
})();

