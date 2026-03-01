const API_BASE = window.API_BASE || "https://ordersync-backend-edjq.onrender.com"; // Restored & Safe

let currentPage = 1;
let pageSize = 25;
let totalPages = null;
let preSelecionadosCodigos = new Set(); // para pré-marcar checkboxes (enviado pelo pai)

/* ========================
   Bootstrap
======================== */

document.addEventListener("DOMContentLoaded", () => {
  const selGrupo = document.getElementById("grupo");
  const selFornecedor = document.getElementById("filtro-fornecedor");
  // 🛡️ Force "Votorantim" default if available. 
  // O usuário solicitou explicitamente "VOTORANTIM" e retirar o Todos.
  if (selFornecedor) selFornecedor.value = "Votorantim";
  const btnFiltrar = document.getElementById("btn-filtrar");
  const btnLimpar = document.getElementById("btn-limpar");
  const ps = document.getElementById("page_size");
  const inpPalavra = document.getElementById("filtro-palavra");

  // === Contexto com o Pai ===
  function getCtxId() {
    return sessionStorage.getItem('TP_CTX_ID') || 'new';
  }
  function loadPreselectionFromParent() {
    const ctx = getCtxId();
    try {
      const arr = JSON.parse(sessionStorage.getItem(`TP_ATUAL:${ctx}`) || '[]');
      preSelecionadosCodigos = new Set((arr || []).map(p => p.codigo_tabela || p.codigo));
    } catch { preSelecionadosCodigos = new Set(); }
  }
  // (sendBufferBackToParent original removida; usada versão shim abaixo)


  // Filtros
  selGrupo?.addEventListener("change", () => { currentPage = 1; carregarProdutos(); });
  selFornecedor?.addEventListener("change", () => { currentPage = 1; carregarProdutos(); });

  // Botões da toolbar
  btnFiltrar?.addEventListener("click", () => { currentPage = 1; carregarProdutos(); });
  btnLimpar?.addEventListener("click", () => {
    if (selGrupo) selGrupo.value = "";
    if (selFornecedor) {
      // Tenta resetar para Votorantim explicitamente ou recarregar se necessário.
      // Como a lista é estática do DB, basta selecionar.
      selFornecedor.value = "Votorantim";
      // Se não existir na lista (edge case), mantém valor atual ou vazio.
    }
    if (inpPalavra) inpPalavra.value = "";   // limpa a palavra
    // fornecedoresMap.clear(); // não usa mais map local
    currentPage = 1;
    carregarProdutos();
  });

  // Itens por página
  if (ps) {
    pageSize = parseInt(ps.value, 10) || 25;
    ps.addEventListener("change", () => {
      pageSize = parseInt(ps.value, 10) || 25;
      currentPage = 1;
      carregarProdutos();
    });
  }

  // Busca por palavra
  inpPalavra?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      currentPage = 1;
      carregarProdutos();
    }
  });
  inpPalavra?.addEventListener("input", debounce(() => {
    currentPage = 1;
    carregarProdutos();
  }, 300));

  // Botões do rodapé
  document.getElementById("btn-adicionar-selecionados")
    ?.addEventListener("click", enviarSelecionados);
  document.getElementById("btn-cancelar")
    ?.addEventListener("click", () => window.location.href = 'criacao_tabela_preco.html');

  // Toggle do cabeçalho de filtros
  const headerToggle = document.getElementById("header-toggle-filtros");
  const conteudoFiltros = document.getElementById("conteudo-filtros");
  const iconToggle = document.getElementById("icon-toggle-filtros");

  if (headerToggle && conteudoFiltros && iconToggle) {
    headerToggle.addEventListener("click", () => {
      const isHidden = conteudoFiltros.style.display === "none";
      conteudoFiltros.style.display = isHidden ? "block" : "none";
      iconToggle.textContent = isHidden ? "▲" : "▼"; // Usando ▼ para aberto e ▲ para fechado, ou vice versa
    });
  }
});

