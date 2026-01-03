// base do backend FastAPI publicado no Render
const API_BASE = "https://ordersync-backend-edjq.onrender.com";

const API = {
  list: `${API_BASE}/api/pedidos`,
  status: `${API_BASE}/api/pedidos/status`,
  resumo: (id) => `${API_BASE}/api/pedidos/${id}/resumo`,
  cancelar: (id) => `${API_BASE}/api/pedidos/${id}/cancelar`,
  reenviar: (id) => `${API_BASE}/api/pedidos/${id}/reenviar_email`,
  pdf: (id) => `${API_BASE}/api/pedido/${id}/pdf`, // endpoint de download direto
};

let state = { page: 1, pageSize: 25, total: 0 };

// ---------------------- utils ----------------------
function fmtMoney(v) {
  if (v == null) return "---";
  try {
    return Number(v).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  } catch {
    return v;
  }
}

function fmtDate(s) {
  if (!s) return "---";
  const d = new Date(s);
  const dt = d.toLocaleDateString("pt-BR");
  const hr = d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return `${dt} ${hr}`;
}

function getStatusBadge(status) {
  if (!status) return '<span class="status-badge status-aberto">---</span>';
  const s = status.toUpperCase();
  if (s === 'CONFIRMADO') return `<span class="status-badge status-conf">CONFIRMADO</span>`;
  if (s === 'CANCELADO') return `<span class="status-badge status-cancel">CANCELADO</span>`;
  if (s === 'ENVIADO') return `<span class="status-badge status-env">ENVIADO</span>`;
  if (s === 'ENTREGUE') return `<span class="status-badge status-entregue">ENTREGUE</span>`;

  return `<span class="status-badge status-aberto">${status}</span>`;
}

function addDays(baseDate, days) {
  const d = new Date(baseDate);
  d.setDate(d.getDate() + days);
  return d;
}

// ---------------------- carregar status ----------------------
async function loadStatus() {
  const r = await fetch(API.status, { cache: "no-store" });
  if (!r.ok) {
    console.error("Falha ao carregar status:", r.status, await r.text());
    return;
  }
  const j = await r.json();
  const arr = Array.isArray(j) ? j : (j.data || j.items || j.results || []);
  const sel = document.getElementById("fStatus");
  if (!sel) return;

  sel.innerHTML = "";

  // opção “Todos” (vazio = não filtra)
  const optAll = document.createElement("option");
  optAll.value = "";
  optAll.textContent = "Todos";
  sel.appendChild(optAll);

  arr.forEach(s => {
    const codigo = s.codigo || s.code || s.id || s.value || s;
    const rotulo = s.rotulo || s.label || s.nome || s.description || codigo;
    if (!codigo) return;
    const opt = document.createElement("option");
    opt.value = String(codigo);
    opt.textContent = String(rotulo);
    sel.appendChild(opt);
  });

  // deixa em “Todos” por padrão
  sel.value = "";
}

// ---------------------- ler filtros da tela ----------------------
function getFilters() {
  const fFrom = document.getElementById("fFrom").value;
  const fTo = document.getElementById("fTo").value;
  const fTabela = document.getElementById("fTabela").value || null;
  const fCliente = document.getElementById("fCliente").value || null;
  const fFornecedor = document.getElementById("fFornecedor").value || null;

  // mesmo que seja um <select> simples, selectedOptions ainda funciona
  const selStatus = Array.from(
    document.getElementById("fStatus").selectedOptions
  ).map((o) => o.value);

  return { fFrom, fTo, fTabela, fCliente, fFornecedor, selStatus };
}

//--------------------------------
// Converte "DD/MM/AAAA" -> "AAAA-MM-DD". Se já vier "AAAA-MM-DD", mantém.
function toISO(d) {
  if (!d) return "";
  if (/^\d{4}-\d{2}-\d{2}$/.test(d)) return d; // já está ISO
  const m = d.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  return m ? `${m[3]}-${m[2]}-${m[1]}` : d;
}

function toBR(iso) {
  if (!iso) return "";
  const [y, m, dd] = iso.split("-");
  return `${dd}/${m}/${y}`;
}

