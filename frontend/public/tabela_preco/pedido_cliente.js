// pedido_cliente.js

// -------------------- Helpers básicos --------------------
const url = new URL(window.location.href);

// preferir valores vindos do /p/{code} (definidos no HTML), senão cair no querystring
let tabelaIdParam = (typeof window.currentTabelaId !== "undefined" && window.currentTabelaId !== null)
  ? String(window.currentTabelaId)
  : url.searchParams.get("tabela_id");

let pedidoId = url.searchParams.get("id");
let produtos = [];
let usarValorComFrete = true;



// Caso a página tenha sido aberta como arquivo estático (ex.: pedido_cliente.html), evita pegar ".html" como id
if (pedidoId && pedidoId.includes(".html")) pedidoId = null;

const comFreteParamQS = url.searchParams.get("com_frete");
const comFreteFromCode = (typeof window.currentComFrete !== "undefined")
  ? (window.currentComFrete ? "true" : "false")
  : null;
const comFreteParam = comFreteFromCode ?? comFreteParamQS;

// Dados opcionais vindos do link
const razaoParam     = url.searchParams.get("razao_social");
const condPagtoParam = url.searchParams.get("cond_pagto");

const API_BASE = (typeof window !== "undefined" && window.API_BASE) ? window.API_BASE : location.origin;
const API = (p) => {
  const base = (typeof window !== "undefined" && window.API_BASE ? window.API_BASE : location.origin) || "";
  // remove barra final do base e garante que p tem barra inicial
  const normBase = base.replace(/\/+$/, "");
  const normPath = p.startsWith("/") ? p : `/${p}`;
  return `${normBase}${normPath}`;
};

const fmtBRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

// ---- Helpers para Data de Entrega/Retirada ----
function isISODate(s) {
  return typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s);
}

