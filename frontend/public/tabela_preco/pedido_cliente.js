// pedido_cliente.js

// -------------------- Helpers básicos --------------------
const url = new URL(window.location.href);

// Modo interno (prévia via "Visualizar")
const IS_MODO_INTERNO = new URLSearchParams(location.search).get("modo") === "interno" || location.hash.replace("#","") === "interno";;
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
  if (Number.isNaN(dt.getTime())) return null;
  return dt.toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo" });
}
function normalizarEntregaISO(iso) {
  if (!isISODate(iso)) return null;
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  if (Number.isNaN(dt.getTime())) return null;
  const hoje = new Date(); hoje.setHours(0,0,0,0);
  dt.setHours(0,0,0,0);
  // regra atual: aceitar passado também mostra "a combinar"? 
  // Se quiser bloquear passado, descomente abaixo:
  if (dt < hoje) return null;
  return iso;
}

function brToISO(br) {
  // "31/12/2025" -> "2025-12-31"
  if (typeof br !== "string") return null;
  const m = br.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  return m ? `${m[3]}-${m[2]}-${m[1]}` : null;
}
function normalizarValidadeCampo(x) {
  if (!x) return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(x)) return x; // já é ISO
  return brToISO(x); // tenta converter BR -> ISO
}


function aplicarEntregaRetiradaHeader() {
  const labelEl = document.getElementById("labelEntregaRetirada");
  const valorEl = document.getElementById("dataEntregaValor");
  if (!labelEl || !valorEl) return;

  const label = (window.usarValorComFrete === true)
    ? "Data de entrega:"
    : "Data de retirada:";
  labelEl.textContent = label;

  const iso = (typeof window.entregaISO === "string" && isISODate(window.entregaISO))
    ? window.entregaISO
    : null;

  valorEl.textContent = iso ? (formatarBR(iso) || "a combinar") : "a combinar";
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
    
    const pathParts = location.pathname.split('/').filter(Boolean);
    const lastPart = pathParts[pathParts.length - 1];
    if (pathParts[0] === 'p' && lastPart) {
      try {
        const r = await fetch(`/link_pedido/resolver?code=${encodeURIComponent(lastPart)}`, { cache: "no-store" });
        if (r.ok) {
          const info = await r.json();
          window.currentTabelaId = info.tabela_id ?? window.currentTabelaId;
          window.currentComFrete = info.com_frete ?? window.currentComFrete;
          window.codigoClienteHidden = info.codigo_cliente || null;  // <— oculto
        }
      } catch {}
    }


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
      
      window.usarValorComFrete = usarValorComFrete;
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
          setCampoTexto("validadeTabela", v.validade ?? v.validade_tabela ?? "---");
          setCampoTexto("tempoRestante",  v.tempo_restante ?? "---");
          const rawVal = v.validade ?? v.validade_tabela ?? null;
          window.validadeGlobalISO = normalizarValidadeCampo(rawVal);
          console.debug("[validade] raw:", rawVal, "ISO:", window.validadeGlobalISO);
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

      window.usarValorComFrete = usarValorComFrete;
      aplicarEntregaRetiradaHeader();

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

function obterValidadeDiasDaTela() {
  const el = document.getElementById("tempoRestante");
  if (!el) return null;
  const m = (el.textContent || "").match(/(\d+)/);
  return m ? parseInt(m[1], 10) : null;
}
//Bloqueia tela depois de confirmar pedido
function lockPageAfterConfirm() {
  // Desabilita todos os elementos interativos da página (menos o botão do modal)
  document.body.classList.add('page-locked');
  document.querySelectorAll('input, textarea, select, button').forEach(el => {
    if (el.id === 'btnFecharConfirm') return;
    el.disabled = true;
  });
  // Também evita scroll enquanto o modal estiver aberto
  document.body.classList.add('modal-open');
}

function openConfirmModal(pedidoId) {
  const modal = document.getElementById('confirmModal');
  const info  = document.getElementById('confirmPedidoInfo');
  if (!modal) return;

  info.textContent = pedidoId ? `Número do pedido: ${pedidoId}` : '';
  modal.hidden = false;

  // Trava a página para não permitir mais modificações
  lockPageAfterConfirm();

  // Foco no botão para acessibilidade
  const btn = document.getElementById('btnFecharConfirm');
  btn && btn.focus();
}

function closeConfirmModal() {
  const modal = document.getElementById('confirmModal');
  if (!modal) return;
  modal.hidden = true;
  // Mantém a página travada mesmo após fechar o pop-up (conforme solicitado)
  document.body.classList.remove('modal-open'); // só libera o scroll do pop-up
}

// -------------------- Ações --------------------
async function confirmarPedido() {
  try {
    const itens = produtos;
    if (!Array.isArray(itens) || itens.length === 0) {
      setMensagem("Inclua pelo menos 1 item com quantidade > 0.", false);
      return;
    }

    if (btnConfirmar) btnConfirmar.disabled = true;
    setMensagem("Enviando pedido...", true);

    // token do link curto (/p/{code})
    const originCode = location.pathname.split('/').pop() || null;

    // razão social mostrada na tela
    const clienteRazao = (document.getElementById('razaoSocialCliente')?.textContent || '').trim() || null;

    // observação limitada a 244 chars
    const observacao = (document.getElementById('observacaoCliente')?.value || '').trim().slice(0, 244);

    const entregaQS = new URLSearchParams(location.search).get("entrega");
    const dataRetiradaISO = (typeof entregaQS === "string" && isISODate(entregaQS)) ? entregaQS : null;

    // pega a validade que guardamos ao carregar a tela
    const validadeISO = (typeof window.validadeGlobalISO === "string" && isISODate(window.validadeGlobalISO))
      ? window.validadeGlobalISO
      : null;

    // CHAMADA ao backend: agora usamos /pedido/{tabela_id}/confirmar
    const resp = await fetch(API(`/pedido/${encodeURIComponent(tabelaIdParam)}/confirmar`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify({
        origin_code: originCode,
        usar_valor_com_frete: !!usarValorComFrete,
        produtos: itens.map(x => ({
          codigo: x.codigo,
          quantidade: Number(x.quantidade || 0),
          preco_unit: x.preco_unit ?? x.valor_sem_frete ?? 0,
          preco_unit_com_frete: x.preco_unit_com_frete ?? x.valor_com_frete ?? x.preco_unit ?? 0,
          peso_kg: x.peso ?? x.peso_kg ?? null
        })),
        observacao,
        cliente: clienteRazao,
        validade_ate: (typeof window.validadeGlobalISO === "string" && isISODate(window.validadeGlobalISO)) ? window.validadeGlobalISO : null,
        data_retirada: dataRetiradaISO,
        validade_dias: obterValidadeDiasDaTela(),
        codigo_cliente: (typeof window.codigoClienteHidden === "string" ? window.codigoClienteHidden : null),
        link_url: location.href
      })
    });

    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`Erro ao confirmar (${resp.status}) ${txt || ''}`);
    }

    const data = await resp.json();
    const pedidoIdConfirmado = data?.id;

    if (!pedidoIdConfirmado) {
      throw new Error("Resposta sem id do pedido.");
    }

    openConfirmModal(pedidoIdConfirmado);

  } catch (err) {
    console.error('[confirmarPedido] erro', err);
    alert("Não foi possível confirmar o pedido. Tente novamente.");
    setMensagem("Falha ao enviar o pedido.", false);
    if (btnConfirmar) btnConfirmar.disabled = false;
  }
}

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


