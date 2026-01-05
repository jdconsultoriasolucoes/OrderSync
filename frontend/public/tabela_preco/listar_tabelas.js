// const API_BASE = "https://ordersync-backend-59d2.onrender.com";
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
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-editar" style="color:white; border:none; border-radius:4px; padding:6px 12px; cursor:pointer;" 
            onclick="window.location.href='criacao_tabela_preco.html?id=${encodeURIComponent(tabela.id)}'">
            Editar
          </button>
          
          <button class="btn btn-excluir" style="color:white; border:none; border-radius:4px; padding:6px 12px; cursor:pointer;" 
            onclick="abrirModalDelecao(${tabela.id})">
            Excluir
          </button>
          
          <button
            class="btn-enviar-link btn-secundario"
            style="border:none; border-radius:4px; padding:6px 12px; cursor:pointer;"
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
  const freteKg =
    freteStr === undefined || freteStr === null || freteStr === ""
      ? null
      : Number(String(freteStr).replace(",", "."));

  if (!tabelaId) return alert("ID da tabela não encontrado.");
  if (typeof window.__showGerarLinkModal !== "function") {
    // If not loaded yet, wait or alert
    return alert("Módulo de gerar link não carregado ou erro de carregamento.");
  }

  window.__showGerarLinkModal({
    tabelaId,
    freteKg,
    pedidoClientePath: "/tabela_preco/pedido_cliente.html",
  });
});