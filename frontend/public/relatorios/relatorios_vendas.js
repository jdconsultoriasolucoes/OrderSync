/**
 * relatorios_vendas.js
 * Gerenciamento e lógica do Módulo de Relatórios (Vendas por Cliente e Vendas por Produto)
 */

var API_BASE = window.API_BASE || window.location.origin;

// DOM Elements
const inDataInicio = document.getElementById("filtro-data-inicio");
const inDataFim = document.getElementById("filtro-data-fim");
const selFilial = document.getElementById("filtro-filial");
const selCategoria = document.getElementById("filtro-categoria");
const selStatus = document.getElementById("filtro-status");
const selMunicipio = document.getElementById("filtro-municipio");
const selGrupo = document.getElementById("filtro-grupo");
const divFiltroGrupo = document.getElementById("campo-filtro-grupo");

const btnFiltrar = document.getElementById("btn-filtrar");
const btnLimpar = document.getElementById("btn-limpar-filtros");
const btnExportar = document.getElementById("btn-exportar-excel");

const tbody = document.getElementById("vendas-tbody");
const tfoot = document.getElementById("vendas-tfoot");
const tableHeaders = document.querySelector("#tabela-vendas thead");
const loadingEl = document.getElementById("loading");
const emptyStateEl = document.getElementById("empty-state");

const txtTitulo = document.getElementById("titulo-relatorio-principal");

const menuButtons = document.querySelectorAll("#relatorios-menu-vendas button");

// State
let activeReport = "cliente"; // "cliente" ou "produto"
let listagemVendas = [];
let sortState = {
    col: null,
    desc: false
};

// Formatter Helpers
function fmtMoney(val) {
    if (val === null || val === undefined) return "R$ 0,00";
    return parseFloat(val).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function fmtPeso(val) {
    if (val === null || val === undefined || val === "" || isNaN(parseFloat(val))) return "0 kg";
    return Math.round(parseFloat(val)).toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + " kg";
}

document.addEventListener("DOMContentLoaded", async () => {
    // 1. Configurar datas padrão (Início do mês atual até Hoje)
    const hoje = new Date();
    const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    
    const formatLocalDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    inDataInicio.value = formatLocalDate(primeiroDia);
    inDataFim.value = formatLocalDate(hoje);

    // 2. Registrar Eventos dos Botões do Menu Lateral (Troca de Relatórios)
    menuButtons.forEach(btn => {
        btn.addEventListener("click", async (e) => {
            menuButtons.forEach(b => b.classList.remove("active"));
            e.currentTarget.classList.add("active");
            
            activeReport = e.currentTarget.dataset.report;
            sortState = { col: null, desc: false }; // reseta ordenação
            
            alternarRelatorioUI();
            await buscarDadosRelatorio();
        });
    });

    // 3. Carregar metadados dos seletores do Backend
    await carregarFiltrosMetadata();

    // 4. Configurar cabeçalhos iniciais
    alternarRelatorioUI();

    // 5. Executar primeira busca automática
    await buscarDadosRelatorio();

    // 6. Registrar Listeners de Ações
    btnFiltrar.addEventListener("click", buscarDadosRelatorio);
    btnLimpar.addEventListener("click", limparTodosFiltros);
    btnExportar.addEventListener("click", exportarExcel);
});

/**
 * Altera cabeçalhos, títulos e visibilidade dos filtros conforme relatório ativo
 */
function alternarRelatorioUI() {
    if (activeReport === "cliente") {
        txtTitulo.textContent = "Relatório de Vendas por Cliente";
        divFiltroGrupo.style.display = "none";
        selGrupo.value = ""; // limpa filtro de grupo
        
        // Cabeçalhos para Vendas por Cliente
        tableHeaders.innerHTML = `
            <tr>
                <th data-sort="numero_pedido">Nº Pedido Sistema</th>
                <th data-sort="pedido_supra">Pedido Supra</th>
                <th data-sort="danfe">Danfe</th>
                <th data-sort="codigo_cliente">Código Cliente</th>
                <th data-sort="cliente">Cliente</th>
                <th data-sort="nome_fantasia">Nome Fantasia</th>
                <th data-sort="municipio">Município</th>
                <th data-sort="peso_liquido" class="tar">Peso Líquido (kg)</th>
                <th data-sort="valor_sem_frete" class="tar">Valor Sem Frete</th>
                <th data-sort="valor_com_frete" class="tar">Valor Com Frete</th>
            </tr>
        `;
    } else {
        txtTitulo.textContent = "Relatório de Vendas por Produto";
        divFiltroGrupo.style.display = "flex";
        
        // Cabeçalhos para Vendas por Produto
        tableHeaders.innerHTML = `
            <tr>
                <th data-sort="codigo_produto">Código Produto</th>
                <th data-sort="produto">Produto</th>
                <th data-sort="embalagem">Embalagem</th>
                <th data-sort="peso_liquido_unitario" class="tar">Peso Líq. Unit.</th>
                <th data-sort="quantidade" class="tar">Quantidade</th>
                <th data-sort="peso_liquido_acumulado" class="tar">Peso Líq. Acum (kg)</th>
                <th data-sort="valor_sem_frete" class="tar">Valor Sem Frete</th>
                <th data-sort="valor_com_frete" class="tar">Valor Com Frete</th>
            </tr>
        `;
    }

    // Registrar clique de ordenação interativa nas novas colunas injetadas
    registrarOrdenacaoTabela();
}

/**
 * Busca os valores distintos no banco de dados para popular os seletores de filtros
 */
async function carregarFiltrosMetadata() {
    try {
        const token = window.Auth ? window.Auth.getToken() : '';
        const resp = await fetch(`${API_BASE}/api/relatorios/vendas_cliente/filtros`, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!resp.ok) throw new Error("Erro ao buscar metadados de filtros");
        const data = await resp.json();

        // Popular Filiais
        if (data.filiais) {
            data.filiais.forEach(f => {
                const opt = document.createElement("option");
                opt.value = f;
                opt.textContent = f;
                selFilial.appendChild(opt);
            });
        }

        // Popular Status
        if (data.status) {
            data.status.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s;
                opt.textContent = s;
                selStatus.appendChild(opt);
            });
        }

        // Popular Municípios
        if (data.municipios) {
            data.municipios.forEach(m => {
                const opt = document.createElement("option");
                opt.value = m;
                opt.textContent = m;
                selMunicipio.appendChild(opt);
            });
        }

        // Popular Grupos
        if (data.grupos) {
            data.grupos.forEach(g => {
                const opt = document.createElement("option");
                opt.value = g;
                opt.textContent = g;
                selGrupo.appendChild(opt);
            });
        }
    } catch (err) {
        console.error("Falha ao carregar metadados dos filtros:", err);
    }
}

