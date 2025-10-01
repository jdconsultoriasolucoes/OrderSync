// pedido_cliente.js

// -------------------- Helpers básicos --------------------
const url = new URL(window.location.href);

// preferir valores vindos do /p/{code} (definidos no HTML), senão cair no querystring
let tabelaIdParam = (typeof window.currentTabelaId !== "undefined" && window.currentTabelaId !== null)
  ? String(window.currentTabelaId)
  : url.searchParams.get("tabela_id");

let pedidoId = url.searchParams.get("id");


// Caso a página tenha sido aberta como arquivo estático (ex.: pedido_cliente.html), evita pegar ".html" como id
if (pedidoId && pedidoId.includes(".html")) pedidoId = null;

const comFreteParamQS = url.searchParams.get("com_frete");
const comFreteFromCode = (typeof window.currentComFrete !== "undefined")
  ? (window.currentComFrete ? "true" : "false")
  : null;
const comFreteParam = comFreteFromCode ?? comFreteParamQS;

// Dados opcionais vindos do link
const cnpjParam      = url.searchParams.get("cnpj");
const razaoParam     = url.searchParams.get("razao_social");
const condPagtoParam = url.searchParams.get("cond_pagto");

const API_BASE = window.API_BASE || "";
const API = (p) => API_BASE + (p.startsWith("/") ? p : "/" + p);

const fmtBRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

// -------------------- Estado da tela --------------------
let produtos = [];
let usarValorComFrete = true;

// -------------------- Elementos --------------------
const tbody         = document.querySelector("#tabelaProdutos tbody");
const totalEl       = document.getElementById("totalGeral");
const msgEl         = document.getElementById("mensagem");
const btnConfirmar  = document.getElementById("btnConfirmar");
const btnCancelar   = document.getElementById("btnCancelar");

// -------------------- UI utils --------------------
function setMensagem(texto, ok = false) {
  if (!msgEl) return;
  msgEl.textContent = texto;
  msgEl.style.color = ok ? "green" : "red";
}

