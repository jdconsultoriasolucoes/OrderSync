function ensureModalInjected() {
  if (document.getElementById("modalGerarLinkPedido")) return;

  const html = `
  <div id="modalGerarLinkPedido" class="glp-backdrop" style="display:none;">
    <div class="glp-modal">
      <div class="glp-header">
        <h3>Gerar Link do Pedido</h3>
        <button class="glp-close" aria-label="Fechar">&times;</button>
      </div>

      <div class="glp-body">

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
            <label for="glpDate">Data de entrega/retirada</label>
            <input type="date" id="glpDate" />
          </div>
        </div>

        <small class="glp-help">
          Será exibida como <i>Data de entrega</i> (com frete) ou <i>Data de retirada</i> (sem frete).
          Se não preencher, mostramos <i>a combinar</i>.
        </small>

        <!-- ===== Link Gerado + Ações ===== -->
        <div class="glp-linkbox">
          <label>Link gerado</label>
          <input type="text" id="glpLinkInput" readonly>
          <div class="glp-actions">
            <button id="glpCopy">Copiar link</button>
            <button id="glpOpen">Visualizar</button>
            <button id="glpWhats">WhatsApp</button>
          </div>
          <p id="glpHint" class="glp-hint"></p>
        </div>

      </div>
    </div>
  </div>`;

  const css = `
  .glp-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:9999;}
  .glp-modal{width:min(560px,95vw);background:#fff;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.25);overflow:hidden;font-family:system-ui,Segoe UI,Arial,sans-serif}
  .glp-header{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;border-bottom:1px solid #e5e5e5}
  .glp-header h3{margin:0;font-size:18px}
  .glp-close{background:none;border:none;font-size:22px;cursor:pointer;line-height:1}
  .glp-body{padding:16px}

  /* ===== Toolbar moderna ===== */
  .glp-toolbar{
    display:flex;align-items:center;justify-content:space-between;
    gap:12px;flex-wrap:wrap;margin:6px 0 10px;
  }

  /* Segmented control (pílulas) */
  .glp-segment{
    display:inline-flex;border:1px solid #d0d7de;border-radius:10px;overflow:hidden;background:#fff;
  }
  /* IMPORTANTE: sobrescreve o estilo genérico de .glp-option */
  .glp-option{ /* estilo legado, mantido para outras telas se usarem */
    flex:1;min-width:180px;border:1px solid #ddd;border-radius:8px;padding:12px 14px;cursor:pointer;background:#f7f7f7;
  }
  .glp-option:hover{background:#f0f0f0}
  .glp-option.is-active{background:#eef2ff;border-color:#c7d2fe;box-shadow:inset 0 0 0 2px #c7d2fe}

  /* Botões do segmented nesta toolbar */
  .glp-seg{flex:0 0 auto;min-width:auto;border:0;border-radius:0;background:#fff;padding:8px 14px;font-weight:600;color:#344054;cursor:pointer}
  .glp-seg + .glp-seg{border-left:1px solid #d0d7de}
  .glp-seg.is-active{background:#eef4ff;color:#1f4bd8}

  /* Chip de data */
  .glp-datechip{
    display:flex;align-items:center;gap:8px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:999px;padding:6px 10px;
  }
  .glp-datechip label{margin:0;font-size:12px;color:#475569;white-space:nowrap}
  .glp-datechip input[type="date"]{width:150px;border:0;background:transparent;padding:2px 4px;font-size:13px}

  /* Texto de ajuda menor */
  .glp-help{font-size:11px;color:#666;display:block;margin:-2px 0 10px}

  /* Linkbox e ações (mantidos) */
  .glp-linkbox label{display:block;font-size:12px;color:#666;margin:6px 0}
  #glpLinkInput{width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;font-size:14px}
  .glp-actions{display:flex;gap:10px;margin-top:10px}
  .glp-actions button{border:none;background:#4a63e7;color:#fff;padding:10px 14px;border-radius:8px;cursor:pointer}
  .glp-actions button:hover{filter:brightness(.95)}
  #glpCopy{background:#4CAF50}
  #glpOpen{background:#1f73f1}
  #glpWhats{background:#25D366}
  .glp-hint{font-size:12px;color:#555;margin-top:8px;min-height:1.2em}

  /* Responsivo */
  @media (max-width:520px){
    .glp-toolbar{flex-direction:column;align-items:stretch}
    .glp-datechip{align-self:flex-end}
  }
  `;

  const wrap = document.createElement("div");
  wrap.innerHTML = html;
  document.body.appendChild(wrap);

  const styleTag = document.createElement("style");
  styleTag.textContent = css;
  document.head.appendChild(styleTag);

  // fechar
  wrap.querySelector(".glp-close").addEventListener("click", hideModal);
  wrap.addEventListener("click", (e) => {
    if (e.target.id === "modalGerarLinkPedido") hideModal();
  });
}

