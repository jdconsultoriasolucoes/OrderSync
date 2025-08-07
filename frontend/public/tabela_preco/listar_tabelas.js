const API_BASE = "https://ordersync-backend-edjq.onrender.com";

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
        <td>${formatarData(tabela.validade_inicio)} → ${formatarData(tabela.validade_fim)}</td>
      `;

      tr.addEventListener("click", () => {
        document.querySelectorAll("#lista-tabelas-body tr").forEach(row => row.classList.remove("selected"));
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
  window.location.href = `tabela_preco.html?id=${tabelaSelecionadaId}`;
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
  window.location.href = "tabela_preco.html";
}