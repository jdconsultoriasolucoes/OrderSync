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

const ENDPOINTS_AUX = {
  familias: `${API_BASE}/api/familias`,
  tiposGiro: `${API_BASE}/api/tipos-giro`,
  unidades: `${API_BASE}/api/unidades`,
};

let PROD_ENDPOINT = null;
let CURRENT_ID = null;

// === Helpers básicos ===
const $ = (id) => document.getElementById(id);

function toast(msg) {
  const t = $("toast");
  if (!t) {
    alert(msg);
    return;
  }
  t.textContent = msg;
  t.classList.add("show");
  t.style.display = "block";
  setTimeout(() => {
    t.classList.remove("show");
    t.style.display = "none";
  }, 2500);
}

function debounce(fn, delay = 400) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

async function fetchRaw(url, options = {}) {
  const opts = {
    credentials: "include",
    ...options,
  };
  return fetch(url, opts);
}

async function fetchJSON(url, options = {}) {
  const headers = options.headers || {};
  const opts = {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  };

  const r = await fetch(url, opts);
  const text = await r.text().catch(() => "");

  let data = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (_) {
      data = {};
    }
  }

  if (!r.ok) {
    const msg = data.detail || data.message || r.statusText || "Erro na requisição.";
    const err = new Error(msg);
    err.status = r.status;
    err.data = data;
    throw err;
  }

  return data;
}

async function resolveProdutosEndpoint(force = false) {
  if (!force && PROD_ENDPOINT) return PROD_ENDPOINT;

  const cached = !force && localStorage.getItem("ordersync_prod_endpoint");
  if (cached) {
    PROD_ENDPOINT = cached;
    return cached;
  }

  for (const base of CANDIDATES) {
    try {
      const probe = await fetchRaw(`${base}?limit=1&offset=0`, { method: "GET" });
      if (probe.status !== 404) {
        PROD_ENDPOINT = base;
        localStorage.setItem("ordersync_prod_endpoint", base);
        console.log("[produto] endpoint resolvido:", base);
        return base;
      }
    } catch (e) {
      // ignora e tenta o próximo
    }
  }

  // fallback bruto: assume o primeiro
  PROD_ENDPOINT = CANDIDATES[0];
  localStorage.setItem("ordersync_prod_endpoint", PROD_ENDPOINT);
  return PROD_ENDPOINT;
}

// wrappers que usam fallback automático quando 404
async function produtosGET(path = "", qs = "") {
  const tried = new Set();
  while (tried.size < CANDIDATES.length) {
    const base = await resolveProdutosEndpoint();
    try {
      return await fetchJSON(`${base}${path}${qs}`, { method: "GET" });
    } catch (e) {
      if (e.status === 404) {
        tried.add(base);
        PROD_ENDPOINT = null;
        localStorage.removeItem("ordersync_prod_endpoint");
        continue;
      }
      throw e;
    }
  }
  // se tudo falhar, taca-lhe exceção
  throw new Error("Não foi possível localizar o endpoint de produtos.");
}

