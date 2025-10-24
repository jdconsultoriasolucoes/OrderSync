// base do backend FastAPI publicado no Render
const API_BASE = "https://ordersync-backend-edjq.onrender.com";

const API = {
  list:   `${API_BASE}/api/pedidos`,
  status: `${API_BASE}/api/pedidos/status`,
  resumo: (id) => `${API_BASE}/api/pedidos/${id}/resumo`,
};


let state = { page: 1, pageSize: 25, total: 0 };

function fmtMoney(v) {
  if (v == null) return "---";
  try { return Number(v).toLocaleString("pt-BR",{style:"currency",currency:"BRL"}); }
  catch { return v; }
}
function fmtDate(s) {
  if (!s) return "---";
  const d = new Date(s);
  const dt = d.toLocaleDateString("pt-BR");
  const hr = d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return `${dt} ${hr}`;
}

async function loadStatus() {
  const r = await fetch(API.status, { cache: "no-store" });
  if (!r.ok) {
    console.error("Falha ao carregar status:", r.status, await r.text());
    return;
  }
  const j = await r.json();
  const sel = document.getElementById("fStatus");
  sel.innerHTML = "";
  j.data.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s.codigo;
    opt.textContent = s.rotulo || s.codigo;
    sel.appendChild(opt);
  });
}

function getFilters() {
  const fFrom = document.getElementById("fFrom").value;
  const fTo = document.getElementById("fTo").value;
  const fTabela = document.getElementById("fTabela").value || null;
  const fCliente = document.getElementById("fCliente").value || null;
  const fFornecedor = document.getElementById("fFornecedor").value || null;
  const selStatus = Array.from(document.getElementById("fStatus").selectedOptions).map(o => o.value);
  return { fFrom, fTo, fTabela, fCliente, fFornecedor, selStatus };
}

async function loadList(page = 1) {
  state.page = page;
  const { fFrom, fTo, fTabela, fCliente, fFornecedor, selStatus } = getFilters();

  // Se datas vazias, usa hoje como fallback
  if (!fFrom || !fTo) {
    const today = new Date().toISOString().slice(0,10);
    document.getElementById("fFrom").value = fFrom || today;
    document.getElementById("fTo").value   = fTo   || today;
  }

  const params = new URLSearchParams();
  params.set("from", document.getElementById("fFrom").value); // só "YYYY-MM-DD"
  params.set("to",   document.getElementById("fTo").value);   // só "YYYY-MM-DD"
  if (selStatus.length) params.set("status", selStatus.join(",")); // "ABERTO,CONFIRMADO"
  if (fTabela)     params.set("tabela_nome", fTabela);
  if (fCliente)    params.set("cliente", fCliente);
  if (fFornecedor) params.set("fornecedor", fFornecedor);
  params.set("page", state.page);
  params.set("pageSize", state.pageSize);

  const url = `${API.list}?${params.toString()}`;

  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) {
    console.error("Falha ao carregar pedidos:", r.status, await r.text());
    return;
  }

  const j = await r.json();
  state.total = j.total;
  renderTable(j.data);
  renderPager();
}

