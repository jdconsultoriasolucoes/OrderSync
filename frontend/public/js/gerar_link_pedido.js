function ensureModalInjected() {
  if (document.getElementById("modalGerarLinkPedido")) return;

  const html = `
  <div id="modalGerarLinkPedido" class="os-modal-backdrop" style="display:none; z-index:9999;">
    <div class="os-modal-dialog" style="max-width: 500px; margin: auto;">
      <div class="os-modal-header">
        <h3 class="os-modal-title">Gerar Link do Pedido</h3>
        <button class="os-modal-close" aria-label="Fechar">&times;</button>
      </div>

      <div class="os-modal-body" style="padding: 20px;">

        <!-- ===== Toolbar: Segmented (com/sem frete) + Chip de Data ===== -->
        <div class="glp-toolbar">
          <div class="glp-segment" role="tablist" aria-label="Modo de frete">
            <button class="glp-option glp-seg is-active" data-frete="1" aria-selected="true">
              Valor <b>com</b> Frete
            </button>
            <button class="glp-option glp-seg" data-frete="0" aria-selected="false">
              Valor <b>sem</b> Frete
            </button>
          </div>

          <div class="glp-datechip">
            <label for="glpDate">Agendamento</label>
            <input type="date" id="glpDate" />
          </div>
        </div>

        <small class="glp-help">
          Será exibida como <i>Data de entrega</i> (com frete) ou <i>Data de retirada</i> (sem frete).
          Se não preencher, mostramos <i>a combinar</i>.
        </small>

        <!-- ===== Link Gerado + Ações ===== -->
        <div class="glp-linkbox">
          <label class="os-label">Link gerado</label>
          <input type="text" id="glpLinkInput" class="os-input" readonly style="margin-bottom: 16px;">
          <div class="glp-actions">
            <button id="glpPriceList" class="os-btn" style="background:var(--os-text-secondary); color:white; border-color:var(--os-text-secondary);">Lista de Preço</button>
            <button id="glpCopy" class="os-btn os-btn-primary" style="background:var(--os-success); border-color:var(--os-success);">Copiar link</button>
            <button id="glpOpen" class="os-btn os-btn-primary">Visualizar</button>
            <button id="glpWhats" class="os-btn os-btn-primary" style="background:#25D366; border-color:#25D366;">WhatsApp</button>
          </div>
          <p id="glpHint" class="glp-hint"></p>
        </div>

      </div>
    </div>
  </div>`;

  const css = `
  /* ===== Toolbar moderna ===== */
  .glp-toolbar{
    display:flex;align-items:center;justify-content:space-between;
    gap:12px;flex-wrap:wrap;margin:6px 0 16px;
  }

  /* Segmented control (pílulas) */
  .glp-segment{
    display:inline-flex;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;background:#f8fafc;width:100%;
  }
  .glp-seg{flex:1;border:0;background:transparent;padding:10px;font-weight:500;font-size:14px;color:#64748b;cursor:pointer;transition:all 0.2s}
  .glp-seg + .glp-seg{border-left:1px solid #e2e8f0}
  .glp-seg.is-active{background:#fff;color:#0f172a;box-shadow:0 1px 3px rgba(0,0,0,0.1);font-weight:600}

  /* Chip de data */
  .glp-datechip{
    display:flex;align-items:center;gap:8px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;width:100%;justify-content:space-between;
  }
  .glp-datechip label{margin:0;font-size:13px;font-weight:500;color:#475569;}
  .glp-datechip input[type="date"]{border:0;background:transparent;font-size:14px;color:#0f172a;outline:none;}

  /* Texto de ajuda menor */
  .glp-help{font-size:12px;color:#64748b;display:block;margin-bottom:16px;line-height:1.4}

  /* Linkbox e ações */
  .glp-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
  .glp-actions button{justify-content:center;}
  
  .glp-hint{font-size:13px;color:#64748b;margin-top:12px;min-height:1.2em;text-align:center}
  
  .glp-option.glp-disabled,
  .glp-seg.glp-disabled{
    opacity: .5;
    cursor: not-allowed;
  }

  /* Responsivo */
  @media (max-width:520px){
    .glp-actions{gap:8px;grid-template-columns:1fr;}
    .glp-segment{flex-direction:row;}
  }
  `;

  const wrap = document.createElement("div");
  wrap.innerHTML = html;
  document.body.appendChild(wrap);

  const styleTag = document.createElement("style");
  styleTag.textContent = css;
  document.head.appendChild(styleTag);

  // fechar
  wrap.querySelector(".os-modal-close").addEventListener("click", hideModal);
  wrap.addEventListener("click", (e) => {
    if (e.target.id === "modalGerarLinkPedido") hideModal();
  });
}