async function produtosPOST(body) {
  const base = await resolveProdutosEndpoint();
  const paths = ["", "/"]; // alguns endpoints podem ser /api/produto, outros /api/produto/
  for (const p of paths) {
    try {
      return await fetchJSON(`${base}${p}`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    } catch (e) {
      if (e.status === 404) continue;
      throw e;
    }
  }
  // tudo falhou → tenta no base simples
  return await fetchJSON(base, { method: "POST", body: JSON.stringify(body) });
}

async function produtosPATCH(id, body) {
  const base = await resolveProdutosEndpoint();
  for (const p of [`${base}/${id}`, `${base}/${encodeURIComponent(id)}`]) {
    try {
      return await fetchJSON(p, {
        method: "PATCH",
        body: JSON.stringify(body),
      });
    } catch (e) {
      if (e.status === 404) continue;
      throw e;
    }
  }
  throw new Error("Não foi possível atualizar o produto.");
}

// ---------- leitura / preenchimento formulário ----------
function getValue(id) {
  const el = $(id);
  if (!el) return "";
  if (el.type === "number") {
    return el.value;
  }
  return el.value != null ? el.value : "";
}

function getNumber(id) {
  const v = getValue(id).replace(",", ".").trim();
  if (v === "") return undefined;
  const n = Number(v);
  return Number.isNaN(n) ? undefined : n;
}

function getInt(id) {
  const v = getValue(id).trim();
  if (v === "") return undefined;
  const n = parseInt(v, 10);
  return Number.isNaN(n) ? undefined : n;
}

function getDateValue(id) {
  const v = getValue(id).trim();
  return v === "" ? undefined : v;
}

function readForm() {
  const produto = {
    codigo_supra: getValue("codigo_supra") || undefined,
    nome_produto: getValue("nome_produto") || undefined,
    status_produto: getValue("status_produto") || undefined,
    tipo_giro: getValue("tipo_giro") || undefined,

    linha: getValue("linha") || undefined,
    familia: getInt("familia"),
    filhos: getInt("filhos"),

    unidade: getValue("unidade") || undefined,
    unidade_anterior: getValue("unidade_anterior") || undefined,
    peso: getNumber("peso"),
    peso_bruto: getNumber("peso_bruto"),
    embalagem_venda: getValue("embalagem_venda") || undefined,
    unidade_embalagem: getValue("unidade_embalagem") || undefined,

    estoque_disponivel: getInt("estoque_disponivel"),
    estoque_ideal: getInt("estoque_ideal"),

    codigo_ean: getValue("codigo_ean") || undefined,
    codigo_embalagem: getValue("codigo_embalagem") || undefined,
    ncm: getValue("ncm") || undefined,

    fornecedor: getValue("fornecedor") || undefined,

    preco: getNumber("preco"),
    preco_tonelada: getNumber("preco_tonelada"),
    validade_tabela: getDateValue("validade_tabela"),

    preco_anterior: getNumber("preco_anterior"),
    preco_tonelada_anterior: getNumber("preco_tonelada_anterior"),
    validade_tabela_anterior: getDateValue("validade_tabela_anterior"),

    desconto_valor_tonelada: getNumber("desconto_valor_tonelada"),
    data_desconto_inicio: getDateValue("data_desconto_inicio"),
    data_desconto_fim: getDateValue("data_desconto_fim"),
  };

  Object.keys(produto).forEach((k) => {
    if (produto[k] === undefined) delete produto[k];
  });

  const imposto = {
    ipi: getNumber("ipi"),
    icms: getNumber("icms"),
    iva_st: getNumber("iva_st"),
    cbs: getNumber("cbs"),
    ibs: getNumber("ibs"),
  };
  Object.keys(imposto).forEach((k) => {
    if (imposto[k] === undefined) delete imposto[k];
  });

  const impostoOut = Object.keys(imposto).length ? imposto : null;

  return { produto, imposto: impostoOut };
}

function fillForm(p) {
  if (!p) return;

  const set = (id, v) => {
    const el = $(id);
    if (!el) return;
    if (el.type === "number" && typeof v === "number") {
      el.value = String(v);
    } else {
      el.value = v != null ? v : "";
    }
  };

  CURRENT_ID = p.id || null;

  set("codigo_supra", p.codigo_supra);
  set("nome_produto", p.nome_produto);
  set("status_produto", p.status_produto);
  set("tipo_giro", p.tipo_giro);

  set("linha", p.linha);
  set("familia", p.familia);
  set("filhos", p.filhos);

  set("unidade", p.unidade);
  set("unidade_anterior", p.unidade_anterior);
  set("peso", p.peso);
  set("peso_bruto", p.peso_bruto);
  set("embalagem_venda", p.embalagem_venda);
  set("unidade_embalagem", p.unidade_embalagem);

  set("estoque_disponivel", p.estoque_disponivel);
  set("estoque_ideal", p.estoque_ideal);

  set("codigo_ean", p.codigo_ean);
  set("codigo_embalagem", p.codigo_embalagem);
  set("ncm", p.ncm);

  set("fornecedor", p.fornecedor);

  set("preco", p.preco);
  set("preco_tonelada", p.preco_tonelada);
  set("validade_tabela", p.validade_tabela);

  set("preco_anterior", p.preco_anterior);
  set("preco_tonelada_anterior", p.preco_tonelada_anterior);
  set("validade_tabela_anterior", p.validade_tabela_anterior);

  set("desconto_valor_tonelada", p.desconto_valor_tonelada);
  set("data_desconto_inicio", p.data_desconto_inicio);
  set("data_desconto_fim", p.data_desconto_fim);

  if ($("reajuste")) {
    $("reajuste").textContent =
      p.reajuste_percentual != null ? `${p.reajuste_percentual.toFixed(2)}%` : "—";
  }
  if ($("vigencia")) {
    $("vigencia").textContent = p.vigencia_ativa ? "Sim" : "Não";
  }

  const imp = p.imposto || {};
  set("ipi", imp.ipi);
  set("icms", imp.icms);
  set("iva_st", imp.iva_st);
  set("cbs", imp.cbs);
  set("ibs", imp.ibs);
}

function clearForm() {
  const root = document.querySelector(".card");
  if (!root) return;
  root.querySelectorAll("input, select, textarea").forEach((el) => {
    if (el.type === "checkbox" || el.type === "radio") {
      el.checked = false;
    } else {
      el.value = "";
    }
  });

  if ($("reajuste")) $("reajuste").textContent = "—";
  if ($("vigencia")) $("vigencia").textContent = "—";
  CURRENT_ID = null;
}

// ---------- cálculo/aux ----------
function setSelect(el, items, getLabel = (x) => x.label, getValue = (x) => x.value) {
  if (!el) return;
  el.innerHTML =
    '<option value="">— selecione —</option>' +
    (items || [])
      .map((it) => `<option value="${getValue(it)}">${getLabel(it)}</option>`)
      .join("");
}

function reajustePercentual(atual, anterior) {
  if (anterior == null || anterior === 0 || atual == null) return null;
  return ((atual - anterior) / anterior) * 100;
}

function parseDateBrToISO(input) {
  const v = (input || "").trim();
  const m = v.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (!m) return null;
  let [, d, M, y] = m;
  if (d.length === 1) d = "0" + d;
  if (M.length === 1) M = "0" + M;
  return `${y}-${M}-${d}`;
}

// ---------- busca / modal ----------
function renderSearchResults(items) {
  const box = $("search-results");
  if (!box) return;

  if (!items || !items.length) {
    box.innerHTML = `<div class="empty">Nenhum produto encontrado.</div>`;
    return;
  }

  const rows = items
    .map(
      (p) => `
    <tr data-id="${p.id}">
      <td>${p.codigo_supra || ""}</td>
      <td>${p.nome_produto || ""}</td>
      <td>${p.preco != null ? p.preco.toFixed(2) : ""}</td>
      <td>${p.unidade || ""}</td>
      <td>${p.status_produto || ""}</td>
    </tr>
  `
    )
    .join("");

  box.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Código</th>
          <th>Descrição</th>
          <th>Preço</th>
          <th>Unid.</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;

  box.querySelectorAll("tbody tr").forEach((tr) => {
    tr.addEventListener("click", async () => {
      const id = tr.getAttribute("data-id");
      try {
        const base = await resolveProdutosEndpoint();
        const data = await fetchJSON(`${base}/${id}`);
        fillForm(data);
        const modal = $("search-modal");
        if (modal && modal.close) modal.close();
        else modal?.classList.add("hidden");
      } catch (e) {
        console.error(e);
        toast("Erro ao abrir item.");
      }
    });
  });
}

const doSearch = debounce(async () => {
  const inp = $("search-input");
  const box = $("search-results");
  if (!inp || !box) return;

  const q = inp.value.trim();
  if (!q) {
    box.innerHTML = `<div class="empty">Digite parte do código ou descrição…</div>`;
    return;
  }

  try {
    const base = await resolveProdutosEndpoint();
    const url = `${base}?q=${encodeURIComponent(q)}&limit=50&offset=0`;
    const data = await fetchJSON(url);
    renderSearchResults(data);
  } catch (e) {
    console.error(e);
    box.innerHTML = `<div class="empty">Erro ao buscar produtos.</div>`;
  }
}, 400);

// ---------- Importar PDF (INS/PET + validade via modal) ----------
async function uploadListaPdf(file) {
  if (!file) {
    toast("Selecione um arquivo PDF.");
    return;
  }

  const tipoEl = $("import_tipo_lista");
  const validadeEl = $("import_validade");

  const tipo = tipoEl ? tipoEl.value : "";
  const validadeISO = validadeEl ? validadeEl.value : "";

  if (!tipo) {
    toast("Informe o tipo da lista (INSUMOS ou PET).");
    return;
  }

  if (!validadeISO) {
    toast("Informe a validade da tabela.");
    return;
  }

  const base = await resolveProdutosEndpoint().catch(() => null);
  if (!base) {
    toast("Não consegui resolver o endpoint de produtos.");
    return;
  }

  const importBase = base
    .replace("/produtos_v2", "/produto_v2")
    .replace("/produtos", "/produto");

  const url = `${importBase}/importar-lista`;

  const formData = new FormData();
  formData.append("tipo_lista", tipo);           // "INSUMOS" ou "PET"
  formData.append("validade_tabela", validadeISO); // yyyy-mm-dd do input date
  formData.append("file", file);

  try {
    const res = await fetch(url, {
      method: "POST",
      body: formData,
    });

    let data = {};
    try {
      data = await res.json();
    } catch (_) {
      data = {};
    }

    if (!res.ok) {
      const msg =
        data.detail ||
        data.message ||
        res.statusText ||
        "Erro ao importar PDF.";
      throw new Error(msg);
    }

    const {
      total_linhas_pdf,
      lista,
      fornecedor,
      validade_tabela,
      sync,
    } = data;

    // Compatibilidade com API nova (sync) e antiga (inseridos/atualizados na raiz)
    let inseridos = data.inseridos ?? 0;
    let atualizados = data.atualizados ?? 0;
    let inativados = 0;

    if (sync && Array.isArray(sync.grupos)) {
      inseridos = sync.grupos.reduce(
        (acc, g) => acc + (g.inseridos || 0),
        0
      );
      atualizados = sync.grupos.reduce(
        (acc, g) => acc + (g.atualizados || 0),
        0
      );
      inativados = sync.grupos.reduce(
        (acc, g) => acc + (g.inativados || 0),
        0
      );
    }

    // --- mensagem no frontend ---
    const totalLinhas = total_linhas_pdf ?? 0;
    toast(
      `Ingestão realizada com sucesso: ${totalLinhas} linhas (${inseridos} novos / ${atualizados} atualizados / ${inativados} inativados).`
    );

    // --- opção de baixar o relatório em PDF ---
    const listaFinal = lista || tipo;
    const fornecedorFinal = fornecedor || "";

    if (listaFinal && fornecedorFinal) {
      const relatorioUrl = `${importBase}/relatorio-lista?fornecedor=${encodeURIComponent(
        fornecedorFinal
      )}&lista=${encodeURIComponent(listaFinal)}`;

      const querPdf = confirm(
        "Ingestão realizada com sucesso.\n\nDeseja baixar o relatório em PDF desta lista?"
      );

      if (querPdf) {
        window.open(relatorioUrl, "_blank");
      }
    }
    
  } catch (e) {
    console.error(e);
    toast(e.message || "Erro ao importar PDF.");
  }
}

// ---------- Importar PDF (INS/PET + validade) ----------
function setupImportarPdf() {
  const btnImportar = $("btn-importar");
  if (!btnImportar) return;

  // evita duplicar listeners se setupImportarPdf for chamado mais de 1x
  if (btnImportar.dataset.wiredImportPdf === "1") return;
  btnImportar.dataset.wiredImportPdf = "1";

  // ---------- Helpers locais ----------
  const normalizeTipo = (tipoRaw) => {
    if (!tipoRaw) return null;
    let tipo = String(tipoRaw).trim().toUpperCase();
    if (["INS", "INSUMO"].includes(tipo)) tipo = "INSUMOS";
    else if (["PET", "PETS"].includes(tipo)) tipo = "PET";
    if (!["INSUMOS", "PET"].includes(tipo)) return null;
    return tipo;
  };

  const normalizeValidISO = (val) => {
    if (!val) return null;
    const s = String(val).trim();
    // se vier do input type="date", já é yyyy-mm-dd
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
    // se vier dd/mm/aaaa (seu parse já existe)
    return parseDateBrToISO(s);
  };

  const doImport = async ({ tipo, validadeISO, file }) => {
    if (!tipo) {
      alert("Tipo inválido. Use INSUMOS ou PET.");
      return;
    }
    if (!validadeISO) {
      alert("Data de validade inválida. Use dd/mm/aaaa ou selecione no calendário.");
      return;
    }
    if (!file) {
      alert("Selecione um arquivo PDF.");
      return;
    }

    try {
      const base = await resolveProdutosEndpoint().catch(() => null);
      if (!base) {
        toast("Não consegui resolver o endpoint de produtos.");
        return;
      }

      // força usar /produto em vez de /produtos para a importação
      const importBase = base
        .replace("/produtos_v2", "/produto_v2")
        .replace("/produtos", "/produto");

      const url = `${importBase}/importar-lista`;
      const formData = new FormData();
      formData.append("tipo_lista", tipo);
      formData.append("validade_tabela", validadeISO); // yyyy-mm-dd
      formData.append("file", file);

      const resp = await fetch(url, { method: "POST", body: formData });

      let data = {};
      try { data = await resp.json(); } catch (_) { data = {}; }

      if (!resp.ok) {
        const msg = data.detail || data.message || resp.statusText || "Erro ao importar PDF.";
        alert(msg);
        return;
      }

      const { total_linhas_pdf, lista, fornecedor, sync } = data;

      // Compatibilidade com API nova (sync) e antiga (inseridos/atualizados na raiz)
      let inseridos = data.inseridos ?? 0;
      let atualizados = data.atualizados ?? 0;
      let inativados = 0;

      if (sync && Array.isArray(sync.grupos)) {
        inseridos = sync.grupos.reduce((acc, g) => acc + (g.inseridos || 0), 0);
        atualizados = sync.grupos.reduce((acc, g) => acc + (g.atualizados || 0), 0);
        inativados = sync.grupos.reduce((acc, g) => acc + (g.inativados || 0), 0);
      }

      const totalLinhas = total_linhas_pdf ?? 0;
      toast(
        `Ingestão realizada com sucesso: ${totalLinhas} linhas (${inseridos} novos / ${atualizados} atualizados / ${inativados} inativados).`
      );

      // opção de baixar o relatório em PDF
      const listaFinal = lista || tipo;
      const fornecedorFinal = fornecedor || "";

      if (listaFinal && fornecedorFinal) {
        const relatorioUrl = `${importBase}/relatorio-lista?fornecedor=${encodeURIComponent(
          fornecedorFinal
        )}&lista=${encodeURIComponent(listaFinal)}`;

        const querPdf = confirm(
          "Ingestão realizada com sucesso.\n\nDeseja baixar o relatório em PDF desta lista?"
        );

        if (querPdf) window.open(relatorioUrl, "_blank");
      }

      return true;
    } catch (err) {
      console.error(err);
      alert(err.message || "Erro inesperado ao importar PDF.");
      return false;
    }
  };

  // ---------- Caminho NOVO (modal), se existir ----------
  const modal = $("import-modal");
  const modalTipo = $("import_tipo_lista");
  const modalValidade = $("import_validade");
  const modalArquivo = $("import_arquivo");
  const modalConfirm = $("import-confirm");
  const modalCancel = $("import-cancel");
  const modalClose = $("import-close");

  const openModal = () => modal?.classList.remove("hidden");
  const closeModal = () => modal?.classList.add("hidden");

  if (modal && modalTipo && modalValidade && modalArquivo && modalConfirm) {
    btnImportar.addEventListener("click", () => {
      // opcional: limpar ao abrir
      // modalTipo.value = "";
      // modalValidade.value = "";
      // modalArquivo.value = "";
      openModal();
    });

    modalCancel?.addEventListener("click", closeModal);
    modalClose?.addEventListener("click", closeModal);

    modalConfirm.addEventListener("click", async () => {
      const tipo = normalizeTipo(modalTipo.value);
      const validadeISO = normalizeValidISO(modalValidade.value);
      const file = modalArquivo.files?.[0];

      const ok = await doImport({ tipo, validadeISO, file });
      if (ok) {
        // opcional: fecha e reseta se deu certo
        modalArquivo.value = "";
        closeModal();
      }
    });

    return; // IMPORTANTÍSSIMO: se tem modal, não monta o fluxo antigo
  }

  // ---------- Caminho ANTIGO (fallback): prompt + input invisível ----------
  const inputFile = document.createElement("input");
  inputFile.type = "file";
  inputFile.accept = "application/pdf";
  inputFile.style.display = "none";
  document.body.appendChild(inputFile);

  btnImportar.addEventListener("click", () => {
    let tipoRaw = window.prompt("Qual lista será importada? (INSUMOS ou PET)");
    const tipo = normalizeTipo(tipoRaw);
    if (!tipo) {
      if (tipoRaw != null) alert("Tipo inválido. Use INSUMOS ou PET.");
      return;
    }

    let validadeBr = window.prompt("Informe a data de validade da tabela (dd/mm/aaaa):");
    const validadeISO = normalizeValidISO(validadeBr);
    if (!validadeISO) {
      alert("Data de validade inválida. Use o formato dd/mm/aaaa.");
      return;
    }

    inputFile.onchange = async () => {
      const file = inputFile.files?.[0];
      inputFile.value = "";
      if (!file) return;

      await doImport({ tipo, validadeISO, file });
    };

    inputFile.click();
  });
}

// ---------- Init ----------
document.addEventListener("DOMContentLoaded", async () => {
  try {
    await resolveProdutosEndpoint();
  } catch (e) {
    console.warn("[produto] não foi possível resolver endpoint ainda:", e);
  }

  $("btn-novo")?.addEventListener("click", () => {
    clearForm();
    toast("Novo produto em edição.");
  });

  $("btn-salvar")?.addEventListener("click", async () => {
    const { produto, imposto } = readForm();
    try {
      if (CURRENT_ID) {
        const res = await produtosPATCH(CURRENT_ID, { produto, imposto });
        fillForm(res);
        toast("Produto atualizado.");
        return;
      }

      let alvoId = null;
      if (produto.codigo_supra) {
        try {
          const probe = await produtosGET(
            "",
            `?q=${encodeURIComponent(produto.codigo_supra)}&limit=1`
          );
          alvoId = probe && probe.length && probe[0].id ? probe[0].id : null;
        } catch {}
      }

      if (alvoId) {
        const res = await produtosPATCH(alvoId, { produto, imposto });
        fillForm(res);
        toast("Produto atualizado.");
      } else {
        const res = await produtosPOST({ produto, imposto });
        fillForm(res);
        toast("Produto criado.");
      }
    } catch (e) {
      toast("Erro ao salvar. Veja o console.");
      console.error(e);
    }
  });

  $("btn-editar")?.addEventListener("click", () => {
    toast("Você já pode editar os campos e salvar.");
  });

  $("btn-buscar")?.addEventListener("click", () => {
    const modal = $("search-modal");
    if (modal && modal.showModal) {
      modal.showModal();
    } else {
      modal?.classList.remove("hidden");
    }
    const box = $("search-results");
    if (box) {
      box.innerHTML = `<div class="empty">Digite parte do código ou descrição…</div>`;
    }
    const inp = $("search-input");
    inp && inp.focus();
  });

  const modal = $("search-modal");
  $("search-close")?.addEventListener("click", () => {
    if (modal && modal.close) modal.close();
    else modal?.classList.add("hidden");
  });
  $("search-cancel")?.addEventListener("click", () => {
    if (modal && modal.close) modal.close();
    else modal?.classList.add("hidden");
  });
  $("search-input")?.addEventListener("input", doSearch);
  $("search-input")?.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") {
      if (modal && modal.close) modal.close();
      else modal?.classList.add("hidden");
    }
    if (ev.key === "Enter") {
      const first = document.querySelector("#search-results tbody tr");
      if (first) first.click();
    }
  });

  setupImportarPdf();

  try {
    const url = new URL(window.location.href);
    const id = url.searchParams.get("id");
    if (id) {
      const base = await resolveProdutosEndpoint();
      const data = await fetchJSON(`${base}/${id}`);
      fillForm(data);
    }
  } catch (e) {
    console.warn("[produto] não foi possível carregar produto inicial:", e);
  }
});