/**
 * Realiza a requisição ao Backend e renderiza o relatório aplicando os parâmetros
 */
async function buscarDadosRelatorio() {
    tbody.innerHTML = "";
    tfoot.innerHTML = "";
    emptyStateEl.style.display = "none";
    loadingEl.style.display = "block";

    // Constroi query string
    const queryParams = new URLSearchParams();
    if (inDataInicio.value) queryParams.append("data_inicio", inDataInicio.value);
    if (inDataFim.value) queryParams.append("data_fim", inDataFim.value);
    if (selFilial.value) queryParams.append("filiais", selFilial.value);
    if (selCategoria.value) queryParams.append("categoria", selCategoria.value);
    if (selStatus.value) queryParams.append("status_list", selStatus.value);
    if (selMunicipio.value) queryParams.append("municipios", selMunicipio.value);
    if (activeReport === "produto" && selGrupo.value) queryParams.append("grupos", selGrupo.value);

    // Seleciona endpoint conforme relatório ativo
    const endpoint = activeReport === "cliente" ? "vendas_cliente" : "vendas_produtos";

    try {
        const token = window.Auth ? window.Auth.getToken() : '';
        const resp = await fetch(`${API_BASE}/api/relatorios/${endpoint}?${queryParams.toString()}`, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!resp.ok) throw new Error("Erro na requisição ao servidor");
        listagemVendas = await resp.json();

        // Se houver ordenação ativa, mantemos o ordenamento atualizado dos novos dados
        if (sortState.col) {
            ordenarDados(sortState.col, sortState.desc);
        }

        renderizarTabela();
    } catch (err) {
        console.error(`Falha ao buscar relatório de ${activeReport}:`, err);
        tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--os-error); font-weight: 600;">Falha ao carregar dados do relatório.</td></tr>`;
    } finally {
        loadingEl.style.display = "none";
    }
}

/**
 * Renderiza as linhas na tabela e calcula os totais dinâmicos
 */