// ---------------------- buscar lista no backend ----------------------
async function loadList(page = 1) {
  state.page = page;
  const p = buildParams(page, state.pageSize);
  const url = `${API.list}?${p.toString()}`;

  // Feedback visual
  const btn = document.getElementById("btnBuscar");
  const orgText = btn ? btn.innerText : "";
  if (btn) btn.innerText = "...";

  try {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) {
      console.error("Falha ao carregar pedidos:", r.status, await r.text());
      return;
    }
    const j = await r.json();
    const arr = Array.isArray(j) ? j : (j.data || j.items || j.results || (j.payload && j.payload.items) || []);
    state.total = (j.total ?? j.count ?? (Array.isArray(arr) ? arr.length : 0)) || 0;

    renderTable(arr); // Backend já agrupa? Se sim, ok. Se não, add groupByPedido. Backend parece já retornar lista.
    renderPager();
  } finally {
    if (btn) btn.innerText = orgText;
  }
}

function buildParams(page, pageSize) {
  const { fFrom, fTo, fTabela, fCliente, fFornecedor, selStatus } = getFilters();
  let fromISO = toISO(fFrom);
  let toISO_ = toISO(fTo);

  if (!fromISO && !toISO_) {
    const hoje = new Date();
    const inicio = new Date(hoje);
    inicio.setDate(hoje.getDate() - 30);
    fromISO = inicio.toISOString().slice(0, 10);
    toISO_ = hoje.toISOString().slice(0, 10);
  }

  const params = new URLSearchParams();
  params.set("from", fromISO);
  params.set("to", toISO_);

  if (selStatus && selStatus.length) {
    const s = selStatus.join(",");
    params.set("status", s);
  }
  if (fTabela) params.set("tabela_nome", fTabela);
  if (fCliente) params.set("cliente", fCliente);
  if (fFornecedor) params.set("fornecedor", fFornecedor);

  params.set("page", page);
  params.set("pageSize", pageSize);
  params.set("limit", pageSize);
  params.set("offset", String((page - 1) * pageSize));

  return params;
}

