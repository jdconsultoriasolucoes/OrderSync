const API_BASE = window.API_BASE || "https://ordersync-backend-59d2.onrender.com"; // Restored & Safe
window.API_BASE = window.API_BASE || API_BASE;
let tabelaSelecionadaId = null;

// Paginação e Busca
let currentPage = 1;
let pageSize = 10;
let totalPages = 1;
let searchTimeout = null;

document.addEventListener("DOMContentLoaded", () => {
  setupMenu();
  setupPagination();
  setupSearch();
  carregarTabelas();
});

function setupMenu() {
  const menuBtn = document.getElementById("menu-button");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("overlay");

  if (menuBtn && sidebar && overlay) {
    menuBtn.addEventListener("click", () => {
      sidebar.classList.add("active");
      overlay.style.display = "block";
    });

    overlay.addEventListener("click", () => {
      sidebar.classList.remove("active");
      overlay.style.display = "none";
    });
  }
}

function setupSearch() {
  const input = document.getElementById("pesquisa");
  if (!input) return;

  input.addEventListener("keyup", () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      currentPage = 1;
      carregarTabelas();
    }, 500); // Debounce 500ms
  });
}

function setupPagination() {
  const btnPrev = document.getElementById("btn-prev");
  const btnNext = document.getElementById("btn-next");

  if (btnPrev) {
    btnPrev.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        carregarTabelas();
      }
    });
  }

  if (btnNext) {
    btnNext.addEventListener("click", () => {
      if (currentPage < totalPages) {
        currentPage++;
        carregarTabelas();
      }
    });
  }
}

async function carregarTabelas() {
  try {
    const input = document.getElementById("pesquisa");
    const q = input ? input.value : "";

    const url = new URL(`${API_BASE}/tabela_preco`);
    url.searchParams.append("page", currentPage);
    url.searchParams.append("page_size", pageSize);
    if (q) url.searchParams.append("q", q);

    const response = await fetch(url);
    const data = await response.json();

    let tabelas = [];
    if (data.items) {
      tabelas = data.items;
      totalPages = data.total_pages;
      const total = data.total || 0;

      const pageInfo = document.getElementById("page-info");
      if (pageInfo) pageInfo.textContent = `Página ${currentPage} de ${totalPages || 1} (Total: ${total})`;

      const btnPrev = document.getElementById("btn-prev");
      const btnNext = document.getElementById("btn-next");
      if (btnPrev) btnPrev.disabled = (currentPage <= 1);
      if (btnNext) btnNext.disabled = (currentPage >= totalPages);

    } else if (Array.isArray(data)) {
      // Fallback caso a API antiga ainda esteja respondendo
      tabelas = data;
    }

    const tbody = document.getElementById("lista-tabelas-body");
    tbody.innerHTML = "";

    tabelas.forEach(tabela => {
      const tr = document.createElement("tr");
      tr.dataset.id = tabela.id;

      tr.innerHTML = `
      <td>${tabela.nome_tabela || '-'}</td>
      <td>${tabela.cliente || '-'}</td>
      <td>${tabela.fornecedor || '-'}</td>
      <td>
        <div style="display: flex; gap: var(--os-space-2);">
          <button class="os-btn os-btn-secondary os-btn-sm" 
            onclick="window.location.href='criacao_tabela_preco.html?id=${encodeURIComponent(tabela.id)}'">
            Editar
          </button>
          
          <button class="os-btn os-btn-danger os-btn-sm" 
            onclick="abrirModalDelecao(${tabela.id})">
            Excluir
          </button>
          
          <button
            class="os-btn os-btn-primary os-btn-sm btn-enviar-link"
            style="display: none;"
            data-id="${tabela.id}"
            data-frete-kg="${tabela.frete_kg !== undefined && tabela.frete_kg !== null ? tabela.frete_kg : ''}"
          >
            Enviar
          </button>
        </div>
      </td>
      `;

      tr.addEventListener("click", () => {
        document.querySelectorAll("#lista-tabelas-body tr")
          .forEach(row => row.classList.remove("selected"));
        tr.classList.add("selected");
        tabelaSelecionadaId = tabela.id;
      });

      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Erro ao carregar tabelas:", err);
  }
}

function formatarData(data) {
  const d = new Date(data);
  return d.toLocaleDateString("pt-BR");
}

function selecionarTabela() {
  if (!tabelaSelecionadaId) {
    alert("Selecione uma tabela para continuar.");
    return;
  }
  window.location.href = `criacao_tabela_preco.html?id=${tabelaSelecionadaId}`;
}

function confirmarDelecao(confirmado) {
  const modal = document.getElementById("modal-confirmar-delete");
  modal.style.display = "none";

  if (!confirmado) return;

  if (!tabelaSelecionadaId) return;

  fetch(`${API_BASE}/tabela_preco/${tabelaSelecionadaId}`, {
    method: "DELETE"
  })
    .then(response => {
      if (!response.ok) throw new Error("Erro ao deletar.");
      alert("Tabela desativada com sucesso!");
      carregarTabelas();
      tabelaSelecionadaId = null;
    })
    .catch(err => {
      console.error("Erro ao deletar tabela:", err);
      alert("Erro ao deletar tabela.");
    });
}

function voltar() {
  window.location.href = "criacao_tabela_preco.html";
}

function abrirModalDelecao(id) {
  tabelaSelecionadaId = id;
  const modal = document.getElementById("modal-confirmar-delete");
  modal.style.display = "flex";
}

// Global scope for HTML access
window.voltar = voltar;
window.confirmarDelecao = confirmarDelecao;
window.abrirModalDelecao = abrirModalDelecao;

// Listener for "Enviar" buttons (delegated)
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".btn-enviar-link");
  if (!btn) return;

  const tabelaId = btn.dataset.id;
  const freteStr = btn.dataset.freteKg;
  let freteKg = null;
  if (freteStr !== undefined && freteStr !== null && freteStr !== "") {
    freteKg = Number(String(freteStr).replace(",", "."));
  }

  if (!tabelaId) return alert("ID da tabela não encontrado.");

  if (window.__showGerarLinkModal) {
    window.__showGerarLinkModal({
      tabelaId,
      freteKg,
      pedidoClientePath: "/tabela_preco/pedido_cliente.html",
    });
  } else {
    console.warn("Módulo de gerar link não carregado ou erro de carregamento.");
  }
});

function setupUpdatePrices() {
  const btn = document.getElementById("btn-update-prices");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    if (!confirm("Isso irá atualizar os preços base de TODAS as tabelas ativas com base no cadastro de produtos atual (PDF). Deseja continuar?")) {
      return;
    }

    const originalText = btn.textContent;
    btn.textContent = "Processando...";
    btn.disabled = true;

    try {
      const response = await fetch(`${API_BASE}/tabela_preco/recalcular_massivo`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({}) // Sem parâmetros por enquanto
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(errText || "Erro ao atualizar preços.");
      }

      const result = await response.json();
      alert(`Sucesso! \n${result.tabelas_afetadas} tabelas analisadas.\n${result.linhas_atualizadas} produtos atualizados.`);
      carregarTabelas(); // Recarrega a lista para refletir datas de edição

    } catch (error) {
      console.error("Erro no update massivo:", error);
      alert("Falha ao atualizar preços: " + error.message);
    } finally {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  });
}
window.setupUpdatePrices = setupUpdatePrices; // Expose if needed