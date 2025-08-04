document.addEventListener("DOMContentLoaded", function () {
  carregarProdutos();

  document.getElementById("grupo").addEventListener("change", carregarProdutos);
  document.getElementById("plano_pagamento").addEventListener("change", carregarProdutos);
  document.getElementById("frete_kg").addEventListener("change", carregarProdutos);
});

function carregarProdutos() {
  let grupo = document.getElementById("grupo").value;
  const plano_pagamento = document.getElementById("plano_pagamento").value || "000";
  const frete_kg = parseFloat(document.getElementById("frete_kg").value) || 0.0;
  const fator_comissao = 0.0;

  // Se grupo estiver vazio, não envie o parâmetro
  const url = new URL("/tabela_preco/produtos_filtro", window.location.origin);
  if (grupo) url.searchParams.append("grupo", grupo);
  url.searchParams.append("plano_pagamento", plano_pagamento);
  url.searchParams.append("frete_kg", frete_kg);
  url.searchParams.append("fator_comissao", fator_comissao);

  fetch(url)
    .then((response) => {
      if (!response.ok) throw new Error("Erro ao buscar produtos");
      return response.json();
    })
    .then((data) => preencherTabela(data))
    .catch((err) => console.error("Erro ao carregar produtos:", err));
}


function preencherTabela(produtos) {
  const tbody = document.getElementById("tabela-produtos-body");
  tbody.innerHTML = "";

  produtos.forEach((p, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="checkbox" class="produto-checkbox"></td>
      <td>${p.codigo_tabela}</td>
      <td>${p.descricao}</td>
      <td>${p.embalagem}</td>
      <td>${p.peso_liquido ?? ""}</td>
      <td>${p.valor_base.toFixed(2)}</td>
      <td>
        <select onchange="atualizarLinhaPorDesconto(this, ${index}, ${p.valor_base})">
            ${Object.entries(mapaDescontos).map(([codigo, percentual]) => `
              <option value="${codigo}">${codigo} - ${percentual}</option>
            `).join('')}
        </select>
      </td>
      <td id="acrescimo-${index}">0.0000</td>
      <td id="desconto-${index}">0.0000</td>
      <td id="valor_liquido-${index}">${p.valor_base.toFixed(2)}</td>
    </tr>`;
    tbody.appendChild(tr);
  });
}


function atualizarLinhaPorDesconto(select, index, valorBase) {
  const idDesconto = select.value;
  const fator = mapaDescontos[idDesconto] || 0;

  const frete_kg = parseFloat(document.getElementById("frete_kg").value) || 0;
  const acrescimo = valorBase * frete_kg;
  const desconto = valorBase * fator;
  const valor_liquido = valorBase + acrescimo - desconto;

  document.getElementById(`acrescimo-${index}`).innerText = acrescimo.toFixed(4);
  document.getElementById(`desconto-${index}`).innerText = desconto.toFixed(4);
  document.getElementById(`valor_liquido-${index}`).innerText = valor_liquido.toFixed(2);
}


let mapaDescontos = {};

async function carregarDescontos() {
    const response = await fetch("/tabela_preco/descontos");
    const dados = await response.json();

    dados.forEach(item => {
        mapaDescontos[item.codigo] = item.percentual;
    });
}

function calcularValorLiquido(valorBase, idDesconto) {
    const fator = mapaDescontos[idDesconto] || 0;
    const desconto = valorBase * fator;
    return (valorBase - desconto).toFixed(2);
}

function atualizarValorLiquido(select, index, valorBase) {
    const idDesconto = parseInt(select.value);
    const valor = calcularValorLiquido(valorBase, idDesconto);
    document.getElementById(`valor_liquido_${index}`).textContent = valor;
}


window.onload = async function() {
    await carregarDescontos();
    await carregarProdutos(); // se tiver outra função para carregar os produtos
};