function hideModal() {
  const el = document.getElementById("modalGerarLinkPedido");
  if (el) {
    el.style.display = "none";
    el.classList.remove("active");
  }
}

function showModal() {
  const el = document.getElementById("modalGerarLinkPedido");
  if (el) {
    el.querySelector("#glpLinkInput").value = "";
    el.querySelector("#glpHint").textContent = "";
    const dt = el.querySelector("#glpDate");
    if (dt) dt.value = ""; // limpa a data a cada abertura
    el.style.display = "flex";
    // standard system class
    el.classList.add("active");
  }
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  }
}

function apiBase() {
  return (typeof window.API_BASE === "string" && window.API_BASE) ? window.API_BASE : "";
}

function getCodigoClienteHidden() {
  const el =
    document.querySelector('#codigo_cliente') ||
    document.querySelector('input[name="codigo_cliente"]') ||
    document.querySelector('[data-codigo-cliente]');
  const v = el?.value ?? el?.dataset?.codigoCliente ?? null;
  return (typeof v === "string" && v.trim()) ? v.trim() : null;
}


async function gerarLinkCurtoNoServidor({ tabelaId, comFrete, dataPrevistaISO }) {
  const url = apiBase() ? `${apiBase()}/link_pedido/gerar` : "/link_pedido/gerar";
  const token = localStorage.getItem("ordersync_token"); // Get token explicitly

  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const resp = await fetch(url, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({
      tabela_id: tabelaId,
      com_frete: comFrete,
      data_prevista: (isISODate(dataPrevistaISO) ? dataPrevistaISO : null),
      codigo_cliente: getCodigoClienteHidden()
    }),
  });
  if (!resp.ok) {
    const msg = await resp.text();
    throw new Error(`Falha ao gerar link: ${msg}`);
  }
  const data = await resp.json();
  return data.url; // ex.: https://.../p/<code>
}

// ----- Helpers de data -----
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
  const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
  dt.setHours(0, 0, 0, 0);
  return (dt < hoje) ? null : iso;
}
function aplicarEntregaNaUrl(urlCurta, entregaISO) {
  try {
    const u = new URL(urlCurta);
    if (entregaISO) u.searchParams.set("entrega", entregaISO);
    return u.toString();
  } catch {
    // fallback (não deve acontecer, pois urlCurta é absoluta)
    if (!entregaISO) return urlCurta;
    const sep = urlCurta.includes("?") ? "&" : "?";
    return `${urlCurta}${sep}entrega=${encodeURIComponent(entregaISO)}`;
  }
}

/**
 * Abre o modal e já mostra a linkbox preenchida.
 * @param {Object} opts
 * @param {number|string} opts.tabelaId
 */