// ---------------------- desenhar tabela ----------------------
function renderTable(rows) {
  const tb = document.getElementById("tblBody");
  tb.innerHTML = "";

  if (!rows || !rows.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="9" class="muted">Nenhum pedido encontrado.</td>`;
    tb.appendChild(tr);
    return;
  }

  rows.forEach(row => {
    const id = row.numero_pedido ?? row.id_pedido ?? row.pedido_id;
    const dataPedido = row.data_pedido || row.created_at;
    const cliente = row.cliente_nome;
    const modalidade = row.modalidade;
    const valor = row.valor_total;
    const status = row.status_codigo;
    const tabela = row.tabela_preco_nome;
    const fornecedor = row.fornecedor;
    const link = row.link_url;

    const tr = document.createElement("tr");
    tr.classList.add("row-click");
    tr.dataset.id = id;

    // Badge visual
    const statusHtml = getStatusBadge(status);

    tr.innerHTML = `
      <td>${fmtDate(dataPedido)}</td>
      <td><a href="#" class="lnk-resumo" data-id="${id}">${id}</a></td>
      <td>${cliente}</td>
      <td><span class="badge badge-gray">${modalidade ?? "---"}</span></td>
      <td class="tar">${fmtMoney(valor)}</td>
      <td>${statusHtml}</td>
      <td>${tabela ?? "---"}</td>
      <td>${fornecedor ?? "---"}</td>
      <td>
        ${link
        ? `<button class="btn-copy" data-url="${link}">Copiar Link</button>`
        : "—"}
      </td>
    `;

    tb.appendChild(tr);

    tr.addEventListener("click", (ev) => {
      if (ev.target.closest(".btn") || ev.target.closest("a") || ev.target.closest(".btn-copy")) return;
      openResumo(id);
    });
  });
}

// ---------------------- paginação ----------------------
function renderPager() {
  const pageInfo = document.getElementById("pageInfo");
  const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
  pageInfo.textContent = `${state.page} / ${totalPages}`;
  document.getElementById("prevPage").disabled = state.page <= 1;
  document.getElementById("nextPage").disabled = state.page >= totalPages;
}

// ---------------------- drawer de resumo & Ações ----------------------
async function openResumo(id) {
  const r = await fetch(API.resumo(id), { cache: "no-store" });
  if (!r.ok) return;
  const p = await r.json();
  const el = document.getElementById("drawerContent");
  const modalidade = p.usar_valor_com_frete ? "ENTREGA" : "RETIRADA";

  el.innerHTML = `
    <div class="stack">
      <div class="kv">
        <div><b>Pedido:</b> ${p.id_pedido}</div>
        <div>${getStatusBadge(p.status)}</div>
      </div>
      <div class="kv">
        <div><b>Cliente:</b> ${p.cliente} (${p.codigo_cliente ?? "-"})</div>
        <div><b>Data:</b> ${fmtDate(p.created_at)}</div>
      </div>
      <div class="kv">
        <div><b>Modalidade:</b> ${modalidade}</div>
        <div><b>Tabela:</b> ${p.tabela_preco_nome ?? "-"}</div>
      </div>
      <div class="kv">
        <div><b>Fornecedor:</b> ${p.fornecedor ?? "-"}</div>
        <div><b>Total:</b> ${fmtMoney(p.total_pedido)}</div>
      </div>
      <div class="block">
        <b>Itens</b>
        <div class="itens">
          ${p.itens.map(i => `
            <div class="item">
              <div><b>${i.codigo}</b> - ${i.nome}</div>
              <div>${i.quantidade} x ${fmtMoney(i.preco_unit)} = <b>${fmtMoney(i.subtotal)}</b></div>
            </div>
          `).join("")}
        </div>
      </div>
    </div>
  `;

  // Renderiza Botões de Ação
  const actionsEl = document.getElementById("drawerActions");
  actionsEl.innerHTML = ""; // limpa anteriores

  // 1. PDF
  const btnPdf = document.createElement("a");
  btnPdf.className = "btn btn-outline";
  btnPdf.href = API.pdf(id);
  btnPdf.target = "_blank";
  btnPdf.innerHTML = "📄 Baixar PDF";
  actionsEl.appendChild(btnPdf);

  // 2. Reenviar Email
  const btnEmail = document.createElement("button");
  btnEmail.className = "btn btn-outline";
  btnEmail.innerHTML = "📧 Reenviar E-mail";
  btnEmail.onclick = () => doAction(API.reenviar(id), "E-mail reenviado com sucesso!");
  actionsEl.appendChild(btnEmail);

  // 3. Cancelar (só se não estiver cancelado)
  if (p.status !== "CANCELADO") {
    const btnCancel = document.createElement("button");
    btnCancel.className = "btn btn-danger";
    btnCancel.innerHTML = "🚫 Cancelar Pedido";
    btnCancel.onclick = () => {
      if (confirm("Tem certeza que deseja cancelar este pedido?")) {
        doAction(API.cancelar(id), "Pedido cancelado!", true);
      }
    };
    actionsEl.appendChild(btnCancel);
  }

  document.getElementById("drawer").classList.remove("hidden");
}

async function doAction(url, successMsg, reload = false) {
  try {
    const r = await fetch(url, { method: "POST" });
    if (r.ok) {
      alert(successMsg);
      if (reload) {
        document.getElementById("drawer").classList.add("hidden");
        loadList(state.page);
      }
    } else {
      const txt = await r.text();
      alert("Erro: " + txt);
    }
  } catch (e) {
    alert("Erro de conexão: " + e.message);
  }
}

// ---------------------- bind de eventos ----------------------
function bindUI() {
  document.getElementById("btnBuscar").addEventListener("click", () => loadList(1));

  // Refresh
  document.getElementById("btnRefresh").addEventListener("click", () => loadList(state.page));

  // Limpar
  const btnLimpar = document.getElementById("btnLimpar");
  if (btnLimpar) {
    btnLimpar.addEventListener("click", limparFiltros);
  }

  // Export
  document.getElementById("btnExport").onclick = exportarCSV;

  // Pagination - Usando onclick para evitar múltiplos listeners em caso de re-inits
  const btnPrev = document.getElementById("prevPage");
  if (btnPrev) {
    btnPrev.onclick = () => {
      if (state.page > 1) loadList(state.page - 1);
    };
  }

  const btnNext = document.getElementById("nextPage");
  if (btnNext) {
    btnNext.onclick = () => {
      const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
      if (state.page < totalPages) loadList(state.page + 1);
    };
  }

  // Drawer Close
  document.getElementById("btnCloseDrawer").onclick = () => {
    document.getElementById("drawer").classList.add("hidden");
  };

  // Período Rápido
  const periodoEl = document.getElementById("fPeriodoRapido");
  if (periodoEl) periodoEl.addEventListener("change", aplicarPeriodoRapido);
}

// ---------------------- CSV Export ----------------------
async function exportarCSV() {
  const btn = document.getElementById("btnExport");
  const orgTxt = btn.innerText;
  btn.innerText = "⏳ Baixando...";
  btn.disabled = true;

  try {
    // Pega TODOS os pedidos do filtro (pageSize alto)
    const params = buildParams(1, 5000);
    const url = `${API.list}?${params.toString()}`;

    const r = await fetch(url);
    if (!r.ok) throw new Error(`Erro HTTP: ${r.status}`);

    const j = await r.json();
    console.log("CSV Export Payload:", j);

    // Tenta normalizar a resposta
    let data = [];
    if (Array.isArray(j)) {
      data = j;
    } else if (j.data && Array.isArray(j.data)) {
      data = j.data;
    } else if (j.items && Array.isArray(j.items)) {
      data = j.items;
    } else if (j.results && Array.isArray(j.results)) {
      data = j.results;
    }

    if (!data.length) {
      alert("Nenhum dado encontrado para exportar com os filtros atuais.");
      return;
    }

    // Como o backend pode não agrupar se pedir many=true ou similar,
    // garantimos o agrupamento se vierem itens soltos (opcional, mas seguro).
    // Se o backend já retorna pedidos unicos, groupByPedido nao atrapalha (idempotente se id for unico).
    const rows = groupByPedido(data);

    // CSV Header
    let csv = "ID;Data;Cliente;Modalidade;Valor Total;Status;Tabela;Fornecedor;Link\n";

    rows.forEach(row => {
      // ajusta campos
      const id = row.numero_pedido ?? row.id_pedido ?? row.pedido_id ?? "";
      const dtRaw = row.data_pedido || row.created_at || "";
      const dt = dtRaw ? new Date(dtRaw).toLocaleDateString() : "";

      const cli = (row.cliente_nome || row.cliente || "").toString().replace(/;/g, ",");
      const modalidade = row.modalidade ?? (row.usar_valor_com_frete ? "ENTREGA" : (row.usar_valor_com_frete === false ? "RETIRADA" : ""));
      const val = (row.valor_total || row.total_pedido || 0).toString().replace(".", ",");
      const st = (row.status_codigo || row.status || "").toString();
      // Match renderTable logic for Tabela
      const tab = (row.tabela_preco_nome ?? row.tabela ?? row.tabela_nome ?? "").toString().replace(/;/g, ",");
      const forn = (row.fornecedor || "").toString().replace(/;/g, ",");
      const lnk = (row.link_url || "").toString();

      csv += `${id};${dt};${cli};${modalidade};${val};${st};${tab};${forn};${lnk}\n`;
    });

    // Download Blob
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const urlObj = URL.createObjectURL(blob);
    link.setAttribute("href", urlObj);
    link.setAttribute("download", `pedidos_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

  } catch (e) {
    console.error("Erro export:", e);
    alert("Erro na exportação: " + e.message);
  } finally {
    if (btn) {
      btn.innerText = orgTxt;
      btn.disabled = false;
    }
  }
}

