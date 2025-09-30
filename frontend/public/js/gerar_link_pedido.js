// js/gerar_link_pedido.js
// Modal "Gerar Link" com a escolha COM/SEM frete (apenas dentro do modal) + caixa de link.

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
        <!-- Escolha de frete DENTRO do modal (mantida) -->
        <div class="glp-row">
          <button class="glp-option" data-frete="1" title="Exibir valores com frete">Valor <b>com</b> Frete</button>
          <button class="glp-option" data-frete="0" title="Exibir valores sem frete">Valor <b>sem</b> Frete</button>
        </div>

        <!-- Caixa que aparece após escolher -->
        <div class="glp-linkbox" style="display:none;">
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
  .glp-row{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px}
  .glp-option{flex:1;min-width:180px;border:1px solid #ddd;border-radius:8px;padding:12px 14px;cursor:pointer;background:#f7f7f7}
  .glp-option:hover{background:#f0f0f0}
  .glp-linkbox{margin-top:8px}
  .glp-linkbox label{display:block;font-size:12px;color:#666;margin:6px 0}
  #glpLinkInput{width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;font-size:14px}
  .glp-actions{display:flex;gap:10px;margin-top:10px}
  .glp-actions button{border:none;background:#4a63e7;color:#fff;padding:10px 14px;border-radius:8px;cursor:pointer}
  .glp-actions button:hover{filter:brightness(.95)}
  #glpCopy{background:#4CAF50}
  #glpOpen{background:#1f73f1}
  #glpWhats{background:#25D366}
  .glp-hint{font-size:12px;color:#555;margin-top:8px}
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
    el.querySelector(".glp-linkbox").style.display = "none";
    el.querySelector("#glpLinkInput").value = "";
    el.querySelector("#glpHint").textContent = "";
    el.style.display = "flex";
  }
}

function buildPedidoLink({ tabelaId, comFrete, pedidoClientePath }) {
  const base = window.location.origin;
  const path = pedidoClientePath || "/pedido_cliente.html";
  const qs = new URLSearchParams({
    tabela_id: String(tabelaId),
    com_frete: comFrete ? "1" : "0",
  });
  return `${base}${path}?${qs.toString()}`;
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

/**
 * Abre o modal com a escolha COM/SEM frete e, após escolher, mostra o link.
 * @param {Object} opts
 * @param {number|string} opts.tabelaId
 * @param {string} [opts.pedidoClientePath="/pedido_cliente.html"]
 */
export function showGerarLinkModal({ tabelaId, pedidoClientePath = "/pedido_cliente.html" }) {
  if (!tabelaId && tabelaId !== 0) {
    console.warn("showGerarLinkModal: tabelaId ausente");
    alert("Não foi possível gerar o link: ID da tabela ausente.");
    return;
  }

  ensureModalInjected();
  showModal();

  const modal = document.getElementById("modalGerarLinkPedido");
  const linkBox = modal.querySelector(".glp-linkbox");
  const input = modal.querySelector("#glpLinkInput");
  const hint = modal.querySelector("#glpHint");

  // Escolha COM/SEM frete dentro do modal
  modal.querySelectorAll(".glp-option").forEach((btn) => {
    btn.onclick = () => {
      const comFrete = btn.dataset.frete === "1";
      const link = buildPedidoLink({ tabelaId, comFrete, pedidoClientePath });
      input.value = link;
      linkBox.style.display = "block";
      hint.textContent = comFrete
        ? "Este link exibirá os preços COM frete. A validade será buscada automaticamente."
        : "Este link exibirá os preços SEM frete. A validade será buscada automaticamente.";
    };
  });

  // Ações
  modal.querySelector("#glpCopy").onclick = async () => {
    if (!input.value) return;
    const ok = await copyToClipboard(input.value);
    hint.textContent = ok ? "Link copiado para a área de transferência." : "Não foi possível copiar. Copie manualmente.";
  };

  modal.querySelector("#glpOpen").onclick = () => {
    if (!input.value) return;
    window.open(input.value, "_blank", "noopener");
  };

  modal.querySelector("#glpWhats").onclick = () => {
    if (!input.value) return;
    const msg = `Olá! Segue o link para visualizar sua proposta de pedido:\n${input.value}`;
    const wa = `https://wa.me/?text=${encodeURIComponent(msg)}`;
    window.open(wa, "_blank", "noopener");
  };
}

/**
 * Handler plugável:
 *   const handler = gerarLinkHandler(() => currentTabelaId);
 *   btn.addEventListener("click", handler);
 */
export function gerarLinkHandler(getTabelaIdFn, options = {}) {
  return () => {
    const tabelaId = typeof getTabelaIdFn === "function" ? getTabelaIdFn() : getTabelaIdFn;
    showGerarLinkModal({ tabelaId, ...options });
  };
}