function renderTabela() {
  if (!tbody) return;
  tbody.innerHTML = "";
  produtos.forEach((item, i) => {
    const valorUnitario = usarValorComFrete ? item.valor_com_frete : item.valor_sem_frete;
    const subtotal = valorUnitario * (Number(item.quantidade) || 0);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.codigo ?? ""}</td>
      <td>${item.nome ?? ""}</td>
      <td>${item.embalagem ?? ""}</td>
      <td>${item.peso ?? ""}</td>
      <td>${fmtBRL.format(valorUnitario)}</td>
      <td><input type="number" min="0" step="1" value="${item.quantidade || 0}" data-index="${i}" class="qtd" /></td>
      <td id="subtotal-${i}">${fmtBRL.format(subtotal)}</td>
    `;
    tbody.appendChild(tr);
  });

  // Listeners de quantidade
  tbody.querySelectorAll("input.qtd").forEach((input) => {
    const handler = (e) => onQtdChange(e);
    input.addEventListener("input", handler);
    input.addEventListener("change", handler);
  });
}

function onQtdChange(e) {
  const idx = Number(e.target.dataset.index);
  let quantidade = Math.max(0, Number(e.target.value) || 0);
  e.target.value = quantidade;
  produtos[idx].quantidade = quantidade;

  const valorUnitario = usarValorComFrete
    ? produtos[idx].valor_com_frete
    : produtos[idx].valor_sem_frete;

  const subtotal = quantidade * valorUnitario;
  const cell = document.getElementById(`subtotal-${idx}`);
  if (cell) cell.textContent = fmtBRL.format(subtotal);

  atualizarTotal();
}

function atualizarTotal() {
  const total = produtos.reduce((acc, item) => {
    const v = usarValorComFrete ? item.valor_com_frete : item.valor_sem_frete;
    return acc + v * (Number(item.quantidade) || 0);
  }, 0);
  if (totalEl) totalEl.textContent = fmtBRL.format(total);
  if (btnConfirmar) btnConfirmar.disabled = total <= 0;
}

// -------------------- Carregamento de dados --------------------
async function carregarPedido() {
  try {
    // Fluxo 1: veio de criação/listagem com ?tabela_id=... (preview)
    if (tabelaIdParam) {
      // 1A) Preview dos itens (sem validade aqui)
      const qs = new URLSearchParams({
        tabela_id: tabelaIdParam,
        com_frete: (comFreteParam === "1" || comFreteParam === "true") ? "true" : "false",
        cnpj: cnpjParam || "",
        razao_social: razaoParam || "",
        condicao_pagamento: condPagtoParam || ""
      });
      const r1 = await fetch(API(`/pedido/preview?${qs.toString()}`));
      if (!r1.ok) throw new Error(`Erro ${r1.status} no preview`);
      const dados = await r1.json();

      // Preencher cabeçalho (sem validade ainda)
      setCampoTexto("cnpjCliente", dados.cnpj ?? "---");
      setCampoTexto("razaoSocialCliente", dados.razao_social ?? "---");
      setCampoTexto("condicaoPagamento", dados.condicao_pagamento ?? "---");

      // Usar c/ ou s/ frete decidido no link
      usarValorComFrete = Boolean(dados.usar_valor_com_frete);
      setCampoTexto("tituloValorFrete", usarValorComFrete ? "c/ Frete" : "s/ Frete");

      // Itens
      produtos = (dados.produtos || []).map(p => ({
        ...p,
        valor_com_frete: Number(p.valor_com_frete) || 0,
        valor_sem_frete: Number(p.valor_sem_frete) || 0,
        quantidade: Number(p.quantidade) || 0
      }));
      renderTabela();
      atualizarTotal();

      // 1B) Validade global (busca direto no front)
      try {
        const r2 = await fetch(API(`/tabela_preco/validade_global?tabela_id=${encodeURIComponent(tabelaIdParam)}`));
        if (r2.ok) {
          const v = await r2.json();
          setCampoTexto("validadeTabela", v.validade ?? "---");
          setCampoTexto("tempoRestante",  v.tempo_restante ?? "---");
        } else {
          setCampoTexto("validadeTabela", "---");
          setCampoTexto("tempoRestante",  "---");
        }
      } catch {
        setCampoTexto("validadeTabela", "---");
        setCampoTexto("tempoRestante",  "---");
      }

      return;
    }

    // Fluxo 2: (opcional) se vier por ?id=<pedidoId>, buscar um pedido existente
    if (pedidoId) {
      const resp = await fetch(API(`/pedido/${encodeURIComponent(pedidoId)}`));
      if (!resp.ok) throw new Error(`Erro ${resp.status} ao carregar pedido`);
      const dados = await resp.json();

      setCampoTexto("cnpjCliente", dados.cnpj ?? "---");
      setCampoTexto("razaoSocialCliente", dados.razao_social ?? "---");
      setCampoTexto("condicaoPagamento", dados.condicao_pagamento ?? "---");
      setCampoTexto("validadeTabela",   dados.validade ?? "---");
      setCampoTexto("tempoRestante",    dados.tempo_restante ?? "---");

      usarValorComFrete = Boolean(dados.usar_valor_com_frete);
      setCampoTexto("tituloValorFrete", usarValorComFrete ? "c/ Frete" : "s/ Frete");

      produtos = Array.isArray(dados.produtos)
        ? dados.produtos.map((p) => ({
            ...p,
            valor_com_frete: Number(p.valor_com_frete) || 0,
            valor_sem_frete: Number(p.valor_sem_frete) || 0,
            quantidade: Number(p.quantidade) || 0,
          }))
        : [];

      renderTabela();
      atualizarTotal();
      return;
    }

    // Nenhum parâmetro reconhecido
    setMensagem("URL sem parâmetros válidos. Use ?tabela_id=<id> (preview) ou ?id=<pedido>.");
    if (btnConfirmar) btnConfirmar.disabled = true;
  } catch (e) {
    console.error(e);
    setMensagem("Não foi possível carregar os dados do pedido.");
    if (btnConfirmar) btnConfirmar.disabled = true;
  }
}

// Pequeno util pra preencher elementos de texto por id
function setCampoTexto(id, valor) {
  const el = document.getElementById(id);
  if (el) el.textContent = valor;
}

// -------------------- Ações --------------------
async function confirmarPedido() {
  try {
    const itens = produtos.filter((p) => (Number(p.quantidade) || 0) > 0);
    if (itens.length === 0) {
      setMensagem("Inclua pelo menos 1 item com quantidade > 0.", false);
      return;
    }

    if (btnConfirmar) btnConfirmar.disabled = true;
    setMensagem("Enviando pedido...", true);

    // Quando vier por preview de tabela, podemos confirmar para um endpoint próprio (ajuste quando existir)
    if (tabelaIdParam) {
      const resp = await fetch(API(`/tabela_preco/${encodeURIComponent(tabelaIdParam)}/confirmar_pedido`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usar_valor_com_frete: usarValorComFrete, produtos: itens }),
      });
      if (resp.ok) {
        setMensagem("Pedido confirmado! O PDF será enviado para a empresa.", true);
      } else {
        const txt = await resp.text();
        throw new Error(`Falha na confirmação: ${resp.status} - ${txt}`);
      }
      return;
    }

    // Fluxo alternativo (se já existir pedido_id):
    if (pedidoId) {
      const resp = await fetch(API(`/pedido/${encodeURIComponent(pedidoId)}/confirmar`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ produtos: itens }),
      });
      if (resp.ok) {
        setMensagem("Pedido confirmado! O PDF será enviado para a empresa.", true);
      } else {
        const txt = await resp.text();
        throw new Error(`Falha na confirmação: ${resp.status} - ${txt}`);
      }
      return;
    }

    // Se chegou aqui, não tinha nem tabelaIdParam nem pedidoId
    setMensagem("Não foi possível confirmar: parâmetro ausente (tabela_id ou id).", false);
  } catch (e) {
    console.error(e);
    setMensagem("Erro ao confirmar pedido. Tente novamente.", false);
  } finally {
    if (btnConfirmar) btnConfirmar.disabled = false;
  }
}

function cancelarPedido() {
  window.location.href = "/";
}

// -------------------- Bind de eventos e início --------------------
if (btnConfirmar) btnConfirmar.addEventListener("click", confirmarPedido);
if (btnCancelar)  btnCancelar.addEventListener("click", cancelarPedido);

carregarPedido();