function renderizarTabela() {
    if (listagemVendas.length === 0) {
        emptyStateEl.style.display = "block";
        tfoot.innerHTML = "";
        return;
    }

    let html = "";
    let totalPeso = 0;
    let totalSemFrete = 0;
    let totalComFrete = 0;

    if (activeReport === "cliente") {
        listagemVendas.forEach(item => {
            totalPeso += parseFloat(item.peso_liquido || 0);
            totalSemFrete += parseFloat(item.valor_sem_frete || 0);
            totalComFrete += parseFloat(item.valor_com_frete || 0);

            html += `
                <tr>
                    <td><strong>${item.numero_pedido || "-"}</strong></td>
                    <td><strong>${item.pedido_supra || "-"}</strong></td>
                    <td>${item.danfe || "-"}</td>
                    <td>${item.codigo_cliente || "-"}</td>
                    <td>${item.cliente || "-"}</td>
                    <td>${item.nome_fantasia || "-"}</td>
                    <td>${item.municipio || "-"}</td>
                    <td class="tar">${fmtPeso(item.peso_liquido)}</td>
                    <td class="tar">${fmtMoney(item.valor_sem_frete)}</td>
                    <td class="tar">${fmtMoney(item.valor_com_frete)}</td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;

        // Rodapé dinâmico Vendas por Cliente (colspan 7 para alinhar totais)
        tfoot.innerHTML = `
            <tr>
                <td colspan="7">Total Acumulado</td>
                <td class="tar" id="total-peso">${fmtPeso(totalPeso)}</td>
                <td class="tar" id="total-valor-sem">${fmtMoney(totalSemFrete)}</td>
                <td class="tar" id="total-valor-com">${fmtMoney(totalComFrete)}</td>
            </tr>
        `;
    } else {
        // Relatório de Vendas por Produto
        listagemVendas.forEach(item => {
            totalPeso += parseFloat(item.peso_liquido_acumulado || 0);
            totalSemFrete += parseFloat(item.valor_sem_frete || 0);
            totalComFrete += parseFloat(item.valor_com_frete || 0);

            html += `
                <tr>
                    <td><strong>${item.codigo_produto || "-"}</strong></td>
                    <td>${item.produto || "-"}</td>
                    <td>${item.embalagem || "-"}</td>
                    <td class="tar">${fmtPeso(item.peso_liquido_unitario).replace(' kg', '')}</td>
                    <td class="tar">${parseFloat(item.quantidade || 0).toLocaleString("pt-BR")}</td>
                    <td class="tar">${fmtPeso(item.peso_liquido_acumulado)}</td>
                    <td class="tar">${fmtMoney(item.valor_sem_frete)}</td>
                    <td class="tar">${fmtMoney(item.valor_com_frete)}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;

        // Rodapé dinâmico Vendas por Produto (colspan 5 para alinhar totais)
        tfoot.innerHTML = `
            <tr>
                <td colspan="5">Total Acumulado</td>
                <td class="tar" id="total-peso">${fmtPeso(totalPeso)}</td>
                <td class="tar" id="total-valor-sem">${fmtMoney(totalSemFrete)}</td>
                <td class="tar" id="total-valor-com">${fmtMoney(totalComFrete)}</td>
            </tr>
        `;
    }
}

/**
 * Adiciona eventos de ordenação interativa nos cabeçalhos da tabela
 */
function registrarOrdenacaoTabela() {
    const headers = tableHeaders.querySelectorAll("th[data-sort]");
    
    headers.forEach(th => {
        const colKey = th.dataset.sort;
        th.classList.add("sortable-header");
        
        // Remove qualquer indicador duplicado anterior
        const oldInd = th.querySelector(".sort-indicator");
        if (oldInd) oldInd.remove();

        // Injeta indicador de ordenação
        const indicator = document.createElement("span");
        indicator.className = "sort-indicator";
        indicator.style.marginLeft = "6px";
        
        // Verifica se é a coluna ativa na ordenação
        if (sortState.col === colKey) {
            indicator.innerHTML = sortState.desc ? " &darr;" : " &uarr;";
            indicator.style.opacity = "1";
            th.style.color = "var(--os-primary)";
        } else {
            indicator.innerHTML = " &bull;";
            indicator.style.opacity = "0.3";
        }
        th.appendChild(indicator);

        // Click event listener
        th.addEventListener("click", () => {
            if (sortState.col === colKey) {
                sortState.desc = !sortState.desc;
            } else {
                sortState.col = colKey;
                sortState.desc = false;
            }

            // Ordena os dados em memória e atualiza a interface
            ordenarDados(colKey, sortState.desc);
            
            // Re-renderiza o cabeçalho para atualizar as setinhas
            alternarRelatorioUI();
            
            // Renderiza as linhas
            renderizarTabela();
        });
    });
}

/**
 * Ordena o array listagemVendas em memória com base na chave e direção informada
 */
function ordenarDados(colKey, desc) {
    listagemVendas.sort((a, b) => {
        let va = a[colKey];
        let vb = b[colKey];

        if (va === null || va === undefined) va = "";
        if (vb === null || vb === undefined) vb = "";

        // Trata ordenação numérica
        if (!isNaN(parseFloat(va)) && isFinite(va)) {
            va = parseFloat(va);
            vb = parseFloat(vb);
        } else {
            va = String(va).toLowerCase();
            vb = String(vb).toLowerCase();
        }

        if (va < vb) return desc ? 1 : -1;
        if (va > vb) return desc ? -1 : 1;
        return 0;
    });
}

/**
 * Limpa todos os filtros e executa uma nova busca do período padrão
 */
async function limparTodosFiltros() {
    const hoje = new Date();
    const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    
    const formatLocalDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    inDataInicio.value = formatLocalDate(primeiroDia);
    inDataFim.value = formatLocalDate(hoje);
    selFilial.value = "";
    selCategoria.value = "";
    selStatus.value = "";
    selMunicipio.value = "";
    selGrupo.value = "";

    await buscarDadosRelatorio();
}

/**
 * Exporta os dados exibidos atualmente na tabela em formato compatível com Excel (CSV formatado)
 */
function exportarExcel() {
    if (listagemVendas.length === 0) {
        alert("Não há dados carregados para exportar.");
        return;
    }

    let csv = "";
    let filename = "";
    
    let totalPeso = 0;
    let totalSemFrete = 0;
    let totalComFrete = 0;

    const clean = (txt) => txt ? String(txt).replace(/;/g, ",").replace(/"/g, '""').trim() : "-";

    if (activeReport === "cliente") {
        csv = "Nº Pedido Sistema;Pedido Supra;Danfe;Código Cliente;Cliente;Nome Fantasia;Município;Peso Líquido (kg);Valor Sem Frete;Valor Com Frete\n";
        filename = "relatorio_vendas_por_cliente";

        listagemVendas.forEach(item => {
            const p = parseFloat(item.peso_liquido || 0);
            const vs = parseFloat(item.valor_sem_frete || 0);
            const vc = parseFloat(item.valor_com_frete || 0);

            totalPeso += p;
            totalSemFrete += vs;
            totalComFrete += vc;

            csv += `"${clean(item.numero_pedido)}";"${clean(item.pedido_supra)}";"${clean(item.danfe)}";"${clean(item.codigo_cliente)}";"${clean(item.cliente)}";"${clean(item.nome_fantasia)}";"${clean(item.municipio)}";"${Math.round(p)}";"${vs.toFixed(2).replace('.', ',')}";"${vc.toFixed(2).replace('.', ',')}"\n`;
        });

        csv += `"TOTAL ACUMULADO";"";"";"";"";"";"";"${Math.round(totalPeso)}";"${totalSemFrete.toFixed(2).replace('.', ',')}";"${totalComFrete.toFixed(2).replace('.', ',')}"\n`;

    } else {
        // Vendas por Produto
        csv = "Código Produto;Produto;Embalagem;Peso Líq. Unit. (kg);Quantidade;Peso Líq. Acumulado (kg);Valor Sem Frete;Valor Com Frete\n";
        filename = "relatorio_vendas_por_produto";

        listagemVendas.forEach(item => {
            const pu = parseFloat(item.peso_liquido_unitario || 0);
            const q = parseFloat(item.quantidade || 0);
            const pa = parseFloat(item.peso_liquido_acumulado || 0);
            const vs = parseFloat(item.valor_sem_frete || 0);
            const vc = parseFloat(item.valor_com_frete || 0);

            totalPeso += pa;
            totalSemFrete += vs;
            totalComFrete += vc;

            csv += `"${clean(item.codigo_produto)}";"${clean(item.produto)}";"${clean(item.embalagem)}";"${Math.round(pu)}";"${q}";"${Math.round(pa)}";"${vs.toFixed(2).replace('.', ',')}";"${vc.toFixed(2).replace('.', ',')}"\n`;
        });

        csv += `"TOTAL ACUMULADO";"";"";"";"";"${Math.round(totalPeso)}";"${totalSemFrete.toFixed(2).replace('.', ',')}";"${totalComFrete.toFixed(2).replace('.', ',')}"\n`;
    }

    // Utiliza BOM (\ufeff) para forçar o Excel a interpretar os caracteres especiais em UTF-8 no Windows
    const blob = new Blob(["\ufeff" + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