function hideModal() {
  const el = document.getElementById("modalGerarLinkPedido");
  if (el) el.style.display = "none";
}

function showModal() {
  const el = document.getElementById("modalGerarLinkPedido");
  if (el) {
    el.querySelector("#glpLinkInput").value = "";
    el.querySelector("#glpHint").textContent = "";
    const dt = el.querySelector("#glpDate");
    if (dt) dt.value = ""; // limpa a data a cada abertura
    el.style.display = "flex";
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


async function gerarLinkCurtoNoServidor({ tabelaId, comFrete, dataPrevistaISO  }) {
  const url  = apiBase() ? `${apiBase()}/link_pedido/gerar` : "/link_pedido/gerar";
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tabela_id: tabelaId,
      com_frete: comFrete,
      data_prevista: (isISODate(dataPrevistaISO) ? dataPrevistaISO : null),
     codigo_cliente: getCodigoClienteHidden() }),
      
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
  const [y,m,d] = iso.split("-").map(Number);
  const dt = new Date(y, m-1, d);
  if (Number.isNaN(dt.getTime())) return null;
  return dt.toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo" });
}
function normalizarEntregaISO(iso) {
  if (!isISODate(iso)) return null;
  const [y,m,d] = iso.split("-").map(Number);
  const dt = new Date(y, m-1, d);
  if (Number.isNaN(dt.getTime())) return null;
  const hoje = new Date(); hoje.setHours(0,0,0,0);
  dt.setHours(0,0,0,0);
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
export function showGerarLinkModal({ tabelaId }) {
  if (!tabelaId && tabelaId !== 0) {
    console.warn("showGerarLinkModal: tabelaId ausente");
    alert("Não foi possível gerar o link: ID da tabela ausente.");
    return;
  }

  ensureModalInjected();
  showModal();

  const modal    = document.getElementById("modalGerarLinkPedido");
  const linkBox  = modal.querySelector(".glp-linkbox");
  const input    = modal.querySelector("#glpLinkInput");
  const hint     = modal.querySelector("#glpHint");
  const buttons  = Array.from(modal.querySelectorAll(".glp-option"));
  const dateInp  = modal.querySelector("#glpDate");

  // padrão: COM frete
  let currentComFrete = true;

  const setBusy = (busy) => {
    buttons.forEach(b => b.disabled = busy);
    if (dateInp) dateInp.disabled = busy;
    if (busy) hint.textContent = "Gerando link...";
  };

  async function regenerate(comFrete) {
    currentComFrete = !!comFrete;
    buttons.forEach(b => b.classList.toggle("is-active", (b.dataset.frete === "1") === currentComFrete));

    const entregaISO = normalizarEntregaISO(dateInp?.value || "");
    if (dateInp && dateInp.value && !entregaISO) {
      hint.textContent = "Data inválida ou no passado. Corrija ou deixe em branco.";
      return;
    }

    try {
      setBusy(true);
      const urlCurta = await gerarLinkCurtoNoServidor({ tabelaId, comFrete: currentComFrete,dataPrevistaISO: entregaISO });
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

  // Gera inicialmente com COM frete
  regenerate(true);

  // Trocar COM/SEM frete
  buttons.forEach((btn) => {
    btn.onclick = () => regenerate(btn.dataset.frete === "1");
  });

  // Regerar quando a data mudar
  if (dateInp) {
    dateInp.addEventListener("change", () => regenerate(currentComFrete));
    dateInp.addEventListener("input",  () => {/* deixa o usuário digitar sem travar */});
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
    window.open(input.value, "_blank", "noopener");
  };

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

/** Handler plugável */
export function gerarLinkHandler(getTabelaIdFn) {
  return () => {
    const tabelaId = typeof getTabelaIdFn === "function" ? getTabelaIdFn() : getTabelaIdFn;
    showGerarLinkModal({ tabelaId });
  };
}