export function showGerarLinkModal({ tabelaId, freteKg }) {
  if (!tabelaId && tabelaId !== 0) {
    console.warn("showGerarLinkModal: tabelaId ausente");
    alert("Não foi possível gerar o link: ID da tabela ausente.");
    return;
  }

  ensureModalInjected();
  showModal();

  const modal = document.getElementById("modalGerarLinkPedido");
  const input = modal.querySelector("#glpLinkInput");
  const hint = modal.querySelector("#glpHint");
  const buttons = Array.from(modal.querySelectorAll(".glp-option"));
  const dateInp = modal.querySelector("#glpDate");

  // --- Pega o frete: prioridade = valor passado; fallback = campo da tela ---
  function obterFreteKg() {
    // 1) se veio freteKg na chamada (listar_tabelas), usa ele
    if (typeof freteKg === "number" && !Number.isNaN(freteKg)) {
      return freteKg;
    }

    // 2) senão, tenta ler o campo da tela de criação de tabela
    const el =
      document.getElementById("frete_kg") ||
      document.querySelector('input[name="frete_kg"]');

    if (!el) return null;

    const raw = String(el.value || "").replace(",", ".");
    const num = Number(raw);
    return Number.isFinite(num) ? num : null;
  }

  const freteAtual = obterFreteKg();
  const temFrete = freteAtual != null && freteAtual > 0;

  // se tem frete -> COM frete; se não tem -> SEM frete
  let currentComFrete = !!temFrete;

  // se não tem frete, desabilita visualmente o botão "COM frete"
  const btnComFrete = buttons.find((b) => b.dataset.frete === "1");
  if (!temFrete && btnComFrete) {
    btnComFrete.classList.add("glp-disabled");
    btnComFrete.setAttribute("aria-disabled", "true");
  }

  const setBusy = (busy) => {
    buttons.forEach((b) => (b.disabled = busy));
    if (dateInp) dateInp.disabled = busy;
    if (busy) hint.textContent = "Gerando link...";
  };

  async function regenerate(comFrete) {
    // se NÃO tem frete configurado, sempre força SEM frete
    if (!temFrete) {
      comFrete = false;
    }

    currentComFrete = !!comFrete;

    buttons.forEach((b) =>
      b.classList.toggle(
        "is-active",
        (b.dataset.frete === "1") === currentComFrete
      )
    );

    const entregaISO = normalizarEntregaISO(dateInp?.value || "");
    if (dateInp && dateInp.value && !entregaISO) {
      hint.textContent =
        "Data inválida ou no passado. Corrija ou deixe em branco.";
      return;
    }

    try {
      setBusy(true);
      const urlCurta = await gerarLinkCurtoNoServidor({
        tabelaId,
        comFrete: currentComFrete,
        dataPrevistaISO: entregaISO,
      });
      input.value = urlCurta;
      hint.textContent = currentComFrete
        ? "Este link exibirá os preços COM frete."
        : "Este link exibirá os preços SEM frete.";
    } catch (e) {
      console.error(e);
      hint.textContent = "Erro ao gerar link. Tente novamente.";
    } finally {
      setBusy(false);
    }
  }

  // Gera inicialmente:
  // - se tem frete -> COM frete
  // - se não tem -> SEM frete
  regenerate(temFrete);

  // Trocar COM/SEM frete
  buttons.forEach((btn) => {
    btn.onclick = () => {
      const isCom = btn.dataset.frete === "1";

      // se não há frete configurado, ignora cliques em "COM frete"
      if (!temFrete && isCom) {
        return;
      }
      regenerate(isCom);
    };
  });

  // Regerar quando a data mudar
  if (dateInp) {
    dateInp.addEventListener("change", () => regenerate(currentComFrete));
    dateInp.addEventListener("input", () => {
      /* deixa o usuário digitar sem travar */
    });
  }

  // Ações
  modal.querySelector("#glpCopy").onclick = async () => {
    if (!input.value) return;
    const ok = await copyToClipboard(input.value);
    hint.textContent = ok
      ? "Link copiado para a área de transferência."
      : "Não foi possível copiar. Copie manualmente.";
  };

  modal.querySelector("#glpOpen").onclick = () => {
    if (!input.value) return;
    try {
      const u = new URL(input.value);
      u.searchParams.set("modo", "interno");
      u.hash = "interno";
      window.open(u.toString(), "_blank", "noopener,noreferrer");
    } catch {
      const sep = input.value.includes("?") ? "&" : "?";
      const url = `${input.value}${sep}modo=interno#interno`;
      window.open(url, "_blank", "noopener,noreferrer");
    }
  };

  const btnList = modal.querySelector("#glpPriceList");
  if (btnList) {
    btnList.onclick = () => {
      // Extrair code do link gerado
      const val = input.value;
      if (!val) return;

      const parts = val.split("/p/");
      if (parts.length < 2) {
        alert("Link inválido, gere novamente.");
        return;
      }
      const code = parts[1].split("?")[0].split("#")[0]; // clean code

      // Show options modal
      showPdfOptions((mode) => {
        const urlPdf = `${apiBase()}/link_pedido/lista_preco/${code}?modo=${mode}`;
        window.open(urlPdf, "_blank", "noopener,noreferrer");
      }, temFrete); // Pass temFrete context
    };
  }

  modal.querySelector("#glpWhats").onclick = () => {
    if (!input.value) return;
    const entregaISO = normalizarEntregaISO(dateInp?.value || "");
    const rotulo = currentComFrete ? "Data de entrega" : "Data de retirada";
    const dataTxt = entregaISO ? formatarBR(entregaISO) : "a combinar";
    const msg = `Olá! Segue o link para visualizar sua proposta de pedido:\n${rotulo}: ${dataTxt}\n${input.value}`;
    const wa = `https://wa.me/?text=${encodeURIComponent(msg)}`;
    window.open(wa, "_blank", "noopener");
  };
}