// ---------------------- Init ----------------------
document.addEventListener('DOMContentLoaded', () => {
  const menuButton = document.getElementById('menu-button');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('overlay');
  if (menuButton && sidebar && overlay) {
    const open = () => { sidebar.classList.add('active'); overlay.style.display = 'block'; };
    const close = () => { sidebar.classList.remove('active'); overlay.style.display = 'none'; };
    menuButton.addEventListener('click', (e) => { e.stopPropagation(); sidebar.classList.contains('active') ? close() : open(); });
    overlay.addEventListener('click', close);
  }
});

function limparFiltros() {
  // Limpar inputs de texto
  document.getElementById("fTabela").value = "";
  document.getElementById("fCliente").value = "";
  document.getElementById("fFornecedor").value = "";

  // Resetar Status para "Todos"
  const fStatus = document.getElementById("fStatus");
  if (fStatus) fStatus.value = "";

  // Resetar Período: deixar apenas dia atual
  const fPeriodo = document.getElementById("fPeriodoRapido");
  if (fPeriodo) {
    fPeriodo.value = "custom"; // ou deixe vazio
  }

  const hoje = new Date();
  document.getElementById("fFrom").value = hoje.toISOString().slice(0, 10);
  document.getElementById("fTo").value = hoje.toISOString().slice(0, 10);

  loadList(1);
}

function aplicarPeriodoRapido() {
  const sel = document.getElementById("fPeriodoRapido");
  const val = sel.value;
  if (val === "custom") return;
  const hoje = new Date();
  const inicio = addDays(hoje, -parseInt(val, 10));
  document.getElementById("fFrom").value = inicio.toISOString().slice(0, 10);
  document.getElementById("fTo").value = hoje.toISOString().slice(0, 10);
  loadList(1);
}

