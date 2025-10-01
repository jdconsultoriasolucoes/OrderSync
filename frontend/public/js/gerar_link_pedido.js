// js/gerar_link_pedido.js
// Modal "Gerar Link" — gera URL curta via POST /link_pedido/gerar e exibe no modal.
// Requisitos: window.API_BASE definido (ex.: http://localhost:8000)

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
        <div class="glp-row">
          <button class="glp-option" data-frete="1" title="Exibir valores com frete">Valor <b>com</b> Frete</button>
          <button class="glp-option" data-frete="0" title="Exibir valores sem frete">Valor <b>sem</b> Frete</button>
        </div>

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
  .glp-row{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px}
  .glp-option{flex:1;min-width:180px;border:1px solid #ddd;border-radius:8px;padding:12px 14px;cursor:pointer;background:#f7f7f7}
  .glp-option:hover{background:#f0f0f0}
  .glp-option.is-active{background:#eef2ff;border-color:#c7d2fe;box-shadow:inset 0 0 0 2px #c7d2fe}
  .glp-linkbox label{display:block;font-size:12px;color:#666;margin:6px 0}
  #glpLinkInput{width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;font-size:14px}
  .glp-actions{display:flex;gap:10px;margin-top:10px}
  .glp-actions button{border:none;background:#4a63e7;color:#fff;padding:10px 14px;border-radius:8px;cursor:pointer}
  .glp-actions button:hover{filter:brightness(.95)}
  #glpCopy{background:#4CAF50}
  #glpOpen{background:#1f73f1}
  #glpWhats{background:#25D366}
  .glp-hint{font-size:12px;color:#555;margin-top:8px;min-height:1.2em}
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

async function gerarLinkCurtoNoServidor({ tabelaId, comFrete }) {
  const base = (typeof window.API_BASE === "string" && window.API_BASE) ? window.API_BASE : "";
  const url  = base ? `${base}/link_pedido/gerar` : "/link_pedido/gerar";
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tabela_id: tabelaId, com_frete: comFrete }),
  });
  if (!resp.ok) {
    const msg = await resp.text();
    throw new Error(`Falha ao gerar link: ${msg}`);
  }
  const data = await resp.json();
  return data.url; // ex.: https://.../p/<code>
}

/**
 * Abre o modal e já mostra a linkbox preenchida (sem "expandir").
 * Botões COM/SEM frete apenas re-geram a URL curta.
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

  const modal   = document.getElementById("modalGerarLinkPedido");
  const linkBox = modal.querySelector(".glp-linkbox");
  const input   = modal.querySelector("#glpLinkInput");
  const hint    = modal.querySelector("#glpHint");
  const buttons = Array.from(modal.querySelectorAll(".glp-option"));

  // padrão: COM frete (troque para false se quiser SEM como padrão)
  const defaultComFrete = true;

  // estado UI helper
  const setBusy = (busy) => {
    buttons.forEach(b => b.disabled = busy);
    hint.textContent = busy ? "Gerando link..." : hint.textContent;
  };

  // gera inicialmente com o padrão
  (async () => {
    try {
      buttons.forEach(b => b.classList.toggle("is-active", (b.dataset.frete === "1") === defaultComFrete));
      setBusy(true);
      const urlCurta = await gerarLinkCurtoNoServidor({ tabelaId, comFrete: defaultComFrete });
      input.value = urlCurta;
      hint.textContent = defaultComFrete
        ? "Este link exibirá os preços COM frete. A validade será buscada automaticamente."
        : "Este link exibirá os preços SEM frete. A validade será buscada automaticamente.";
    } catch (e) {
      console.error(e);
      hint.textContent = "Erro ao gerar link. Tente novamente.";
    } finally {
      setBusy(false);
    }
  })();

  // cliques trocam a opção e re-geram a URL curta
  buttons.forEach((btn) => {
    btn.onclick = async () => {
      const comFrete = btn.dataset.frete === "1";
      buttons.forEach(b => b.classList.toggle("is-active", b === btn));
      try {
        setBusy(true);
        const urlCurta = await gerarLinkCurtoNoServidor({ tabelaId, comFrete });
        input.value = urlCurta;
        hint.textContent = comFrete
          ? "Este link exibirá os preços COM frete. A validade será buscada automaticamente."
          : "Este link exibirá os preços SEM frete. A validade será buscada automaticamente.";
      } catch (e) {
        console.error(e);
        hint.textContent = "Erro ao gerar link. Tente novamente.";
      } finally {
        setBusy(false);
      }
    };
  });

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
export function gerarLinkHandler(getTabelaIdFn) {
  return () => {
    const tabelaId = typeof getTabelaIdFn === "function" ? getTabelaIdFn() : getTabelaIdFn;
    showGerarLinkModal({ tabelaId });
  };
}
