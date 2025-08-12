const API_BASE = "https://ordersync-backend-edjq.onrender.com";

let currentPage = 1;
let pageSize = 25;
let totalPages = null; 

let cacheListaCompleta = null; // fallback para paginação no cliente

document.addEventListener("DOMContentLoaded", function () {
  // 1) Filtro que MUDA a lista -> refaz fetch (vai no backend de novo)
  document.getElementById("grupo").addEventListener("change", () => {
    currentPage = 1;
    carregarProdutos();
  });

  // 2) Filtros que NÃO mudam a lista -> só recalculam a página atual (sem backend)
  document.getElementById("plano_pagamento").addEventListener("change", recalcTabelaAtual);
  document.getElementById("frete_kg").addEventListener("change", recalcTabelaAtual);

  // 3) Itens por página -> refaz fetch com novo page_size
  const ps = document.getElementById("page_size");
  if (ps) {
    pageSize = parseInt(ps.value, 10) || 25;
    ps.addEventListener("change", () => {
      pageSize = parseInt(ps.value, 10) || 25;
      currentPage = 1;
      carregarProdutos();
    });
  }
});


function carregarProdutos(page = currentPage) {
  currentPage = page;

  const grupo = document.getElementById("grupo").value;

  const url = new URL(`${API_BASE}/tabela_preco/produtos_filtro`);
  if (grupo) url.searchParams.append("grupo", grupo);
  url.searchParams.append("page", currentPage);
  url.searchParams.append("page_size", pageSize);

  fetch(url)
    .then((response) => {
      if (!response.ok) throw new Error("Erro ao buscar produtos");
      return response.json();
    })
    .then((data) => {
      let items = [];
      let total = null;

      if (Array.isArray(data)) {
        // Backend sem paginação: pagina no cliente
        cacheListaCompleta = data.slice();
        const start = (currentPage - 1) * pageSize;
        const end = start + pageSize;
        items = cacheListaCompleta.slice(start, end);
        total = cacheListaCompleta.length;
      } else if (data && Array.isArray(data.items)) {
        // Backend paginado: usa dados do server
        items = data.items;
        total = typeof data.total === "number" ? data.total : data.items.length;
      } else {
        items = [];
        total = 0;
      }

      preencherTabela(items);

      // Aplica o cálculo linha a linha depois de renderizar
      items.forEach((p, index) => {
        const selectDesconto = document.querySelector(
          `#tabela-produtos-body tr:nth-child(${index + 1}) select`
        );
        if (selectDesconto) {
          const valor = Number(p.valor) || 0;
          const peso  = Number(p.peso_liquido) || 0;
          atualizarLinhaPorDesconto(selectDesconto, index, valor, peso);
        }
      });

      atualizarPaginacaoUI(total);
    })
    .catch((e) => console.error("Erro em carregarProdutos:", e));
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
      <td class="num">${(p.peso_liquido ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
      <td class="num">${(p.valor ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
      <td>
        <select onchange="atualizarLinhaPorDesconto(this, ${index}, ${p.valor}, ${p.peso_liquido || 0})">
            ${Object.entries(mapaDescontos).map(([codigo, percentual]) => `
              <option value="${codigo}" ${codigo == '15' ? 'selected' : ''}>
              ${codigo} - ${percentual}
              </option>
            `).join('')}
        </select>
      </td>
      <td id="acrescimo-${index}">0.0000</td>
      <td id="desconto-${index}">0.0000</td>
      <td id="valor_liquido-${index}" class="num">${(p.valor_liquido ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
    </tr>`;
    tbody.appendChild(tr);
  });
}

function atualizarLinhaPorDesconto(select, index, valorBase, peso_liquido = 0) {
  try{
  const idDesconto = select.value;
  const fator = mapaDescontos[idDesconto] || 0;

  const frete_kg = parseFloat(document.getElementById("frete_kg").value) || 0;

  const planoSelecionado = document.getElementById("plano_pagamento").value;
  const taxaCondicao = parseFloat(mapaCondicoesPagamento[planoSelecionado]) || 0;

  const acrescimoFrete = (frete_kg / 1000) * (peso_liquido || 0);
  const acrescimoCond = valorBase * taxaCondicao;
  const desconto = valorBase * fator;

  const valor_liquido = valorBase + acrescimoFrete + acrescimoCond - desconto;

  document.getElementById(`acrescimo-${index}`).innerText = (acrescimoFrete + acrescimoCond).toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
  document.getElementById(`desconto-${index}`).innerText = desconto.toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
  document.getElementById(`valor_liquido-${index}`).innerText = valor_liquido.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  } catch (error) {
    console.error("Erro ao calcular linha:", error);
  }
}


async function carregarGrupos() {
  try {
    const response = await fetch(`${API_BASE}/tabela_preco/filtro_grupo_produto`);
    if (!response.ok) throw new Error("Erro ao buscar grupos");

    const grupos = await response.json();
    const selectGrupo = document.getElementById("grupo");

    selectGrupo.innerHTML = "<option value=''>Todos os grupos</option>";

    grupos.forEach(item => {
      const grupo = item.grupo || item;  // cobre os dois casos: objeto ou string simples
      const option = document.createElement("option");
      option.value = grupo;
      option.textContent = grupo;
      selectGrupo.appendChild(option);
    });
  } catch (error) {
    console.error("Erro ao carregar grupos:", error);
  }
}

let mapaCondicoesPagamento = {};

async function carregarCondicoesPagamento() {
  try {
    const response = await fetch(`${API_BASE}/tabela_preco/condicoes_pagamento`);
    const condicoes = await response.json();

    const select = document.getElementById("plano_pagamento");
    select.innerHTML = "<option value=''>Selecione</option>";

    mapaCondicoesPagamento = {};
    condicoes.forEach(cond => {
      // 🔹 usa o nome correto do backend:
      mapaCondicoesPagamento[cond.codigo] = parseFloat(cond.taxa_condicao) || 0;

    const option = document.createElement("option");
      option.value = cond.codigo;
      option.textContent = `${cond.codigo} - ${cond.descricao}`;
      select.appendChild(option);
    });

    // ⬇️ Quando mudar o valor do select, recarrega os produtos
    select.addEventListener("change", recalcTabelaAtual);

  } catch (error) {
    console.error("Erro ao carregar condições de pagamento:", error);
  }
}

function recalcTabelaAtual() {
  const linhas = document.querySelectorAll("#tabela-produtos-body tr");
  linhas.forEach((linha, index) => {
    const selectDesconto = linha.querySelector("select");
    if (!selectDesconto) return;

    const valor = parseFloat(linha.children[5].innerText) || 0; // coluna Valor
    const peso  = parseFloat(linha.children[4].innerText) || 0; // coluna Peso Líquido
    atualizarLinhaPorDesconto(selectDesconto, index, valor, peso);
  });
}
let mapaDescontos = {};

async function carregarDescontos() {
    const response = await fetch(`${API_BASE}/tabela_preco/descontos`);
    const dados = await response.json();

    dados.forEach(item => {
        mapaDescontos[item.codigo] = item.percentual;
    });
}

async function salvarTabela() {
  try {
    const nome_tabela = document.getElementById("nome_tabela").value.trim();
    const cliente = document.getElementById("cliente").value.trim();
    const fornecedor = document.getElementById("fornecedor").value.trim();
    const validade_inicio = document.getElementById("validade_inicio").value;
    const validade_fim = document.getElementById("validade_fim").value;
    const plano_pagamento = document.getElementById("plano_pagamento").value || null;
    const frete_kg = parseFloat(document.getElementById("frete_kg").value) || 0;

    const linhas = document.querySelectorAll("#tabela-produtos-body tr");
    const produtosSelecionados = [];

    linhas.forEach((linha, index) => {
      const checkbox = linha.querySelector(".produto-checkbox");
      if (checkbox && checkbox.checked) {
        const codigo_tabela = linha.children[1].innerText;
        const descricao = linha.children[2].innerText;
        const embalagem = linha.children[3].innerText;
        const peso_liquido = parseFloat(linha.children[4].innerText) || 0;
        const valor = parseFloat(linha.children[5].innerText) || 0;
        const selectDesconto = linha.children[6].querySelector("select");
        const desconto_id = selectDesconto.value;
        const desconto_percentual = mapaDescontos[desconto_id] || 0;
        const acrescimo = parseFloat(document.getElementById(`acrescimo-${index}`).innerText) || 0;
        const valor_liquido = parseFloat(document.getElementById(`valor_liquido-${index}`).innerText) || 0;

        const produto = {
          nome_tabela,
          validade_inicio,
          validade_fim,
          cliente,
          fornecedor,

          codigo_tabela,
          descricao,
          embalagem,
          peso_liquido,
          peso_bruto: peso_liquido, // por enquanto igual
          valor,
          desconto: parseFloat((valor * desconto_percentual).toFixed(4)),
          acrescimo: parseFloat(acrescimo.toFixed(4)),
          fator_comissao: 0,
          plano_pagamento,
          frete_kg,
          frete_percentual: null,
          ipi: false,
          icms_st: false,
          valor_liquido,
          grupo: null,
          departamento: null
        };

        produtosSelecionados.push(produto);
      }
    });

    if (produtosSelecionados.length === 0) {
      alert("Selecione ao menos um produto para salvar.");
      return;
    }

    const payload = {
      nome_tabela,
      validade_inicio,
      validade_fim,
      cliente,
      fornecedor,
      produtos: produtosSelecionados
    };

    const response = await fetch(`${API_BASE}/tabela_preco/salvar`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const erro = await response.json();
      throw new Error(erro.detail || "Erro ao salvar a tabela de preços.");
    }

    const resultado = await response.json();
    alert(`✅ Tabela salva com sucesso! ${resultado.qtd_produtos} produtos incluídos.`);

    // Opcional: redirecionar ou limpar o formulário
    // window.location.href = "/tabela_preco/listar.html";

  } catch (error) {
    console.error("Erro ao salvar a tabela:", error);
    alert(`❌ Erro ao salvar a tabela: ${error.message}`);
  }
}


async function desativarTabela(id) {
  if (!confirm("Tem certeza que deseja desativar esta tabela?")) return;

  try {
    const response = await fetch(`${API_BASE}/tabela_preco/${id}`, { method: "DELETE" });
    if (!response.ok) throw new Error("Erro ao desativar.");

    alert("Tabela desativada com sucesso.");
    // nesta página não existe carregarTabelas(); redireciona para a lista
    window.location.href = "listar_tabelas.html";
  } catch (error) {
    console.error("Erro ao desativar:", error);
    alert("Erro ao desativar a tabela.");
  }
}

async function carregarTabelaSelecionada(id) {
  try {
    const response = await fetch(`${API_BASE}/tabela_preco/${id}`);
    if (!response.ok) throw new Error("Tabela não encontrada.");

    const tabela = await response.json();
    
    // Preenche os dados principais
    document.getElementById("nome_tabela").value = tabela.nome_tabela;
    document.getElementById("cliente").value = tabela.cliente;
    document.getElementById("fornecedor").value = tabela.fornecedor;
    document.getElementById("validade_inicio").value = tabela.validade_inicio;
    document.getElementById("validade_fim").value = tabela.validade_fim;
    document.getElementById("frete_kg").value = tabela.frete_kg || 0;

    // TODO: carregar produtos salvos (depois)
    preencherTabelaSalva(tabela.produtos || []);

    bloquearCampos();
    mostrarBotoesAcao();
  } catch (error) {
    console.error("Erro ao carregar tabela selecionada:", error);
    alert("Erro ao carregar tabela selecionada.");
  }
}

function bloquearCampos() {
  const inputs = document.querySelectorAll("input, select, textarea");
  inputs.forEach(el => el.disabled = true);
}

function desbloquearCampos() {
  const inputs = document.querySelectorAll("input, select, textarea");
  inputs.forEach(el => el.disabled = false);
}

// Mostra botões "Editar" e "Duplicar"
function mostrarBotoesAcao() {
  const container = document.createElement("div");
  container.id = "acoes-container";
  container.style.marginTop = "20px";

 const btnEditar = document.createElement("button");
btnEditar.innerText = "Editar";
btnEditar.className = "btn btn-editar";
btnEditar.onclick = () => {
  desbloquearCampos();
  mostrarBotoesSalvarCancelar();
};


  const btnDuplicar = document.createElement("button");
  btnDuplicar.innerText = "Duplicar";
  btnDuplicar.className = "btn btn-duplicar";
  btnDuplicar.onclick = () => {
    desbloquearCampos();
    document.getElementById("nome_tabela").value = "";
  };

  const btnDeletar = document.createElement("button");
  btnDeletar.innerText = "Excluir";
  btnDeletar.className = "btn btn-excluir";
  btnDeletar.style.marginLeft = "10px";
  btnDeletar.onclick = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get("id");
    if (id) desativarTabela(id);
  };

  container.appendChild(btnEditar);
  container.appendChild(btnDuplicar);
  container.appendChild(btnDeletar);

  const main = document.querySelector("main");
  main.appendChild(container);
}

function preencherTabelaSalva(produtos) {
  const tbody = document.getElementById("tabela-produtos-body");
  tbody.innerHTML = "";

  produtos.forEach((p, index) => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td><input type="checkbox" class="produto-checkbox" checked></td>
      <td>${p.codigo_tabela}</td>
      <td>${p.descricao}</td>
      <td>${p.embalagem ?? ""}</td>
      <td>${p.peso_liquido ?? ""}</td>
     <td>${(p.valor && p.valor > 0) ? p.valor.toFixed(2) : "<span style='color:red'>Produto sem valor</span>"}</td>
      <td>
        <select onchange="atualizarLinhaPorDesconto(this, ${index}, ${p.valor}, ${p.peso_liquido || 0})">
          ${Object.entries(mapaDescontos).map(([codigo, percentual]) => `
            <option value="${codigo}" ${
              (p.desconto && parseFloat(p.desconto / p.valor).toFixed(4) == percentual)
                ? "selected"
                : (!p.desconto && codigo == '15' ? 'selected' : '')
            }>
              ${codigo} - ${percentual}
            </option>

          `).join('')}
        </select>
      </td>
      <td id="acrescimo-${index}">${(p.acrescimo ?? 0).toFixed(4)}</td>
      <td id="desconto-${index}">${(p.desconto ?? 0).toFixed(4)}</td>
      <td id="valor_liquido-${index}"> ${(p.valor_liquido && p.valor_liquido > 0)? p.valor_liquido.toFixed(2): "<span style='color:red'>Produto sem valor</span>"}</td>
    `;

    tbody.appendChild(tr);
  });
}


function mostrarBotoesSalvarCancelar() {
  const container = document.getElementById("acoes-container");
  container.innerHTML = ""; // limpa botões anteriores

  const btnSalvar = document.createElement("button");
  btnSalvar.innerText = "Salvar Alterações";
  btnSalvar.className = "btn btn-salvar";
  btnSalvar.onclick = () => salvarEdicao();

  const btnCancelar = document.createElement("button");
  btnCancelar.innerText = "Cancelar";
  btnCancelar.className = "btn btn-cancelar";
  btnCancelar.style.marginLeft = "10px";
  btnCancelar.onclick = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get("id");
    if (id) {
      await carregarTabelaSelecionada(id);
    }
  };

  container.appendChild(btnSalvar);
  container.appendChild(btnCancelar);
}

async function salvarEdicao() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get("id");
    if (!id) {
      alert("ID da tabela não encontrado.");
      return;
    }

    const nome_tabela = document.getElementById("nome_tabela").value.trim();
    const cliente = document.getElementById("cliente").value.trim();
    const fornecedor = document.getElementById("fornecedor").value.trim();
    const validade_inicio = document.getElementById("validade_inicio").value;
    const validade_fim = document.getElementById("validade_fim").value;
    const plano_pagamento = document.getElementById("plano_pagamento").value || null;
    const frete_kg = parseFloat(document.getElementById("frete_kg").value) || 0;

    const linhas = document.querySelectorAll("#tabela-produtos-body tr");
    const produtosSelecionados = [];

    linhas.forEach((linha, index) => {
      const checkbox = linha.querySelector(".produto-checkbox");
      if (checkbox && checkbox.checked) {
        const codigo_tabela = linha.children[1].innerText;
        const descricao = linha.children[2].innerText;
        const embalagem = linha.children[3].innerText;
        const peso_liquido = parseFloat(linha.children[4].innerText) || 0;
        const valor = parseFloat(linha.children[5].innerText) || 0;
        const selectDesconto = linha.children[6].querySelector("select");
        const desconto_id = selectDesconto.value;
        const desconto_percentual = mapaDescontos[desconto_id] || 0;
        const acrescimo = parseFloat(document.getElementById(`acrescimo-${index}`).innerText) || 0;
        const valor_liquido = parseFloat(document.getElementById(`valor_liquido-${index}`).innerText) || 0;

        const produto = {
          nome_tabela,
          validade_inicio,
          validade_fim,
          cliente,
          fornecedor,

          codigo_tabela,
          descricao,
          embalagem,
          peso_liquido,
          peso_bruto: peso_liquido,
          valor,
          desconto: parseFloat((valor * desconto_percentual).toFixed(4)),
          acrescimo: parseFloat(acrescimo.toFixed(4)),
          fator_comissao: 0,
          plano_pagamento,
          frete_kg,
          frete_percentual: null,
          ipi: false,
          icms_st: false,
          valor_liquido,
          grupo: null,
          departamento: null
        };

        produtosSelecionados.push(produto);
      }
    });

    if (produtosSelecionados.length === 0) {
      alert("Selecione ao menos um produto para salvar.");
      return;
    }

    const payload = {
      nome_tabela,
      validade_inicio,
      validade_fim,
      cliente,
      fornecedor,
      produtos: produtosSelecionados
    };

    const response = await fetch(`${API_BASE}/tabela_preco/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const erro = await response.json();
      throw new Error(erro.detail || "Erro ao atualizar a tabela.");
    }

    alert("✅ Tabela atualizada com sucesso!");
    window.location.href = "listar_tabelas.html";
  } catch (error) {
    console.error("Erro ao salvar edição:", error);
    alert(`❌ Erro ao salvar alterações: ${error.message}`);
  }
}

function atualizarPaginacaoUI(total) {
  const info = document.getElementById("pagina-info");
  const btnPrev = document.getElementById("btn-prev");
  const btnNext = document.getElementById("btn-next");

  if (!info) return;

  if (total == null) {
    // backend não retornou total: não dá pra saber os limites
    totalPages = null;
    info.textContent = "";
    if (btnPrev) btnPrev.disabled = (currentPage <= 1);
    if (btnNext) btnNext.disabled = false; // sem total, não limitamos "Próxima"
    return;
  }

  totalPages = Math.max(1, Math.ceil(total / pageSize));
  info.textContent = `Página ${currentPage} de ${totalPages}`;

  if (btnPrev) btnPrev.disabled = (currentPage <= 1);
  if (btnNext) btnNext.disabled = (currentPage >= totalPages);
}

function gotoPrevPage() {
  if (currentPage > 1) {
    carregarProdutos(currentPage - 1);
  }
}

function gotoNextPage() {
  // Se conhecemos o total, respeita o limite
  if (totalPages != null && currentPage >= totalPages) return;
  carregarProdutos(currentPage + 1);
}
 

function coletarEstadoTela() {
  const estado = {
    campos: {
      nome_tabela: document.getElementById("nome_tabela")?.value || "",
      cliente: document.getElementById("cliente")?.value || "",
      fornecedor: document.getElementById("fornecedor")?.value || "",
      grupo: document.getElementById("grupo")?.value || "",
      validade_inicio: document.getElementById("validade_inicio")?.value || "",
      validade_fim: document.getElementById("validade_fim")?.value || "",
      frete_kg: document.getElementById("frete_kg")?.value || "0",
      plano_pagamento: document.getElementById("plano_pagamento")?.value || ""
    },
    // guarda produtos selecionados e o desconto escolhido por produto (chave = codigo)
    selecionados: Array.from(document.querySelectorAll("#tabela-produtos-body tr"))
      .map(linha => {
        const chk = linha.querySelector(".produto-checkbox");
        if (!chk || !chk.checked) return null;
        const codigo = linha.children[1].innerText;
        const descontoId = linha.children[6].querySelector("select")?.value || null;
        return { codigo, descontoId };
      })
      .filter(Boolean)
  };
  return estado;
}

function salvarEstadoTela() {
  try {
    const estado = coletarEstadoTela();
    sessionStorage.setItem("tabela_preco_state", JSON.stringify(estado));
  } catch (e) {
    console.warn("Não foi possível salvar o estado:", e);
  }
}

async function restaurarEstadoTela() {
  try {
    const raw = sessionStorage.getItem("tabela_preco_state");
    if (!raw) return;
    const estado = JSON.parse(raw);

    // 1) Restaura campos
    for (const [k, v] of Object.entries(estado.campos || {})) {
      const el = document.getElementById(k);
      if (el) el.value = v;
    }

    // 2) Se mudou o grupo, recarrega produtos dessa lista antes de aplicar seleções
    //    (se já chamou carregarProdutos() antes, chame de novo com currentPage=1)
    currentPage = 1;
    await carregarProdutos();

    // 3) Reaplica seleções de produtos e descontos
    const mapSel = new Map((estado.selecionados || []).map(s => [s.codigo, s.descontoId]));
    const linhas = document.querySelectorAll("#tabela-produtos-body tr");
    linhas.forEach((linha, idx) => {
      const codigo = linha.children[1].innerText;
      if (mapSel.has(codigo)) {
        // marcar checkbox
        const chk = linha.querySelector(".produto-checkbox");
        if (chk) chk.checked = true;

        // selecionar desconto salvo
        const descontoId = mapSel.get(codigo);
        const selectDesconto = linha.children[6].querySelector("select");
        if (selectDesconto && descontoId) {
          selectDesconto.value = descontoId;
          // recalcular a linha com o desconto reaplicado
          const valor = parseFloat(linha.children[5].innerText) || 0;
          const peso  = parseFloat(linha.children[4].innerText) || 0;
          atualizarLinhaPorDesconto(selectDesconto, idx, valor, peso);
        }
      }
    });
  } catch (e) {
    console.warn("Não foi possível restaurar o estado:", e);
  }
}


window.addEventListener("beforeunload", salvarEstadoTela);

window.onload = async function() {
    await carregarDescontos();
    await carregarCondicoesPagamento();
    await carregarGrupos(); 
    const selectGrupo = document.getElementById("grupo");
const DEFAULT = "AVES"; // <- mude aqui o grupo a ser iniciado.
const opt = Array.from(selectGrupo.options).find(o => o.value === DEFAULT);
if (opt) selectGrupo.value = DEFAULT;

const linkVer = document.getElementById("link-ver-tabelas");
if (linkVer) {
  linkVer.addEventListener("click", () => {
    salvarEstadoTela();
  });
}

// Se quiser manter um default, aplique só se não houver estado salvo.
  const estadoSalvo = sessionStorage.getItem("tabela_preco_state");
  if (!estadoSalvo) {
    const selectGrupo = document.getElementById("grupo");
    const DEFAULT = "AVES";
    const opt = Array.from(selectGrupo.options).find(o => o.value === DEFAULT);
    if (opt) selectGrupo.value = DEFAULT;
    carregarProdutos();
  } else {
    await restaurarEstadoTela(); // isto já chama carregarProdutos internamente
  }

  // Se estiver carregando uma tabela por id, mantém tua lógica:
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get("id");
  if (id) {
    await carregarTabelaSelecionada(id);
    document.getElementById("btn-salvar-principal").style.display = "none";
  }


};