(async function init() {
  bindUI();
  await loadStatus();

  const periodoEl = document.getElementById("fPeriodoRapido");
  if (periodoEl) aplicarPeriodoRapido();
  else {
    const hoje = new Date();
    const inicio = addDays(hoje, -30);
    document.getElementById("fFrom").value = inicio.toISOString().slice(0, 10);
    document.getElementById("fTo").value = hoje.toISOString().slice(0, 10);
    loadList(1);
  }

  // Event Delegation para Copiar Link principal
  document.getElementById("tblBody").addEventListener("click", (ev) => {
    const btn = ev.target.closest(".btn-copy");
    if (btn) {
      navigator.clipboard.writeText(btn.dataset.url).then(() => {
        const org = btn.innerText;
        btn.innerText = "Copiado!";
        setTimeout(() => btn.innerText = org, 1500);
      });
    }
  });

})();

// ---------------------- utils ----------------------
function fmtMoney(v) {
  if (v == null) return "---";
  try {
    return Number(v).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  } catch {
    return v;
  }
}

function fmtDate(s) {
  if (!s) return "---";
  const d = new Date(s);
  const dt = d.toLocaleDateString("pt-BR");
  const hr = d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return `${dt} ${hr}`;
}

function addDays(baseDate, days) {
  const d = new Date(baseDate);
  d.setDate(d.getDate() + days);
  return d;
}

// ---------------------- carregar status ----------------------
async function loadStatus() {
  const r = await fetch(API.status, { cache: "no-store" });
  if (!r.ok) {
    console.error("Falha ao carregar status:", r.status, await r.text());
    return;
  }
  const j = await r.json();
  const arr = Array.isArray(j) ? j : (j.data || j.items || j.results || []);
  const sel = document.getElementById("fStatus");
  if (!sel) return;

  sel.innerHTML = "";

  // opção “Todos” (vazio = não filtra)
  const optAll = document.createElement("option");
  optAll.value = "";
  optAll.textContent = "Todos";
  sel.appendChild(optAll);

  arr.forEach(s => {
    const codigo = s.codigo || s.code || s.id || s.value || s;
    const rotulo = s.rotulo || s.label || s.nome || s.description || codigo;
    if (!codigo) return;
    const opt = document.createElement("option");
    opt.value = String(codigo);
    opt.textContent = String(rotulo);
    sel.appendChild(opt);
  });

  // deixa em “Todos” por padrão
  sel.value = "";
}

// ---------------------- agrupar linhas do backend ----------------------
function groupByPedido(rows) {
  if (!Array.isArray(rows)) return [];
  const map = new Map();
  const ordered = [];
  for (const r of rows) {
    const id = r.numero_pedido ?? r.id_pedido ?? r.pedido_id ?? r.id ?? r.numero ?? r.num_pedido ?? r.codigo_pedido;
    if (!id) continue;
    if (!map.has(id)) {
      map.set(id, { ...r, _count_itens: 0 });
      ordered.push(map.get(id));
    }
    map.get(id)._count_itens += 1;
  }
  return ordered;
}


// ---------------------- ler filtros da tela ----------------------
function getFilters() {
  const fFrom = document.getElementById("fFrom").value;
  const fTo = document.getElementById("fTo").value;
  const fTabela = document.getElementById("fTabela").value || null;
  const fCliente = document.getElementById("fCliente").value || null;
  const fFornecedor = document.getElementById("fFornecedor").value || null;

  // mesmo que seja um <select> simples, selectedOptions ainda funciona
  const selStatus = Array.from(
    document.getElementById("fStatus").selectedOptions
  ).map((o) => o.value);

  return { fFrom, fTo, fTabela, fCliente, fFornecedor, selStatus };
}

//--------------------------------
// Converte "DD/MM/AAAA" -> "AAAA-MM-DD". Se já vier "AAAA-MM-DD", mantém.
function toISO(d) {
  if (!d) return "";
  if (/^\d{4}-\d{2}-\d{2}$/.test(d)) return d; // já está ISO
  const m = d.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  return m ? `${m[3]}-${m[2]}-${m[1]}` : d;
}

// Converte "AAAA-MM-DD" -> "DD/MM/AAAA" (alguns backends aceitam BR)
function toBR(iso) {
  if (!iso) return "";
  const [y, m, dd] = iso.split("-");
  return `${dd}/${m}/${y}`;
}


