document.addEventListener("DOMContentLoaded", function () {
  carregarProdutos();

  document.getElementById("grupo").addEventListener("change", carregarProdutos);
  document.getElementById("plano_pagamento").addEventListener("change", carregarProdutos);
  document.getElementById("frete_kg").addEventListener("change", carregarProdutos);
});

function carregarProdutos() {
  const grupo = document.getElementById("grupo").value || null;
  const plano_pagamento = document.getElementById("plano_pagamento").value || "000";
  const frete_kg = parseFloat(document.getElementById("frete_kg").value) || 0.0;
  const fator_comissao = 0.0; // valor padrão ao carregar

  fetch(`/tabela_preco/produtos_filtro?grupo=${grupo}&plano_pagamento=${plano_pagamento}&frete_kg=${frete_kg}&fator_comissao=${fator_comissao}`)
    .then((response) => response.json())
    .then((data) => preencherTabela(data));
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
      <td>${p.valor.toFixed(2)}</td>
      <td><input type="number" step="0.0001" value="${p.fator_comissao}" onchange="atualizarLinha(${index}, this.value)"></td>
      <td id="acrescimo-${index}">${p.acrescimo?.toFixed(4) ?? "0.0000"}</td>
      <td id="desconto-${index}">${p.desconto?.toFixed(4) ?? "0.0000"}</td>
      <td id="valor_liquido-${index}">${p.valor_liquido?.toFixed(2) ?? "0.00"}</td>
    `;
    tbody.appendChild(tr);
  });
}

function atualizarLinha(index, novoFator) {
  const valor = parseFloat(document.querySelectorAll("#tabela-produtos-body tr")[index].children[5].innerText);
  const planoPercentual = parseFloat(document.getElementById("frete_kg").value) || 0;
  const fator = parseFloat(novoFator) || 0;

  const acrescimo = valor * planoPercentual;
  const desconto = valor * fator;
  const valor_liquido = valor + acrescimo - desconto;

  document.getElementById(`acrescimo-${index}`).innerText = acrescimo.toFixed(4);
  document.getElementById(`desconto-${index}`).innerText = desconto.toFixed(4);
  document.getElementById(`valor_liquido-${index}`).innerText = valor_liquido.toFixed(2);
}