function aplicarModoInterno() {
  if (!IS_MODO_INTERNO) return;

  // Esconde "Confirmar"
  document.getElementById("btnConfirmar")?.style.setProperty("display","none");

  // "Cancelar" -> "Voltar" com override total de listeners
  const oldBtn = document.getElementById("btnCancelar");
  if (oldBtn) {
    const newBtn = oldBtn.cloneNode(true);
    newBtn.textContent = "Voltar";
    newBtn.disabled = false;
    newBtn.onclick = (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      if (window.opener && !window.opener.closed) { window.close(); return; }
      if (history.length > 1) { history.back(); return; }
      window.location.href = "/";
    };
    oldBtn.replaceWith(newBtn);
  }

  // "Validade:" -> "Proposta válida até:"
  const spanVal = document.getElementById("validadeTabela");
  if (spanVal) {
    const lbl = spanVal.previousElementSibling;
    if (lbl && lbl.tagName === "STRONG") lbl.textContent = "Proposta válida até:";
  }
}
// -------------------- Bind de eventos e início --------------------
if (btnConfirmar) btnConfirmar.addEventListener("click", confirmarPedido);
if (btnCancelar)  btnCancelar.addEventListener("click", cancelarPedido);

window.carregarPedido = carregarPedido;
window.addEventListener("DOMContentLoaded", aplicarModoInterno);
window.addEventListener("load", aplicarModoInterno);

if (taObs) {
  taObs.addEventListener('input', atualizarObsCounter);
  atualizarObsCounter(); // inicia contador
}
const btnFecharConfirm = document.getElementById('btnFecharConfirm');
if (btnFecharConfirm) btnFecharConfirm.addEventListener('click', closeConfirmModal);