// ---------------------- buscar lista no backend ----------------------
async function loadList(page = 1) {
  state.page = page;

  const { fFrom, fTo, fTabela, fCliente, fFornecedor, selStatus } = getFilters();

  let fromISO = toISO(fFrom);
  let toISO_ = toISO(fTo);

  // só faz fallback se NÃO tem nenhuma das duas datas
  if (!fromISO && !toISO_) {
    const hoje = new Date();
    const inicio = new Date(hoje);
    inicio.setDate(hoje.getDate() - 30);

    fromISO = inicio.toISOString().slice(0, 10);
    toISO_ = hoje.toISOString().slice(0, 10);


  }


  const params = new URLSearchParams();

  // datas — enviamos vários nomes para garantir compat
  params.set("from", fromISO);
  params.set("to", toISO_);
  params.set("date_from", fromISO);
  params.set("date_to", toISO_);
  params.set("inicio", toBR(fromISO));
  params.set("fim", toBR(toISO_));

  // status — só manda se tiver selecionado (se “Todos”, fica vazio)
  if (selStatus && selStatus.length) {
    const s = selStatus.join(",");
    params.set("status", s);
    params.set("status_codigo", s);
    params.set("status_codes", s);
  }

  // outros filtros — sinônimos
  if (fTabela) {
    params.set("tabela_nome", fTabela);
    params.set("tabela", fTabela);
  }
  if (fCliente) {
    params.set("cliente", fCliente);
    params.set("cliente_nome", fCliente);
  }
  if (fFornecedor) {
    params.set("fornecedor", fFornecedor);
    params.set("fornecedor_nome", fFornecedor);
  }

  // paginação — várias convenções
  params.set("page", state.page);
  params.set("pageSize", state.pageSize);
  params.set("limit", state.pageSize);
  params.set("offset", String((state.page - 1) * state.pageSize));

  const url = `${API.list}?${params.toString()}`;
  console.log("GET", url);

  // Feedback visual
  const btn = document.getElementById("btnBuscar");
  // const orgText = "Buscar";
  if (btn) {
    // btn.innerText = "...";
    btn.disabled = true;
  }

  try {

    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) {
      console.error("Falha ao carregar pedidos:", r.status, await r.text());
      return;
    }
    const j = await r.json();

    // 8. monta resposta
    // ... logic above in backend ...
    // Frontend JS:
    console.log("loadList: Recebido do backend:", j);
    const arr = Array.isArray(j) ? j : (j.data || j.items || j.results || (j.payload && j.payload.items) || []);
    state.total = (j.total ?? j.count ?? (Array.isArray(arr) ? arr.length : 0)) || 0;
    console.log("loadList: Array processado:", arr, "Total:", state.total);

    const rows = groupByPedido(arr);
    console.log("loadList: Rows agrupadas:", rows);
    renderTable(rows);
    renderPager();
  } catch (e) {
    console.error("Erro em loadList:", e);
    document.getElementById("tblBody").innerHTML = `<tr><td colspan="9" class="error">Erro ao buscar dados: ${e.message}</td></tr>`;
  } finally {
    if (btn) {
      // btn.innerText = orgText;
      btn.disabled = false;
    }
  }
}

// ...

