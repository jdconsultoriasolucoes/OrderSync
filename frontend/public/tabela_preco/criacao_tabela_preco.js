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

function calcularLinha(item, fator, taxaCond, freteKg) {
  const valor = Number(item.valor || 0);
  const peso = Number(item.peso_liquido || 0);
  const acrescimoCond = valor * (Number(taxaCond || 0));
  // Frete por regra já usada no projeto: (frete_kg / 1000) * peso_liquido
  const freteValor = (Number(freteKg || 0) / 1000) * peso;
  const descontoValor = valor * Number(fator || 0);
  const valorFinal = valor + acrescimoCond + freteValor - descontoValor;
  return { acrescimoCond, freteValor, descontoValor, valorFinal };
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
  data.forEach(d => { mapaDescontos[d.codigo] = Number(d.percentual) || 0; sel.appendChild(option(`${d.codigo} - ${d.percentual}`, d.codigo)); });
}

function atualizarPillTaxa() {
  const codigo = document.getElementById('plano_pagamento').value;
  const taxa = mapaCondicoes[codigo];
  document.getElementById('pill-taxa').textContent = (taxa || taxa === 0) ? `${fmt4(taxa)}` : '—';
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
      document.getElementById('cliente').value = t.cliente || '';
      document.getElementById('validade_inicio').value = t.validade_inicio || '';
      document.getElementById('validade_fim').value = t.validade_fim || '';
      itens = (t.produtos || []).map(p => ({...p}));
      renderTabela();

      // >>> AQUI: entrar em modo “visualização”
      currentTabelaId = id;
      setMode('view');                // trava tudo e mostra Editar/Duplicar

      return;
    }
  }

  // Modo “novo” (sem id)
  itens = obterItensDaSessao();
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
  const inpFator = document.createElement('input'); Object.assign(inpFator, { type: 'number', step: '0.0001', min: '0', max: '1', value: item.fator_comissao ?? '' });
  inpFator.style.width = '110px'; inpFator.addEventListener('input', () => recalcLinha(tr));
  tdFator.appendChild(inpFator);

  const tdDescOpt = document.createElement('td');
  const selDesc = document.createElement('select');
  selDesc.appendChild(option('—', ''));
  Object.entries(mapaDescontos).forEach(([cod, fator]) => selDesc.appendChild(option(`${cod} - ${fator}`, cod)));
  if (item.desconto && item.valor) {
    const fatorInferido = (Number(item.desconto) / Number(item.valor)).toFixed(4);
    const match = Object.entries(mapaDescontos).find(([, f]) => String(f) === fatorInferido);
    if (match) selDesc.value = match[0];
  }
  selDesc.addEventListener('change', () => {
    const code = selDesc.value; const fator = mapaDescontos[code];
    if (fator !== undefined) { inpFator.value = fator; }
    recalcLinha(tr);
  });
  tdDescOpt.appendChild(selDesc);

  const tdCond = document.createElement('td'); tdCond.className = 'num'; tdCond.textContent = '0,00';
  const tdFrete = document.createElement('td'); tdFrete.className = 'num'; tdFrete.textContent = '0,00';
  const tdDescAplic = document.createElement('td'); tdDescAplic.className = 'num'; tdDescAplic.textContent = '0,00';
  const tdGrupo = document.createElement('td'); tdGrupo.textContent = [item.grupo, item.departamento].filter(Boolean).join(' / ');
  const tdFinal = document.createElement('td'); tdFinal.className = 'num'; tdFinal.textContent = '0,00';

  tr.append(tdSel, tdCod, tdDesc, tdEmb, tdPeso, tdValor, tdFator, tdDescOpt, tdCond, tdFrete, tdDescAplic, tdGrupo, tdFinal);
  return tr;
}

function renderTabela() {
  const tbody = document.getElementById('tbody-itens');
  tbody.innerHTML = '';
  itens.forEach((it, i) => tbody.appendChild(criarLinha(it, i)));
  recalcTudo();
  if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
}

function recalcLinha(tr) {
  const idx = Number(tr.dataset.idx);
  const item = itens[idx]; if (!item) return;

  const fator = Number(tr.querySelector('td:nth-child(7) input')?.value || 0);
  const taxaCond = mapaCondicoes[document.getElementById('plano_pagamento').value] || 0;
  const freteKg = Number(document.getElementById('frete_kg').value || 0);

  const { acrescimoCond, freteValor, descontoValor, valorFinal } = calcularLinha(item, fator, taxaCond, freteKg);
  tr.querySelector('td:nth-child(9)').textContent = fmtMoney(acrescimoCond);
  tr.querySelector('td:nth-child(10)').textContent = fmtMoney(freteValor);
  tr.querySelector('td:nth-child(11)').textContent = fmtMoney(descontoValor);
  tr.querySelector('td:nth-child(13)').textContent = fmtMoney(valorFinal);
}