function showPdfOptions(onSelect, temFrete = true) {
  // Se não tem frete, desabilitamos "Com frete"(1) e "Ambos"(3).
  // Indices ou data-mode: 'com', 'sem', 'ambos'.

  const styleDisabled = 'opacity: 0.5; cursor: not-allowed; pointer-events: none; background: #eee; color: #999;';

  const html = `
  <div id="modalPdfOptions" class="os-modal-backdrop active" style="z-index: 10000; align-items: center; justify-content: center; display: flex;">
    <div class="os-modal-dialog" style="max-width: 380px; text-align: center; margin: auto;">
      <div class="os-modal-header" style="justify-content: center; padding: 16px;">
        <h3 class="os-modal-title" style="font-size: 16px; margin: 0;">Opções de Lista de Preço</h3>
      </div>
      <div class="os-modal-body" style="display: flex; flex-direction: column; gap: 10px; padding: 20px;">
        <button class="os-btn glp-option ${temFrete ? 'os-btn-primary' : 'os-btn-secondary'}" data-mode="com" style="${!temFrete ? styleDisabled : ''}">Com Frete</button>
        <button class="os-btn glp-option ${!temFrete ? 'os-btn-primary' : 'os-btn-secondary'}" data-mode="sem">Sem Frete</button>
        <button class="os-btn glp-option os-btn-secondary" data-mode="ambos" style="${!temFrete ? styleDisabled : ''}">Ambos (Padrão)</button>
        <button class="os-btn os-btn-text glp-option" data-mode="cancel" style="color: var(--os-error, #d9534f); padding-top: 10px; margin-top: 4px;">Cancelar</button>
      </div>
    </div>
  </div>`;

  const wrap = document.createElement("div");
  wrap.innerHTML = html;
  document.body.appendChild(wrap);

  const close = () => {
    wrap.remove();
  };

  wrap.addEventListener("click", (e) => {
    if (e.target.id === "modalPdfOptions") close();
  });

  wrap.querySelectorAll("button").forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      // Se estiver desabilitado visualmente, nao faz nada (embora pointer-events:none ja trate)
      if (btn.style.pointerEvents === 'none') return;

      const mode = btn.dataset.mode;
      close();
      if (mode !== "cancel") {
        onSelect(mode);
      }
    };
  });
}


/** Handler plugável */
export function gerarLinkHandler(getTabelaIdFn) {
  return () => {
    const tabelaId = typeof getTabelaIdFn === "function" ? getTabelaIdFn() : getTabelaIdFn;
    showGerarLinkModal({ tabelaId });
  };
}