// ---------------------- desenhar tabela ----------------------
function renderTable(rows) {
  const tb = document.getElementById("tblBody");
  tb.innerHTML = "";

  console.log("renderTable: Iniciando render. Rows:", rows);

  if (!rows || !rows.length) {
    console.warn("renderTable: Nenhuma linha para renderizar.");
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="9" class="muted">Nenhum pedido encontrado.</td>`;
    tb.appendChild(tr);
    return;
  }

  rows.forEach(row => {
    try {
      const id = row.numero_pedido ?? row.id_pedido ?? row.pedido_id ?? row.id ?? row.numero ?? row.num_pedido ?? row.codigo_pedido;
      const dataPedido = row.data_pedido || row.created_at || row.data || row.dt || row.data_emissao;
      const cliente = row.cliente_nome || row.cliente || row.nome_cliente || row.cliente_fantasia || "---";
      const modalidade = row.modalidade ?? (row.usar_valor_com_frete ? "ENTREGA" : (row.usar_valor_com_frete === false ? "RETIRADA" : "---"));
      const valor = row.valor_total ?? row.total_pedido ?? row.total ?? row.valor ?? 0;
      const status = row.status_codigo ?? row.status ?? row.situacao ?? row.sit ?? "---";
      const tabela = row.tabela_preco_nome ?? row.tabela ?? row.tabela_nome ?? "---";
      const fornecedor = row.fornecedor ?? row.fornecedor_nome ?? row.fornecedor_fantasia ?? "---";
      const link = row.link_url ?? row.link ?? row.pedido_link_url ?? null;
      const linkSent = row.link_enviado ?? row.link_status === "ENVIADO";

      const tr = document.createElement("tr");
      tr.classList.add("row-click");
      tr.dataset.id = id;

      // Badge visual
      const statusHtml = getStatusBadge(status);

      tr.innerHTML = `
          <td>${fmtDate(dataPedido)}</td>
          <td><a href="#" class="lnk-resumo" data-id="${id}">${id}</a></td>
          <td>${cliente}</td>
          <td><span class="badge badge-gray">${modalidade ?? "---"}</span></td>
          <td class="tar">${fmtMoney(valor)}</td>
          <td>${statusHtml}</td>
          <td>${tabela}</td>
          <td>${fornecedor}</td>
          <td>
            ${link
          ? `<div class="flex-gap">
                     <a class="btn" href="${link}" target="_blank" rel="noopener">Abrir</a>
                     <button class="btn-copy" data-url="${link}">${linkSent ? "Copiar (Enviado)" : "Copiar (Gerado)"}</button>
                   </div>`
          : "<span class='muted'>—</span>"
        }
          </td>
        `;

      tb.appendChild(tr);

      tr.addEventListener("click", (ev) => {
        if (ev.target.closest(".btn") || ev.target.closest("a") || ev.target.closest(".btn-copy")) return;
        openResumo(id);
      });
    } catch (err) {
      console.error("Erro renderizando linha:", row, err);
    }
  });
}


// ---------------------- paginação ----------------------
function renderPager() {
  const pageInfo = document.getElementById("pageInfo");
  const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
  pageInfo.textContent = `${state.page} / ${totalPages}`;

  document.getElementById("prevPage").disabled = state.page <= 1;
  document.getElementById("nextPage").disabled = state.page >= totalPages;
}

// ---------------------- drawer de resumo ----------------------
async function openResumo(id) {
  const r = await fetch(API.resumo(id), { cache: "no-store" });
  if (!r.ok) return;

  const p = await r.json();
  const el = document.getElementById("drawerContent");
  const modalidade = p.usar_valor_com_frete ? "ENTREGA" : "RETIRADA";

  el.innerHTML = `
    <div class="stack">
      <div class="kv">
        <div><b>Pedido:</b> ${p.id_pedido}</div>
        <div><b>Status:</b> ${p.status}</div>
      </div>

      <div class="kv">
        <div><b>Cliente:</b> ${p.cliente} (${p.codigo_cliente ?? "-"})</div>
        <div><b>Data:</b> ${fmtDate(p.created_at)}</div>
      </div>

      <div class="kv">
        <div><b>Modalidade:</b> ${modalidade}</div>
        <div><b>Tabela:</b> ${p.tabela_preco_nome ?? "-"}</div>
      </div>

      <div class="kv">
        <div><b>Fornecedor:</b> ${p.fornecedor ?? "-"}</div>
        <div><b>Total:</b> ${fmtMoney(p.total_pedido)}</div>
      </div>

      <div class="kv">
        <div><b>Contato:</b> ${p.contato_nome ?? "-"} • ${p.contato_email ?? "-"} • ${p.contato_fone ?? "-"}</div>
      </div>

      <div class="block">
        <b>Itens</b>
        <div class="itens">
          ${p.itens
      .map(
        (i) => `
            <div class="item">
              <div><b>${i.codigo}</b> — ${i.nome ?? ""} <small>${i.embalagem ?? ""}</small></div>
              <div>${i.quantidade} × ${fmtMoney(i.preco_unit)} = <b>${fmtMoney(
          i.subtotal
        )}</b></div>
            </div>
          `
      )
      .join("")}
        </div>
      </div>

      <div class="block">
        <b>Observações</b>
        <div class="obs">${p.observacoes ?? "-"}</div>
      </div>

      <div class="block">
        <b>Link</b>
        <div class="kv">
          <div class="truncate">${p.link_url ?? "-"}</div>
          ${p.link_url
      ? `<button id="copyResumo" class="btn">Copiar</button>`
      : ""
    }
        </div>
        <small>Status: ${p.link_status ?? "-"} • Primeiro acesso: ${fmtDate(
      p.link_primeiro_acesso_em
    )}</small>
      </div>
    </div>
  `;

  const btn = el.querySelector("#copyResumo");
  btn?.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(p.link_url);
      btn.textContent = "Copiado!";
      setTimeout(() => (btn.textContent = "Copiar"), 1500);
    } catch { }
  });

  document.getElementById("drawer").classList.remove("hidden");
}

// ---------------------- bind de eventos da tela ----------------------
function bindUI() {
  // busca
  const btnBuscar = document.getElementById("btnBuscar");
  if (btnBuscar) {
    btnBuscar.addEventListener("click", () => loadList(1));
  }

  // refresh
  const btnRefresh = document.getElementById("btnRefresh");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => loadList(state.page));
  }

  // limpar
  const btnLimpar = document.getElementById("btnLimpar");
  if (btnLimpar) {
    btnLimpar.addEventListener("click", limparFiltros);
  }

  // exportar
  const btnExport = document.getElementById("btnExport");
  if (btnExport) {
    btnExport.addEventListener("click", exportarCSV);
  }

  // paginação
  const btnPrev = document.getElementById("prevPage");
  if (btnPrev) {
    btnPrev.addEventListener("click", () => {
      if (state.page > 1) loadList(state.page - 1);
    });
  }

  const btnNext = document.getElementById("nextPage");
  if (btnNext) {
    btnNext.addEventListener("click", () => {
      const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
      if (state.page < totalPages) loadList(state.page + 1);
    });
  }

  // fechar drawer
  const btnClose = document.getElementById("btnCloseDrawer");
  if (btnClose) {
    btnClose.addEventListener("click", () => {
      document.getElementById("drawer").classList.add("hidden");
    });
  }

  // período rápido
  const periodoEl = document.getElementById("fPeriodoRapido");
  if (periodoEl) {
    periodoEl.addEventListener("change", aplicarPeriodoRapido);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const menuButton = document.getElementById('menu-button');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('overlay');
  if (!menuButton || !sidebar || !overlay) return;

  const open = () => { sidebar.classList.add('active'); overlay.style.display = 'block'; };
  const close = () => { sidebar.classList.remove('active'); overlay.style.display = 'none'; };

  menuButton.addEventListener('click', (e) => {
    e.stopPropagation();
    if (sidebar.classList.contains('active')) close(); else open();
  });

  overlay.addEventListener('click', close);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
});

// ---------------------- aplica período e já busca ----------------------
function aplicarPeriodoRapido() {
  const sel = document.getElementById("fPeriodoRapido");
  const val = sel.value; // "7","15","30","60","90","custom"

  // se for 'custom' deixa o usuário escolher a mão e não dispara loadList ainda
  if (val === "custom") {
    return;
  }

  const hoje = new Date();
  const inicio = addDays(hoje, -parseInt(val, 10));

  document.getElementById("fFrom").value = inicio.toISOString().slice(0, 10);
  document.getElementById("fTo").value = hoje.toISOString().slice(0, 10);

  // depois que atualiza as datas, já recarrega lista pág 1
  loadList(1);
}

// ---------------------- inicialização imediata ----------------------
// isso roda assim que o script é carregado (script está no final do body)
(async function init() {
  bindUI();
  await loadStatus();

  const periodoEl = document.getElementById("fPeriodoRapido");
  if (periodoEl) {
    // essa função já seta datas e chama loadList(1)
    aplicarPeriodoRapido();
  } else {
    // fallback se por algum motivo não tiver <select id="fPeriodoRapido">
    const hoje = new Date();
    const inicio = addDays(hoje, -30);
    document.getElementById("fFrom").value = inicio.toISOString().slice(0, 10);
    document.getElementById("fTo").value = hoje.toISOString().slice(0, 10);
    await loadList(1);
  }
})();

// ---------------------- eventos delegados na tabela ----------------------
// esse bloco precisa rodar AGORA também, não esperar DOMContentLoaded
(() => {
  const tb = document.getElementById("tblBody");
  if (!tb) return;

  tb.addEventListener("click", (ev) => {
    const a = ev.target.closest(".lnk-resumo");
    if (a) { ev.preventDefault(); openResumo(a.dataset.id); return; }
    const tr = ev.target.closest("tr.row-click");
    if (tr && !ev.target.closest(".btn") && !ev.target.closest("a")) {
      openResumo(tr.dataset.id);
    }
  });

  tb.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".btn-copy");
    if (!btn) return;
    const url = btn.getAttribute("data-url");
    navigator.clipboard.writeText(url).then(() => {
      btn.textContent = "Copiado!";
      setTimeout(() => (btn.textContent = "Copiar"), 1500);
    });
  });
})();