function recalcTudo() {
  document.querySelectorAll('#tbody-itens tr').forEach(tr => recalcLinha(tr));
}

function aplicarFatorGlobal() {
  const sel = document.getElementById('desconto_global');
  const fatorInput = document.getElementById('fator_global');
  let fator = null;
  if (fatorInput.value) fator = Number(fatorInput.value);
  else if (sel.value && mapaDescontos[sel.value] !== undefined) fator = Number(mapaDescontos[sel.value]);
  if (fator == null || isNaN(fator)) { alert('Informe um fator válido (0–1) ou escolha um desconto.'); return; }
  document.querySelectorAll('#tbody-itens tr').forEach(tr => {
    const inp = tr.querySelector('td:nth-child(7) input');
    if (inp) inp.value = fator;
  });
  recalcTudo();
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

  // reset visual e estado dos botões
  const chkAll = document.getElementById('chk-all');
  if (chkAll) chkAll.checked = false;
  if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();
}

async function salvarTabela() {
  const nome_tabela = document.getElementById('nome_tabela').value.trim();
  const cliente = document.getElementById('cliente').value.trim();
  const validade_inicio = document.getElementById('validade_inicio').value;
  const validade_fim = document.getElementById('validade_fim').value;
  const plano_pagamento = document.getElementById('plano_pagamento').value || null;
  const frete_kg = Number(document.getElementById('frete_kg').value || 0);

  const taxaCond = mapaCondicoes[plano_pagamento] || 0;

  // Mapeia as linhas já renderizadas na tabela para o formato do backend
  const produtos = Array.from(document.querySelectorAll('#tbody-itens tr')).map(tr => {
    const idx = Number(tr.dataset.idx); const item = itens[idx];
    const fator = Number(tr.querySelector('td:nth-child(7) input')?.value || 0);
    const { acrescimoCond, freteValor, descontoValor, valorFinal } =
      calcularLinha(item, fator, taxaCond, frete_kg);

    return {
      nome_tabela, validade_inicio, validade_fim, cliente, fornecedor: item.fornecedor || '',
      codigo_tabela: item.codigo_tabela, descricao: item.descricao, embalagem: item.embalagem,
      peso_liquido: item.peso_liquido || 0, peso_bruto: item.peso_bruto || item.peso_liquido || 0,
      valor: item.valor || 0,
      desconto: Number(descontoValor.toFixed(4)),
      acrescimo: Number((acrescimoCond + freteValor).toFixed(4)),
      fator_comissao: fator || 0, plano_pagamento, frete_kg, frete_percentual: null,
      valor_liquido: Number(valorFinal.toFixed(2)),
      grupo: item.grupo || null, departamento: item.departamento || null
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
  const cliente = document.getElementById('cliente')?.value?.trim();
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
  document.getElementById('cliente').value = '';
  document.getElementById('validade_inicio').value = '';
  document.getElementById('validade_fim').value = '';

  // Parâmetros globais
  const frete = document.getElementById('frete_kg');
  if (frete) frete.value = 0;

  const cond = document.getElementById('plano_pagamento');
  if (cond) cond.value = '';

  const descGlobal = document.getElementById('desconto_global');
  if (descGlobal) descGlobal.value = '';

  const fatorGlobal = document.getElementById('fator_global');
  if (fatorGlobal) fatorGlobal.value = '';

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
          document.getElementById('cliente').value         = t.cliente || '';
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
    // Se você já tem a navegação pronta pro buscador, mantém:
    window.location.href = 'tabela_preco.html';
  });

  document.getElementById('btn-remover-selecionados')?.addEventListener('click', () => {
    removerSelecionados();
    refreshToolbarEnablement();
  });

  document.getElementById('btn-salvar')?.addEventListener('click', async () => {
  try {
    await salvarTabela();

    // Após salvar em NEW ou DUP → volta para NEW travado
    setMode(MODE.NEW);
    setFormDisabled(true); // trava campos
  } catch (e) {
    console.error(e);
    alert(e.message || 'Erro ao salvar a tabela.');
    // NÃO mude de modo; apenas re-sincronize a barra
  } finally {
    toggleToolbarByMode();
    refreshToolbarEnablement();
  }
});
  
  document.getElementById('btn-cancelar')?.addEventListener('click', onCancelar);
  document.getElementById('btn-editar')?.addEventListener('click', onEditar);
  document.getElementById('btn-duplicar')?.addEventListener('click', onDuplicar); 
  
  // Init
  (async function init(){
    await Promise.all([carregarCondicoes(), carregarDescontos()]);
    await carregarItens();
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