function formatarBR(iso) {
  if (!isISODate(iso)) return null;
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  // validação simples do objeto Date
  if (Number.isNaN(dt.getTime())) return null;
  return dt.toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

function normalizarEntregaISO(iso) {
  // Aceita apenas ISO e não permite data passada
  if (!isISODate(iso)) return null;
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  if (Number.isNaN(dt.getTime())) return null;

  const hoje = new Date();
  hoje.setHours(0,0,0,0);
  dt.setHours(0,0,0,0);
  if (dt < hoje) return null;

  return iso; // ok
}

function aplicarEntregaRetiradaHeader() {
  const entregaQS = new URLSearchParams(location.search).get("entrega");
  const entregaISO = normalizarEntregaISO(entregaQS);

  const labelEl = document.getElementById("labelEntregaRetirada");
  const valorEl = document.getElementById("dataEntregaValor");
  if (!labelEl || !valorEl) return;

  const label = (window.usarValorComFrete === true) ? "Data de entrega:" : "Data de retirada:";
  labelEl.textContent = label;

  if (entregaISO) {
    const br = formatarBR(entregaISO);
    valorEl.textContent = br || "a combinar";
  } else {
    valorEl.textContent = "a combinar";
  }
}

// -------------------- Elementos --------------------
const tbody         = document.querySelector("#tabelaProdutos tbody");
const totalEl       = document.getElementById("totalGeral");
const msgEl         = document.getElementById("mensagem");
const btnConfirmar  = document.getElementById("btnConfirmar");
const btnCancelar   = document.getElementById("btnCancelar");

// Observação do cliente – contador de caracteres
const taObs = document.getElementById('observacaoCliente');
const obsCounter = document.getElementById('obsCounter');

// -------------------- UI utils --------------------
function setMensagem(texto, ok = false) {
  if (!msgEl) return;
  msgEl.textContent = texto;
  msgEl.style.color = ok ? "green" : "red";
}

function atualizarObsCounter() {
  if (!taObs || !obsCounter) return;
  const len = (taObs.value || "").length;
  obsCounter.textContent = `${len}/244`;
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
      <td>${item.condicao_pagamento ?? ""}</td>
      <td class="celula-peso" data-peso-unit="${Number(item.peso ?? 0)}"></td>
      <td>${fmtBRL.format(valorUnitario)}</td>
      <td><input type="number" min="0" step="1" value="${item.quantidade || 1}" data-index="${i}" class="qtd" /></td>
      <td id="subtotal-${i}">${fmtBRL.format(subtotal)}</td>
    `;
    tbody.appendChild(tr);
    // Peso total inicial (peso unitário × quantidade inicial)
    const pesoUnit = Number(item.peso ?? 0);
    const qtdInicial = Number(item.quantidade) || 1;
    const pesoCell = tr.querySelector('.celula-peso');
      if (pesoCell) {
      const pesoTotal = pesoUnit * qtdInicial;
      pesoCell.textContent = (Number.isFinite(pesoTotal) ? pesoTotal : 0).toLocaleString('pt-BR');
      }
    
   
  });

  // Listeners de quantidade
  tbody.querySelectorAll("input.qtd").forEach((input) => {
    const handler = (e) => onQtdChange(e);
    input.addEventListener("input", handler);
    input.addEventListener("change", handler);
  });
  atualizarResumoFreteEPeso();
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
  
  // Atualizar peso total da linha (peso unitário × nova quantidade)
 const tr = e.target.closest('tr');
 const pesoCell = tr?.querySelector('.celula-peso');
 if (pesoCell) {
   const pesoUnit = Number(pesoCell.dataset.pesoUnit || produtos[idx].peso || 0);
   const pesoTotal = pesoUnit * quantidade;
   pesoCell.textContent = (Number.isFinite(pesoTotal) ? pesoTotal : 0).toLocaleString('pt-BR');
  }

  atualizarTotal();
  atualizarResumoFreteEPeso();
}

function atualizarTotal() {
  const total = produtos.reduce((acc, item) => {
    const v = usarValorComFrete ? item.valor_com_frete : item.valor_sem_frete;
    return acc + v * (Number(item.quantidade) || 0);
  }, 0);
  if (totalEl) totalEl.textContent = fmtBRL.format(total);
  if (btnConfirmar) btnConfirmar.disabled = total <= 0;
}

function atualizarResumoFreteEPeso() {
  const tbody = document.querySelector('#tabelaProdutos tbody');
  if (!tbody) return;

  let pesoTotal = 0;
  let freteTotal = 0;

  // usa o mesmo array 'produtos' já usado para render (presente no seu JS)
  const linhas = tbody.querySelectorAll('tr');
  linhas.forEach((tr, idx) => {
    // quantidade
    const qtdInput = tr.querySelector('input.qtd');
    const qtd = Math.max(0, Number(qtdInput?.value) || 0);

    // peso unitário (guardado na célula .celula-peso como data-attribute)
    const pesoUnit = Number(tr.querySelector('.celula-peso')?.dataset.pesoUnit || 0);
    pesoTotal += pesoUnit * qtd;

    // frete por item (diferença entre valores) — só soma quando estiver em "com frete"
    if (window.usarValorComFrete === true) {
      const valorCom = Number((produtos[idx]?.valor_com_frete) || 0);
      const valorSem = Number((produtos[idx]?.valor_sem_frete) || 0);
      const delta = Math.max(valorCom - valorSem, 0);
      freteTotal += delta * qtd;
    }
  });

  // escreve na tela
  const elPeso = document.getElementById('totalPesoPedido');
  const elFrete = document.getElementById('totalFretePedido');
  if (elPeso) elPeso.textContent = (Number.isFinite(pesoTotal) ? pesoTotal : 0).toLocaleString('pt-BR');
  if (elFrete) elFrete.textContent = window.usarValorComFrete === true ? fmtBRL.format(freteTotal) : fmtBRL.format(0);
}



function obterParametrosPedido() {
  const qs = new URLSearchParams(location.search);
  let tabelaId = qs.get("tabela_id") || window.currentTabelaId;
  let comFrete = qs.get("com_frete");

  if (comFrete === null || comFrete === undefined) comFrete = window.currentComFrete;

  comFrete = String(comFrete).toLowerCase() === "true";
  if (!tabelaId) throw new Error("sem_parametros");

  return { tabelaId: Number(tabelaId), comFrete };
}

// -------------------- Carregamento de dados --------------------
async function carregarPedido() {
  try {
    const _qsNow = new URLSearchParams(location.search);

    tabelaIdParam = tabelaIdParam
    || _qsNow.get("tabela_id")
    || (typeof window.currentTabelaId !== "undefined" ? String(window.currentTabelaId) : null);

    const _comFreteQS   = _qsNow.get("com_frete");
    const _comFreteCode = (typeof window.currentComFrete !== "undefined")
    ? (window.currentComFrete ? "true" : "false")
    : null;

    // valor efetivo de com_frete (prioriza query; se não houver, usa o do resolver)
    const _comFreteEfetivo = (_comFreteQS ?? _comFreteCode);
    // Fluxo 1: veio de criação/listagem com ?tabela_id=... (preview)
    if (tabelaIdParam) {
      // 1A) Preview dos itens (sem validade aqui)
      // 1A) Preview dos itens (sem validade aqui)
      const qs = new URLSearchParams({
        tabela_id: tabelaIdParam,
        com_frete: (_comFreteEfetivo === "1" || String(_comFreteEfetivo).toLowerCase() === "true") ? "true" : "false",
        razao_social: razaoParam || "",
        condicao_pagamento: condPagtoParam || ""
      });

      // 🔎 LOGA a URL completa que será chamada
      const previewURL = `/pedido/preview?${qs.toString()}`;
      console.debug("[preview] URL:", previewURL);

      const r1 = await fetch(API(`/pedido/preview?${qs.toString()}`));
      
      if (!r1.ok) {
        let detail = "";
        try {
          const err = await r1.json();
          detail = err?.detail || JSON.stringify(err);
        } catch (_) {}
        throw new Error(`Erro ${r1.status} no preview${detail ? " — " + detail : ""}`);
      }

      const dados = await r1.json();

      // Preencher cabeçalho (sem validade ainda)
      setCampoTexto("razaoSocialCliente", dados.razao_social ?? "---");
      setCampoTexto("condicaoPagamento", dados.condicao_pagamento ?? "---");

      // Usar c/ ou s/ frete decidido no link
      usarValorComFrete = Boolean(dados.usar_valor_com_frete);
      setCampoTexto("tituloValorFrete", usarValorComFrete ? "c/ Frete" : "s/ Frete");
      window.usarValorComFrete = !!dados.usar_valor_com_frete;
      aplicarEntregaRetiradaHeader();
      // Itens
      produtos = (dados.produtos || []).map(p => ({
        ...p,
        valor_com_frete: Number(p.valor_com_frete) || 0,
        valor_sem_frete: Number(p.valor_sem_frete) || 0,
        quantidade: Number(p.quantidade) || 1
      }));
      renderTabela();
      atualizarResumoFreteEPeso();
      atualizarTotal();

      // 1B) Validade global (busca direto no front)
      try {
        const r2 = await fetch(API(`/tabela_preco/meta/validade_global?tabela_id=${encodeURIComponent(tabelaIdParam)}`));

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
            quantidade: Number(p.quantidade) || 1,
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
    const itens = produtos;
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
        body: JSON.stringify({usar_valor_com_frete: usarValorComFrete,
        produtos: itens,
        observacao: (document.getElementById('observacaoCliente')?.value || '').trim().slice(0, 244)
      }),
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
        body: JSON.stringify({
        produtos: itens,
        observacao: (document.getElementById('observacaoCliente')?.value || '').trim().slice(0, 244)}),
      });
      if (resp.ok) {
        setMensagem("Pedido confirmado! O PDF será enviado para a empresa.", true);
      } else {
        const txt = await resp.text();
        throw new Error(`Falha na confirmação: ${resp.status} - ${txt}`);
      }
      return;
    }

     const observacao = (document.getElementById('observacaoCliente')?.value || '').trim();

     // ... seu body existente
     const body = {
     usar_valor_com_frete: !!window.usarValorComFrete,
     produtos: produtos.map(p => ({
     codigo: p.codigo,
     quantidade: Number(p.quantidade) || 0,
     // (mantenha os campos que você já envia)
     })),
     // ✅ novo campo:
     observacao: observacao.slice(0, 244)
     };


    // Se chegou aqui, não tinha nem tabelaIdParam nem pedidoId
    setMensagem("Não foi possível confirmar: parâmetro ausente (tabela_id ou id).", false);
  } catch (e) {
    console.error(e);
    setMensagem("Erro ao confirmar pedido. Tente novamente.", false);
  } finally {
    if (btnConfirmar) btnConfirmar.disabled = false;
  }
}

    const observacao = (document.getElementById('observacaoCliente')?.value || '').trim();

    // ... seu body existente
    const body = {
      usar_valor_com_frete: !!window.usarValorComFrete,
      produtos: produtos.map(p => ({
        codigo: p.codigo,
        quantidade: Number(p.quantidade) || 0,
        // (mantenha os campos que você já envia)
      })),
      // ✅ novo campo:
      observacao: observacao.slice(0, 244)
    };

function assertShape(d) {
  const must = [
    ["tabela", "object"],
    ["tabela.nome", "string"],
    ["tabela.validade", "string"], // ajuste aos seus campos reais
    ["cliente", "object"],
    ["cliente.nome", "string"],
    ["itens", "object"], // array
  ];
  const get = (o, path) => path.split(".").reduce((a,k)=> (a && a[k]!==undefined ? a[k] : undefined), o);
  const errs = [];
  for (const [p, t] of must) {
    const v = get(d, p);
    if (t === "object" && (typeof v !== "object" || v === null)) errs.push(`${p} ausente`);
    if (t === "string" && typeof v !== "string") errs.push(`${p} inválido`);
  }
  if (Array.isArray(d.itens) === false) errs.push("itens não é array");
  if (errs.length) {
    console.error("[pedido] shape inválido:", errs, d);
    alert("Formato de dados inesperado para a tela de pedido.");
  }
}


function cancelarPedido() {
  if (window.opener) {
    window.close();
  } else if (history.length > 1) {
    history.back();
  } else {
    window.location.href = "/";
 }
}

// -------------------- Bind de eventos e início --------------------
if (btnConfirmar) btnConfirmar.addEventListener("click", confirmarPedido);
if (btnCancelar)  btnCancelar.addEventListener("click", cancelarPedido);

window.carregarPedido = carregarPedido;

if (taObs) {
  taObs.addEventListener('input', atualizarObsCounter);
  atualizarObsCounter(); // inicia contador
}