function renderTable(rows) {
  const tb = document.getElementById("tblBody");
  tb.innerHTML = "";
  rows.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${fmtDate(row.data_pedido)}</td>
      <td><button class="btn-link" data-id="${row.numero_pedido}">${row.numero_pedido}</button></td>
      <td>${row.cliente_nome ?? "---"}</td>
      <td><span class="badge">${row.modalidade}</span></td>
      <td class="tar">${fmtMoney(row.valor_total)}</td>
      <td>${row.status_codigo}</td>
      <td>${row.tabela_preco_nome ?? "---"}</td>
      <td>${row.fornecedor ?? "---"}</td>
      <td>
        ${row.link_url
          ? `<button class="btn-copy" data-url="${row.link_url}">${row.link_enviado ? "Enviado" : "Gerado"}</button>`
          : "<span class='muted'>—</span>"
        }
      </td>
    `;
    tb.appendChild(tr);
  });

  // bind actions
  tb.querySelectorAll(".btn-link").forEach(btn => {
    btn.addEventListener("click", () => openResumo(btn.dataset.id));
  });
  tb.querySelectorAll(".btn-copy").forEach(btn => {
    btn.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(btn.dataset.url);
        btn.textContent = "Copiado!"; setTimeout(()=>btn.textContent="Copiar",1500);
      } catch { alert("Não foi possível copiar o link."); }
    });
  });
}

function renderPager() {
  const pageInfo = document.getElementById("pageInfo");
  const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
  pageInfo.textContent = `${state.page} / ${totalPages}`;
  document.getElementById("prevPage").disabled = state.page <= 1;
  document.getElementById("nextPage").disabled = state.page >= totalPages;
}

async function openResumo(id) {
  const r = await fetch(API.resumo(id), { cache: "no-store" });
  if (!r.ok) return;
  const p = await r.json();
  const el = document.getElementById("drawerContent");
  const modalidade = p.usar_valor_com_frete ? "ENTREGA" : "RETIRADA";

  el.innerHTML = `
    <div class="stack">
      <div class="kv"><div><b>Pedido:</b> ${p.id_pedido}</div><div><b>Status:</b> ${p.status}</div></div>
      <div class="kv"><div><b>Cliente:</b> ${p.cliente} (${p.codigo_cliente ?? "-"})</div><div><b>Data:</b> ${fmtDate(p.created_at)}</div></div>
      <div class="kv"><div><b>Modalidade:</b> ${modalidade}</div><div><b>Tabela:</b> ${p.tabela_preco_nome ?? "-"}</div></div>
      <div class="kv"><div><b>Fornecedor:</b> ${p.fornecedor ?? "-"}</div><div><b>Total:</b> ${fmtMoney(p.total_pedido)}</div></div>
      <div class="kv"><div><b>Contato:</b> ${p.contato_nome ?? "-"} • ${p.contato_email ?? "-"} • ${p.contato_fone ?? "-"}</div></div>
      <div class="block">
        <b>Itens</b>
        <div class="itens">
          ${p.itens.map(i => `
            <div class="item">
              <div><b>${i.codigo}</b> — ${i.nome ?? ""} <small>${i.embalagem ?? ""}</small></div>
              <div>${i.quantidade} × ${fmtMoney(i.preco_unit)} = <b>${fmtMoney(i.subtotal)}</b></div>
            </div>
          `).join("")}
        </div>
      </div>
      <div class="block"><b>Observações</b><div class="obs">${p.observacoes ?? "-"}</div></div>
      <div class="block">
        <b>Link</b>
        <div class="kv">
          <div class="truncate">${p.link_url ?? "-"}</div>
          ${p.link_url ? `<button id="copyResumo" class="btn">Copiar</button>` : ""}
        </div>
        <small>Status: ${p.link_status ?? "-"} • Primeiro acesso: ${fmtDate(p.link_primeiro_acesso_em)}</small>
      </div>
    </div>
  `;

  const btn = el.querySelector("#copyResumo");
  btn?.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(p.link_url); btn.textContent = "Copiado!"; setTimeout(()=>btn.textContent="Copiar",1500);} catch {}
  });

  document.getElementById("drawer").classList.remove("hidden");
}

function bindUI() {
  document.getElementById("btnBuscar").addEventListener("click", () => loadList(1));
  document.getElementById("prevPage").addEventListener("click", () => { if (state.page>1) loadList(state.page-1); });
  document.getElementById("nextPage").addEventListener("click", () => {
    const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
    if (state.page < totalPages) loadList(state.page+1);
  });
  document.getElementById("btnCloseDrawer").addEventListener("click", () => {
    document.getElementById("drawer").classList.add("hidden");
  });
   const periodoEl = document.getElementById("fPeriodoRapido");
  if (periodoEl) {
    periodoEl.addEventListener("change", aplicarPeriodoRapido);
  }

  // botão "Buscar" manual (se existir)
  const btnBuscar = document.getElementById("btnBuscar");
  if (btnBuscar) {
    btnBuscar.addEventListener("click", () => loadList(1));
  }
}

function addDays(baseDate, days) {
  const d = new Date(baseDate);
  d.setDate(d.getDate() + days);
  return d;
}

function addDays(baseDate, days) {
  const d = new Date(baseDate);
  d.setDate(d.getDate() + days);
  return d;
}

(async function init(){
  bindUI();
  await loadStatus();

  // garante período inicial (30 dias porque está selected no HTML)
  const periodoEl = document.getElementById("fPeriodoRapido");
  if (periodoEl) {
    aplicarPeriodoRapido();
  } else {
    // fallback (caso o select não esteja no HTML ainda)
    const hoje = new Date();
    const inicio = addDays(hoje, -30);
    document.getElementById("fFrom").value = inicio.toISOString().slice(0,10);
    document.getElementById("fTo").value   = hoje.toISOString().slice(0,10);
    await loadList(1);
  }
})();

function aplicarPeriodoRapido() {
  const sel = document.getElementById("fPeriodoRapido");
  const val = sel.value; // "7", "15", "30", "60", "90", ou "custom"

  // se for custom, não mexe nos campos de data, o usuário vai escolher
  if (val === "custom") {
    return;
  }

  const hoje = new Date();
  const inicio = addDays(hoje, -parseInt(val, 10));

  document.getElementById("fFrom").value = inicio.toISOString().slice(0,10);
  document.getElementById("fTo").value   = hoje.toISOString().slice(0,10);

  // depois que atualiza as datas, já recarrega a lista página 1
  loadList(1);
}