// === Compat shim: envia seleção de volta ao PAI, sem quebrar legado ===
function sendBufferBackToParent(selecionados) {
  try {
    const arr = Array.isArray(selecionados) ? selecionados : [];

    // --- LEGADO: MERGE na chave 'criacao_tabela_preco_produtos'
    let prev = [];
    try { prev = JSON.parse(sessionStorage.getItem('criacao_tabela_preco_produtos') || '[]'); } catch { }
    const map = new Map((prev || []).map(x => [(x.codigo_tabela ?? x.codigo), x]));
    for (const p of arr) {
      const k = p.codigo_tabela ?? p.codigo;
      map.set(k, { ...(map.get(k) || {}), ...p });
    }
    sessionStorage.setItem('criacao_tabela_preco_produtos', JSON.stringify(Array.from(map.values())));

    // --- CONTEXTO (se houver): MERGE em TP_BUFFER:<ctx> (não atrapalha se o pai não usar)
    const ctx = sessionStorage.getItem('TP_CTX_ID');
    if (ctx) {
      let prevCtx = [];
      try { prevCtx = JSON.parse(sessionStorage.getItem(`TP_BUFFER:${ctx}`) || '[]'); } catch { }
      const mapCtx = new Map((prevCtx || []).map(x => [(x.codigo_tabela ?? x.codigo), x]));
      for (const p of arr) {
        const k = p.codigo_tabela ?? p.codigo;
        mapCtx.set(k, { ...(mapCtx.get(k) || {}), ...p });
      }
      sessionStorage.setItem(`TP_BUFFER:${ctx}`, JSON.stringify(Array.from(mapCtx.values())));
    }
  } catch (e) {
    console.warn('sendBufferBackToParent merge shim falhou:', e);
  }
}

// fora do DOMContentLoaded
const fornecedoresMap = new Map();
// chave = nome normalizado; valor = nome original para exibir
function norm(s) { return String(s || "").trim().toUpperCase(); }

function normText(s) {
  return String(s || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // remove diacríticos
    .toLowerCase()
    .trim();
}

// Verifica se o produto combina com o termo
function matchesTerm(p, termN) {
  if (!termN) return true;
  return [
    p.codigo_tabela,
    p.descricao,
    p.marca,
    p.grupo,
    p.embalagem
  ].some(v => normText(v).includes(termN));
}

// Debounce pra não fazer requisição a cada tecla
function debounce(fn, wait = 300) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(null, args), wait);
  };
}




/* ========================
   Fetch & Render
======================== */
async function carregarGrupos() {
  try {
    const r = await fetch(`${API_BASE}/tabela_preco/filtro_grupo_produto`);
    if (!r.ok) throw new Error("Erro ao buscar grupos");
    const grupos = await r.json();

    const selectGrupo = document.getElementById("grupo");
    selectGrupo.innerHTML = "<option value=''>Todos os grupos</option>";

    grupos.forEach(item => {
      const grupo = item.grupo || "";
      if (!grupo) return;
      const opt = document.createElement("option");
      opt.value = grupo;
      opt.textContent = grupo;
      selectGrupo.appendChild(opt);
    });
  } catch (e) {
    console.error(e);
  }
}

// Função para carregar fornecedores do banco
async function carregarFornecedoresDb() {
  const sel = document.getElementById("filtro-fornecedor");
  if (!sel) return;

  try {
    const r = await fetch(`${API_BASE}/api/fornecedores`); // Rota ajustada
    let lista = [];
    if (r.ok) {
      lista = await r.json();
    } else {
      console.warn("Falha ao carregar fornecedores do banco, status:", r.status);
    }

    sel.innerHTML = "";

    // O backend retorna [{ id, nome_fornecedor }, ...] ou similar
    // Vamos normalizar e ordenar
    const fornecedores = lista
      .map(f => f.nome_fornecedor || f.nome || "")
      .filter(n => n.trim() !== "")
      .sort((a, b) => a.localeCompare(b, 'pt-BR', { sensitivity: 'base' }));

    // Remove duplicados se houver
    const unique = [...new Set(fornecedores)];

    // Popula o select
    for (const f of unique) {
      const o = document.createElement("option");
      o.value = f;
      o.textContent = f;
      sel.appendChild(o);
    }

    // Default Votorantim logic
    const opVotorantim = [...sel.options].find(o => o.value.toUpperCase() === "VOTORANTIM");
    if (opVotorantim) {
      sel.value = opVotorantim.value;
    } else if (sel.options.length > 0) {
      sel.value = sel.options[0].value;
    }

  } catch (e) {
    console.error("Erro ao carregarFornecedoresDb:", e);
  }
}

