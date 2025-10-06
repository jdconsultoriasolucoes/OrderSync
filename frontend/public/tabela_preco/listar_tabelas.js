const API_BASE = "https://ordersync-backend-edjq.onrender.com";
window.API_BASE = window.API_BASE || API_BASE;
let tabelaSelecionadaId = null;

document.addEventListener("DOMContentLoaded", () => {
  carregarTabelas();
});

async function carregarTabelas() {
  try {
    const response = await fetch(`${API_BASE}/tabela_preco`);
    const tabelas = await response.json();

    const tbody = document.getElementById("lista-tabelas-body");
    tbody.innerHTML = "";

    tabelas.forEach(tabela => {
      const tr = document.createElement("tr");
      tr.dataset.id = tabela.id;

      tr.innerHTML = `
      <td>${tabela.nome_tabela}</td>
      <td>${tabela.cliente}</td>
      <td>${tabela.fornecedor}</td>
      <td>
          <button onclick="window.location.href='criacao_tabela_preco.html?id=${encodeURIComponent(tabela.id)}'">Editar</button>
          <button onclick="abrirModalDelecao(${tabela.id})">Excluir</button>
          <button class="btn-enviar-link" data-id="${tabela.id}">Enviar</button>
      </td>
      `;

      tr.addEventListener("click", () => {
             document.querySelectorAll("#lista-tabelas-body tr")
             .forEach(row => row.classList.remove("selected"));
             tr.classList.add("selected");
             tabelaSelecionadaId = tabela.id;

      // ✅ Habilita os botões se existirem na página
       const btnEditar  = document.getElementById("btn-editar");
       const btnExcluir = document.getElementById("btn-excluir");
       if (btnEditar)  btnEditar.disabled  = false;
       if (btnExcluir) btnExcluir.disabled = false;
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

function deletarTabela() {
  if (!tabelaSelecionadaId) {
    alert("Selecione uma tabela para deletar.");
    return;
  }

  const modal = document.getElementById("modal-confirmar-delete");
  modal.style.display = "flex";
}

async function confirmarDelecao(confirmado) {
  const modal = document.getElementById("modal-confirmar-delete");
  modal.style.display = "none";

  if (!confirmado) return;

  try {
    const response = await fetch(`${API_BASE}/tabela_preco/${tabelaSelecionadaId}`, {
      method: "DELETE"
    });

    if (!response.ok) throw new Error("Erro ao deletar.");

    alert("Tabela desativada com sucesso!");
    carregarTabelas();
    tabelaSelecionadaId = null;
  } catch (err) {
    console.error("Erro ao deletar tabela:", err);
    alert("Erro ao deletar tabela.");
  }
}

function voltar() {
  window.location.href = "criacao_tabela_preco.html";
}

function abrirModalDelecao(id) {
  tabelaSelecionadaId = id;
  const modal = document.getElementById("modal-confirmar-delete");
  modal.style.display = "flex";
}

document.getElementById("pesquisa").addEventListener("keyup", function() {
  let filtro = this.value.toLowerCase();
  let linhas = document.querySelectorAll("#lista-tabelas-body tr");

  linhas.forEach(linha => {
    let textoLinha = linha.innerText.toLowerCase();
    linha.style.display = textoLinha.includes(filtro) ? "" : "none";
  });
});

document.addEventListener("click", (e) => {
  const btn = e.target.closest(".btn-enviar-link");
  if (!btn) return;
  const tabelaId = btn.dataset.id;
  if (!tabelaId) return alert("ID da tabela não encontrado.");
  if (typeof window.__showGerarLinkModal !== "function") {
    return alert("Módulo de gerar link não carregado. Verifique o import em listar_tabelas.html.");
  }
  window.__showGerarLinkModal({ tabelaId, pedidoClientePath: "/tabela_preco/pedido_cliente.html" });
});