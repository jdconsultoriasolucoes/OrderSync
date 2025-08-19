const API_BASE = "https://ordersync-backend-edjq.onrender.com";

let currentPage = 1;
let pageSize = 25;
let totalPages = null;
let preSelecionadosCodigos = new Set(); // para pré-marcar checkboxes (enviado pelo pai)

/* ========================
   Bootstrap
======================== */

document.addEventListener("DOMContentLoaded", () => {
  const selGrupo      = document.getElementById("grupo");
  const selFornecedor = document.getElementById("filtro-fornecedor");
  const btnFiltrar    = document.getElementById("btn-filtrar");
  const btnLimpar     = document.getElementById("btn-limpar");
  const ps            = document.getElementById("page_size");
  const inpPalavra    = document.getElementById("filtro-palavra");

  // Filtros
  selGrupo?.addEventListener("change",      () => { currentPage = 1; carregarProdutos(); });
  selFornecedor?.addEventListener("change", () => { currentPage = 1; carregarProdutos(); });

  // Botões da toolbar
  btnFiltrar?.addEventListener("click", () => { currentPage = 1; carregarProdutos(); });
  btnLimpar?.addEventListener("click", () => {
    if (selGrupo) selGrupo.value = "";
    if (selFornecedor) selFornecedor.value = "";
    if (inpPalavra) inpPalavra.value = "";   // limpa a palavra
    fornecedoresMap.clear();                 // limpa cache de fornecedores
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
    ?.addEventListener("click", () => window.parent?.postMessage({ type: "CLOSE_DIALOG" }, "*"));
});


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


// Recebe do pai o estado atual para pré‑marcar
window.addEventListener("message", (evt) => {
  if (!evt.data || !evt.data.type) return;
  if (evt.data.type === "INIT_STATE") {
    preSelecionadosCodigos = new Set((evt.data.payload || []).map(p => p.codigo || p.codigo_tabela));
    // se já houver lista, re-render para aplicar a marcação
    marcarPreSelecionados();
  }
});

window.onload = async function () {
  await carregarGrupos();
  await carregarProdutos();
};

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
      const grupo = item.grupo || item;
      const opt = document.createElement("option");
      opt.value = grupo;
      opt.textContent = grupo;
      selectGrupo.appendChild(opt);
    });
  } catch (e) {
    console.error(e);
  }
}

function coletarFornecedores(lista) {
  (lista || []).forEach(p => {
    const show = p.fornecedor;
    const key = norm(show);
    if (show && key && !fornecedoresMap.has(key)) {
      fornecedoresMap.set(key, show); // guarda o “bonitinho” pra exibir
    }
  });
}

function renderFornecedoresDropdown() {
  const sel = document.getElementById("filtro-fornecedor");
  if (!sel) return;

  const selecionado = sel.value;
  sel.innerHTML = "<option value=''>Todos</option>";

  // ordena alfabeticamente pelo valor exibido
  const valores = Array.from(fornecedoresMap.values()).sort((a,b) =>
    a.localeCompare(b, 'pt-BR', { sensitivity: 'base' })
  );

  for (const f of valores) {
    const o = document.createElement("option");
    o.value = f; o.textContent = f;
    sel.appendChild(o);
  }

  if ([...sel.options].some(o => o.value === selecionado)) {
    sel.value = selecionado; // mantém a seleção do usuário
  }
}

function carregarProdutos(page = currentPage) {
  currentPage = page;

  const grupo      = document.getElementById("grupo")?.value || "";
  const fornecedor = document.getElementById("filtro-fornecedor")?.value || "";
  const termo      = document.getElementById("filtro-palavra")?.value?.trim() || "";
  const termoN     = normText(termo);

  const url = new URL(`${API_BASE}/tabela_preco/produtos_filtro`);
  if (grupo)      url.searchParams.append("grupo", grupo);
  if (fornecedor) url.searchParams.append("fornecedor", fornecedor);
  if (termo)      url.searchParams.append("q", termo); // ajuste se o nome do param for outro
  url.searchParams.append("page", currentPage);
  url.searchParams.append("page_size", pageSize);

  fetch(url)
    .then(r => { if (!r.ok) throw new Error("Erro ao buscar produtos"); return r.json(); })
    .then(data => {
      const lista = Array.isArray(data) ? data
                  : (Array.isArray(data.items) ? data.items : []);

      // dropdown de fornecedor (distinct)
      coletarFornecedores(lista);
      renderFornecedoresDropdown();

      // aplica filtros locais (garante mesmo se o backend não filtrar)
      let base = lista;
      if (fornecedor) base = base.filter(p => p.fornecedor === fornecedor);
      if (termoN)     base = base.filter(p => matchesTerm(p, termoN));

      let items = [], total = 0;
      if (Array.isArray(data)) {
        const start = (currentPage - 1) * pageSize;
        const end   = start + pageSize;
        items = base.slice(start, end);
        total = base.length;
      } else {
        items = base;
        total = typeof data.total === "number" ? data.total : base.length;
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
      <td class="num">${(p.peso_liquido ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
      <td class="num">${(p.valor ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
    `;
    // anexa o objeto completo na linha para facilitar coleta
    tr.dataset.produto = JSON.stringify(p);
    tbody.appendChild(tr);
  });
}

function marcarPreSelecionados() {
  if (!preSelecionadosCodigos.size) return;
  document.querySelectorAll("#tabela-produtos-body .produto-checkbox").forEach(chk => {
    const codigo = chk.dataset.codigo;
    if (preSelecionadosCodigos.has(codigo)) chk.checked = true;
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
function enviarSelecionados() {
  const selecionados = [];
  document.querySelectorAll("#tabela-produtos-body tr").forEach(tr => {
    const chk = tr.querySelector(".produto-checkbox");
    if (!chk || !chk.checked) return;

    const p = JSON.parse(tr.dataset.produto || "{}");
    selecionados.push({
      // chaves que o pai vai usar para merge/render
      id: p.codigo_tabela,              // usando código como ID estável
      codigo: p.codigo_tabela,
      nome: p.descricao,
      grupo: p.grupo || null,
      marca: p.marca || null,
      embalagem: p.embalagem || null,
      peso_liquido: p.peso_liquido || 0,
      preco_base: p.valor || 0,
      desconto: 0                      // pai pode editar depois, se necessário
    });
  });

  if (selecionados.length === 0) {
    alert("Selecione ao menos um produto.");
    return;
  }

  window.parent?.postMessage({
    type: "PRODUCTS_SELECTED",
    payload: selecionados
  }, "*");
}