// Stub para manter compatibilidade se algo chamar (mas não deve ser usado mais)
function coletarFornecedores(lista) {
  // no-op: agora carregamos do banco globalmente
}

function renderFornecedoresDropdown() {
  // no-op: renderização é feita no carregarFornecedoresDb
}

function carregarProdutos(page = currentPage) {
  currentPage = page;

  const grupo = document.getElementById("grupo")?.value || "";
  const fornecedor = document.getElementById("filtro-fornecedor")?.value || "";
  const termo = document.getElementById("filtro-palavra")?.value?.trim() || "";
  const termoN = normText(termo);

  const url = new URL(`${API_BASE}/tabela_preco/produtos_filtro`);
  if (grupo) url.searchParams.append("grupo", grupo);
  if (fornecedor) url.searchParams.append("fornecedor", fornecedor);
  if (termo) url.searchParams.append("q", termo);
  url.searchParams.append("page", currentPage);
  url.searchParams.append("page_size", pageSize);

  fetch(url)
    .then(r => { if (!r.ok) throw new Error("Erro ao buscar produtos"); return r.json(); })
    .then(data => {
      const paginado = !Array.isArray(data) && Array.isArray(data.items);

      let items = [];
      let total = 0;

      if (paginado) {
        // ✅ confiar no backend: sem filtro local
        items = data.items || [];
        total = typeof data.total === "number" ? data.total : (data.items?.length || 0);

        // ainda podemos popular o dropdown de fornecedores com a página atual
        coletarFornecedores(items);
        renderFornecedoresDropdown();
      } else {
        // 🔁 legado: array simples => filtra e pagina no cliente
        let base = Array.isArray(data) ? data : [];
        coletarFornecedores(base);
        renderFornecedoresDropdown();

        if (fornecedor) base = base.filter(p => p.fornecedor === fornecedor);
        if (termoN) base = base.filter(p => matchesTerm(p, termoN));

        const start = (currentPage - 1) * pageSize;
        const end = start + pageSize;
        items = base.slice(start, end);
        total = base.length;
      }

      preencherTabela(items);
      atualizarPaginacaoUI(total);
      if (typeof marcarPreSelecionados === "function") marcarPreSelecionados();
    })
    .catch(e => console.error("Erro em carregarProdutos:", e));
}

function preencherTabela(produtos) {
  const tbody = document.getElementById("tabela-produtos-body");
  tbody.innerHTML = "";

  produtos.forEach(p => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="checkbox" class="produto-checkbox" data-codigo="${p.codigo_tabela}"></td>
      <td>${p.codigo_tabela}</td>
      <td>${p.descricao}</td>
      <td>${p.embalagem ?? ""}</td>
      <td class="num">${(p.peso_liquido ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</td>
      <td class="num">${(p.valor ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</td>
    `;
    // anexa o objeto completo na linha para facilitar coleta
    tr.dataset.produto = JSON.stringify(p);

    // Toggle para mobile
    tr.addEventListener("click", (e) => {
      // Ignorar cliques diretos no checkbox (para não impedir marcação normal no desktop)
      if (e.target.tagName.toLowerCase() === 'input') return;

      // Expande/colapsa o card no mobile
      tr.classList.toggle("expanded");
    });

    tbody.appendChild(tr);
  });
}

function marcarPreSelecionados() {
  if (!preSelecionadosCodigos.size) return;

  document.querySelectorAll("#tabela-produtos-body .produto-checkbox").forEach(chk => {
    const codigo = chk.dataset.codigo;
    if (preSelecionadosCodigos.has(codigo)) {
      // Não marcar de novo: deixa desmarcado e desabilita para evitar duplicação
      chk.checked = false;
      chk.disabled = true;
      chk.title = "Já adicionado à tabela";
      const tr = chk.closest("tr");
      if (tr) tr.classList.add("ja-adicionado"); // opcional: estilizar se quiser
    }
  });
}

/* ========================
   Paginação
======================== */
function atualizarPaginacaoUI(total) {
  const info = document.getElementById("pagina-info");
  const btnPrev = document.getElementById("btn-prev");
  const btnNext = document.getElementById("btn-next");

  if (total == null) {
    totalPages = null;
    info.textContent = "";
    if (btnPrev) btnPrev.disabled = (currentPage <= 1);
    if (btnNext) btnNext.disabled = false;
    return;
  }

  totalPages = Math.max(1, Math.ceil(total / pageSize));
  info.textContent = `Página ${currentPage} de ${totalPages}`;

  if (btnPrev) btnPrev.disabled = (currentPage <= 1);
  if (btnNext) btnNext.disabled = (currentPage >= totalPages);
}

function gotoPrevPage() {
  if (currentPage > 1) carregarProdutos(currentPage - 1);
}
function gotoNextPage() {
  if (totalPages != null && currentPage >= totalPages) return;
  carregarProdutos(currentPage + 1);
}

/* ========================
   Enviar selecionados ao PAI
======================== */
// ===================================
// CUSTOM OS MODALS
// ===================================
function showOsModal(options) {
  return new Promise((resolve) => {
    const backdrop = document.createElement('div');
    backdrop.className = 'os-modal-backdrop active';
    backdrop.style.zIndex = '99999';

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

async function enviarSelecionados() {
  const selecionados = [];
  document.querySelectorAll("#tabela-produtos-body tr").forEach(tr => {
    const chk = tr.querySelector(".produto-checkbox");
    if (!chk || !chk.checked) return;
    const p = JSON.parse(tr.dataset.produto || "{}");
    selecionados.push({
      codigo_tabela: p.codigo_tabela,
      descricao: p.descricao,
      embalagem: p.embalagem || "",
      peso_liquido: p.peso_liquido || 0,
      valor: p.valor || 0,
      grupo: p.grupo || null,
      departamento: p.departamento || null,
      tipo: p.tipo,
      fornecedor: p.fornecedor || "",
      fator_comissao: 0,
      ipi: Number(p.ipi ?? 0),
      iva_st: Number(p.iva_st ?? 0)
    });
  });

  if (selecionados.length === 0) {
    await showOsModal({ title: 'Aviso', message: 'Selecione ao menos um produto.', type: 'alert' });
    return;
  }

  // devolve para o pai no buffer do contexto
  sendBufferBackToParent(selecionados);

  // volta para o pai
  window.location.href = 'criacao_tabela_preco.html';
}

function carregarPreSelecionadosDaSessao() {
  try {
    const arr = JSON.parse(sessionStorage.getItem('criacao_tabela_preco_produtos') || '[]');
    preSelecionadosCodigos = new Set(arr.map(p => p.codigo_tabela || p.codigo));
  } catch { preSelecionadosCodigos = new Set(); }
}

// No onload do filho:
window.onload = async function () {
  // ✅ Blindagem mínima: só chama se existir; se não, ignora e segue.
  if (typeof carregarPreSelecionadosDaSessao === 'function') {
    try { carregarPreSelecionadosDaSessao(); } catch (e) { console.warn(e); }
  }
  // mantém o fluxo original
  await carregarFornecedoresDb(); // ✅ Carrega filtro primeiro
  await carregarGrupos();
  await carregarProdutos();
};
