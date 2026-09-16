/**
 * relatorios_vendas.js
 * Gerenciamento e lógica do Módulo de Relatórios (Vendas por Cliente e Vendas por Produto)
 */

var API_BASE = window.API_BASE || window.location.origin;

// DOM Elements
const inDataInicio = document.getElementById("filtro-data-inicio");
const inDataFim = document.getElementById("filtro-data-fim");
const inFaturamentoInicio = document.getElementById("filtro-faturamento-inicio");
const inFaturamentoFim = document.getElementById("filtro-faturamento-fim");
const selFilial = document.getElementById("filtro-filial");
const selCategoria = document.getElementById("filtro-categoria");
const selStatus = document.getElementById("filtro-status");
const selMunicipio = document.getElementById("filtro-municipio");
const selGrupo = document.getElementById("filtro-grupo");
const divFiltroGrupo = document.getElementById("campo-filtro-grupo");

// Elementos Filtro Gerencial
const inGerencialCodigo = document.getElementById("filtro-gerencial-codigo");
const inGerencialDoc = document.getElementById("filtro-gerencial-documento");
const inGerencialNome = document.getElementById("filtro-gerencial-nome");
const selGerencialMun = document.getElementById("filtro-gerencial-municipio");
const selGerencialVend = document.getElementById("filtro-gerencial-vendedor");
const inGerencialDataInicio = document.getElementById("filtro-gerencial-data-inicio");
const inGerencialDataFim = document.getElementById("filtro-gerencial-data-fim");
const inGerencialObs = document.getElementById("filtro-gerencial-observacao");

const btnLimpar = document.getElementById("btn-limpar-filtros");
const btnExportar = document.getElementById("btn-exportar-excel");

const tbody = document.getElementById("vendas-tbody");
const tfoot = document.getElementById("vendas-tfoot");
const tableHeaders = document.querySelector("#tabela-vendas thead");
const loadingEl = document.getElementById("loading");
const emptyStateEl = document.getElementById("empty-state");

const txtTitulo = document.getElementById("titulo-relatorio-principal");

const menuButtons = document.querySelectorAll(".relatorios-menu button");

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

function fmtData(dateStr) {
    if (!dateStr) return "-";
    // Extrai apenas a data se vier com formato ISO
    const onlyDate = dateStr.split('T')[0];
    const parts = onlyDate.split('-');
    if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return dateStr;
}

function limparNomeCliente(nome) {
    if (!nome) return "-";
    return nome.replace(/\s*-\s*(\d{2,3}\.\d{3}\.\d{3}(\/\d{4})?-\d{2})$/, '').trim();
}

function fmtDoc(s) {
    const d = String(s || '').replace(/\D/g, '');
    if (d.length === 14) return d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
    if (d.length === 11) return d.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
    return s || '';
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
    btnLimpar.addEventListener("click", limparTodosFiltros);
    btnExportar.addEventListener("click", exportarExcel);

    // 7. Auto-filtragem nos inputs e selects
    let debounceTimer;
    document.querySelectorAll('.filtro-campo .os-input, .filtro-campo .os-select').forEach(el => {
        const evType = (el.tagName === 'SELECT' || el.type === 'date') ? 'change' : 'input';
        el.addEventListener(evType, () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                buscarDadosRelatorio();
            }, 600);
        });
    });
});

/**
 * Altera cabeçalhos, títulos e visibilidade dos filtros conforme relatório ativo
 */
function alternarRelatorioUI() {
    // Alterna a visibilidade dos campos de filtro
    const todosFiltros = document.querySelectorAll(".filtro-campo");
    todosFiltros.forEach(f => {
        if (f.classList.contains("filtro-gerencial")) {
            f.style.display = (activeReport === "gerencial") ? "flex" : "none";
        } else if (f.classList.contains("filtro-gerencial2")) {
            f.style.display = (activeReport === "gerencial2") ? "flex" : "none";
        } else {
            if (f.id === "campo-filtro-grupo") {
                f.style.display = activeReport === "produto" ? "flex" : "none";
            } else {
                f.style.display = (activeReport === "gerencial" || activeReport === "gerencial2") ? "none" : "flex";
            }
        }
    });

    if (activeReport === "cliente") {
        txtTitulo.textContent = "Relatório de Vendas por Cliente";
        
        // Cabeçalhos para Vendas por Cliente com Linha de Totais no Topo
        tableHeaders.innerHTML = `
            <tr>
                <th>#</th>
                <th data-sort="numero_pedido">Nº Pedido Sistema</th>
                <th data-sort="pedido_supra" class="col-pedido-supra">Pedido Supra</th>
                <th data-sort="danfe">Danfe</th>
                <th data-sort="data_faturamento">Data Faturamento</th>
                <th data-sort="codigo_cliente">Código Cliente</th>
                <th data-sort="cliente">Cliente</th>
                <th data-sort="nome_fantasia">Nome Fantasia</th>
                <th data-sort="municipio">Município</th>
                <th data-sort="peso_liquido" class="tar">Peso Líquido (kg)</th>
                <th data-sort="valor_sem_frete" class="tar col-money">Valor Sem Frete</th>
                <th data-sort="valor_com_frete" class="tar col-money">Valor Com Frete</th>
            </tr>
            <tr style="background-color: #f1f5f9; font-weight: bold; position: sticky; top: 38px; z-index: 14; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <td colspan="9" style="text-align: left; padding: 10px 16px; font-weight: bold; border-bottom: 2px solid var(--os-border);">Total Acumulado</td>
                <td class="tar" id="total-peso" style="font-weight: bold; border-bottom: 2px solid var(--os-border);">0 kg</td>
                <td class="tar col-money" id="total-valor-sem" style="font-weight: bold; border-bottom: 2px solid var(--os-border);">R$ 0,00</td>
                <td class="tar col-money" id="total-valor-com" style="font-weight: bold; border-bottom: 2px solid var(--os-border);">R$ 0,00</td>
            </tr>
        `;
    } else if (activeReport === "produto") {
        txtTitulo.textContent = "Relatório de Vendas por Produto";
        
        // Cabeçalhos para Vendas por Produto com Linha de Totais no Topo
        tableHeaders.innerHTML = `
            <tr>
                <th>#</th>
                <th data-sort="codigo_produto">Código Produto</th>
                <th data-sort="produto">Produto</th>
                <th data-sort="embalagem">Embalagem</th>
                <th data-sort="peso_liquido_unitario" class="tar">Peso Líq. Unit.</th>
                <th data-sort="quantidade" class="tar">Quantidade</th>
                <th data-sort="peso_liquido_acumulado" class="tar">Peso Líq. Acum (kg)</th>
                <th data-sort="valor_sem_frete" class="tar col-money">Valor Sem Frete</th>
                <th data-sort="valor_com_frete" class="tar col-money">Valor Com Frete</th>
            </tr>
            <tr style="background-color: #f1f5f9; font-weight: bold; position: sticky; top: 38px; z-index: 14; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <td colspan="6" style="text-align: left; padding: 10px 16px; font-weight: bold; border-bottom: 2px solid var(--os-border);">Total Acumulado</td>
                <td class="tar" id="total-peso" style="font-weight: bold; border-bottom: 2px solid var(--os-border);">0 kg</td>
                <td class="tar col-money" id="total-valor-sem" style="font-weight: bold; border-bottom: 2px solid var(--os-border);">R$ 0,00</td>
                <td class="tar col-money" id="total-valor-com" style="font-weight: bold; border-bottom: 2px solid var(--os-border);">R$ 0,00</td>
            </tr>
        `;
    } else if (activeReport === "gerencial") {
        txtTitulo.textContent = "Relatório Gerencial";
        
        // Cabeçalhos para Relatório Gerencial
        tableHeaders.innerHTML = `
            <tr>
                <th>#</th>
                <th data-sort="documento" style="white-space: nowrap;">CNPJ/CPF</th>
                <th data-sort="nome_cliente">Nome Cliente</th>
                <th data-sort="municipio">Município</th>
                <th data-sort="vendedor">Vendedor</th>
                <th data-sort="data_ultima_compra">Data Última Compra</th>
                <th data-sort="observacao">Observação</th>
            </tr>
        `;
    } else if (activeReport === "gerencial2") {
        txtTitulo.textContent = "Relatório Gerencial 2 - Evolução de Vendas";
        
        const mesesSel = document.getElementById("filtro-gerencial2-meses");
        const qtdeMeses = mesesSel ? parseInt(mesesSel.value) : 12;
        gerencial2Meses = generateLastXMonths(qtdeMeses);
        
        let htmlHeader1 = `<tr>
            <th rowspan="2" style="width: 40px; min-width: 40px; border-right: 1px solid var(--os-border);">#</th>
            <th rowspan="2" data-sort="codigo_cliente" style="min-width: 100px; border-right: 1px solid var(--os-border);">Cód. Cliente</th>
            <th rowspan="2" data-sort="cliente" style="min-width: 250px; border-right: 1px solid var(--os-border);">Cliente</th>`;
        let htmlHeader2 = `<tr>`;
        
        gerencial2Meses.forEach((m, i) => {
            const [ano, mes] = m.split('-');
            const borderLeft = "border-left: 2px solid #cbd5e1;";
            htmlHeader1 += `<th colspan="2" style="text-align: center; border-bottom: 1px solid var(--os-border); background-color: #f8fafc; ${borderLeft}">${mes}/${ano}</th>`;
            htmlHeader2 += `<th class="tar" style="${borderLeft}">Peso (kg)</th><th class="tar col-money">Valor (R$)</th>`;
        });
        
        htmlHeader1 += `</tr>`;
        htmlHeader2 += `</tr>`;
        
        tableHeaders.innerHTML = htmlHeader1 + htmlHeader2;
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
                
                const optG = document.createElement("option");
                optG.value = m;
                optG.textContent = m;
                selGerencialMun.appendChild(optG);
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
        
        // Popular Filtros Gerenciais
        const respGerencial = await fetch(`${API_BASE}/api/relatorios/gerencial/filtros`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (respGerencial.ok) {
            const dataG = await respGerencial.json();
            if (dataG.municipios) {
                dataG.municipios.forEach(m => {
                    const opt = document.createElement("option");
                    opt.value = m;
                    opt.textContent = m;
                    selGerencialMun.appendChild(opt);
                });
            }
            if (dataG.vendedores) {
                dataG.vendedores.forEach(v => {
                    const opt = document.createElement("option");
                    opt.value = v;
                    opt.textContent = v;
                    selGerencialVend.appendChild(opt);
                });
            }
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
    
    if (activeReport === "gerencial") {
        if (inGerencialCodigo.value) queryParams.append("codigo_cliente", inGerencialCodigo.value);
        if (inGerencialDoc.value) queryParams.append("cnpj_cpf", inGerencialDoc.value);
        if (inGerencialNome.value) queryParams.append("nome_cliente", inGerencialNome.value);
        if (selGerencialMun.value) queryParams.append("municipio", selGerencialMun.value);
        if (selGerencialVend.value) queryParams.append("vendedor", selGerencialVend.value);
        if (inGerencialDataInicio.value) queryParams.append("data_compra_inicio", inGerencialDataInicio.value);
        if (inGerencialDataFim.value) queryParams.append("data_compra_fim", inGerencialDataFim.value);
        if (inGerencialObs.value) queryParams.append("observacao", inGerencialObs.value);
    } else if (activeReport === "gerencial2") {
        const inG2Cod = document.getElementById("filtro-gerencial2-codigo");
        const inG2Nome = document.getElementById("filtro-gerencial2-nome");
        const selG2Meses = document.getElementById("filtro-gerencial2-meses");
        
        if (inG2Cod && inG2Cod.value) queryParams.append("codigo_cliente", inG2Cod.value);
        if (inG2Nome && inG2Nome.value) queryParams.append("nome_cliente", inG2Nome.value);
        if (selG2Meses && selG2Meses.value) queryParams.append("meses", selG2Meses.value);
    } else {
        if (inDataInicio.value) queryParams.append("data_inicio", inDataInicio.value);
        if (inDataFim.value) queryParams.append("data_fim", inDataFim.value);
        if (inFaturamentoInicio.value) queryParams.append("faturamento_inicio", inFaturamentoInicio.value);
        if (inFaturamentoFim.value) queryParams.append("faturamento_fim", inFaturamentoFim.value);
        if (selFilial.value) queryParams.append("filiais", selFilial.value);
        if (selCategoria.value) queryParams.append("categoria", selCategoria.value);
        if (selStatus.value) queryParams.append("status_list", selStatus.value);
        if (selMunicipio.value) queryParams.append("municipios", selMunicipio.value);
        if (activeReport === "produto" && selGrupo.value) queryParams.append("grupos", selGrupo.value);
    }

    // Seleciona endpoint conforme relatório ativo
    let endpoint = "vendas_cliente";
    if (activeReport === "produto") endpoint = "vendas_produtos";
    else if (activeReport === "gerencial") endpoint = "gerencial";
    else if (activeReport === "gerencial2") endpoint = "gerencial2";

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
        listagemVendas.forEach((item, index) => {
            totalPeso += parseFloat(item.peso_liquido || 0);
            totalSemFrete += parseFloat(item.valor_sem_frete || 0);
            totalComFrete += parseFloat(item.valor_com_frete || 0);

            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td><strong>${item.numero_pedido || "-"}</strong></td>
                    <td class="col-pedido-supra"><strong>${item.pedido_supra || "-"}</strong></td>
                    <td>${item.danfe || "-"}</td>
                    <td>${fmtData(item.data_faturamento)}</td>
                    <td>${item.codigo_cliente || "-"}</td>
                    <td>${limparNomeCliente(item.cliente)}</td>
                    <td>${item.nome_fantasia || "-"}</td>
                    <td>${item.municipio || "-"}</td>
                    <td class="tar">${fmtPeso(item.peso_liquido)}</td>
                    <td class="tar col-money">${fmtMoney(item.valor_sem_frete)}</td>
                    <td class="tar col-money">${fmtMoney(item.valor_com_frete)}</td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
    } else if (activeReport === "produto") {
        // Relatório de Vendas por Produto
        listagemVendas.forEach((item, index) => {
            totalPeso += parseFloat(item.peso_liquido_acumulado || 0);
            totalSemFrete += parseFloat(item.valor_sem_frete || 0);
            totalComFrete += parseFloat(item.valor_com_frete || 0);

            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td><strong>${item.codigo_produto || "-"}</strong></td>
                    <td>${item.produto || "-"}</td>
                    <td>${item.embalagem || "-"}</td>
                    <td class="tar">${fmtPeso(item.peso_liquido_unitario).replace(' kg', '')}</td>
                    <td class="tar">${parseFloat(item.quantidade || 0).toLocaleString("pt-BR")}</td>
                    <td class="tar">${fmtPeso(item.peso_liquido_acumulado)}</td>
                    <td class="tar col-money">${fmtMoney(item.valor_sem_frete)}</td>
                    <td class="tar col-money">${fmtMoney(item.valor_com_frete)}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    } else if (activeReport === "gerencial") {
        listagemVendas.forEach((item, index) => {
            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td style="white-space: nowrap;">${fmtDoc(item.documento) || "-"}</td>
                    <td>${limparNomeCliente(item.nome_cliente)}</td>
                    <td>${item.municipio || "-"}</td>
                    <td>${item.vendedor || "-"}</td>
                    <td>${fmtData(item.data_ultima_compra)}</td>
                    <td>${item.observacao || "-"}</td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
    } else if (activeReport === "gerencial2") {
        listagemVendas.forEach((item, index) => {
            html += `<tr>
                <td style="border-right: 1px solid var(--os-border);">${index + 1}</td>
                <td style="border-right: 1px solid var(--os-border);">${item.codigo_cliente || "-"}</td>
                <td style="border-right: 1px solid var(--os-border);">${limparNomeCliente(item.cliente)}</td>`;
            
            gerencial2Meses.forEach(m => {
                const borderLeft = "border-left: 2px solid #cbd5e1;";
                const p = item.meses?.[m]?.peso || 0;
                const v = item.meses?.[m]?.valor || 0;
                html += `<td class="tar" style="${borderLeft}">${fmtPeso(p).replace(' kg','')}</td><td class="tar col-money">${fmtMoney(v)}</td>`;
            });
            html += `</tr>`;
        });
        tbody.innerHTML = html;
    }

    // Atualiza totais na parte superior da tabela (thead)
    const elPeso = document.getElementById("total-peso");
    const elSem = document.getElementById("total-valor-sem");
    const elCom = document.getElementById("total-valor-com");
    if (elPeso) elPeso.textContent = fmtPeso(totalPeso);
    if (elSem) elSem.textContent = fmtMoney(totalSemFrete);
    if (elCom) elCom.textContent = fmtMoney(totalComFrete);
    tfoot.innerHTML = "";
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
    inFaturamentoInicio.value = "";
    inFaturamentoFim.value = "";
    selFilial.value = "";
    selCategoria.value = "";
    selStatus.value = "";
    selMunicipio.value = "";
    selGrupo.value = "";
    
    inGerencialCodigo.value = "";
    inGerencialDoc.value = "";
    inGerencialNome.value = "";
    selGerencialMun.value = "";
    selGerencialVend.value = "";
    inGerencialDataInicio.value = "";
    inGerencialDataFim.value = "";
    inGerencialObs.value = "";

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

    let aoa = [];
    let filename = "";
    
    let totalPeso = 0;
    let totalSemFrete = 0;
    let totalComFrete = 0;

    if (activeReport === "cliente") {
        aoa.push(["#", "Nº Pedido Sistema", "Pedido Supra", "Danfe", "Data Faturamento", "Código Cliente", "Cliente", "Nome Fantasia", "Município", "Peso Líquido (kg)", "Valor Sem Frete", "Valor Com Frete"]);
        filename = "relatorio_vendas_por_cliente";

        listagemVendas.forEach((item, index) => {
            const p = parseFloat(item.peso_liquido || 0);
            const vs = parseFloat(item.valor_sem_frete || 0);
            const vc = parseFloat(item.valor_com_frete || 0);

            totalPeso += p;
            totalSemFrete += vs;
            totalComFrete += vc;

            aoa.push([index + 1, item.numero_pedido || "-", item.pedido_supra || "-", item.danfe || "-", fmtData(item.data_faturamento), item.codigo_cliente || "-", limparNomeCliente(item.cliente), item.nome_fantasia || "-", item.municipio || "-", Math.round(p), vs, vc]);
        });

        aoa.push(["TOTAL ACUMULADO", "", "", "", "", "", "", "", "", Math.round(totalPeso), totalSemFrete, totalComFrete]);

    } else if (activeReport === "produto") {
        aoa.push(["#", "Código Produto", "Produto", "Embalagem", "Peso Líq. Unit. (kg)", "Quantidade", "Peso Líq. Acumulado (kg)", "Valor Sem Frete", "Valor Com Frete"]);
        filename = "relatorio_vendas_por_produto";

        listagemVendas.forEach((item, index) => {
            const pu = parseFloat(item.peso_liquido_unitario || 0);
            const q = parseFloat(item.quantidade || 0);
            const pa = parseFloat(item.peso_liquido_acumulado || 0);
            const vs = parseFloat(item.valor_sem_frete || 0);
            const vc = parseFloat(item.valor_com_frete || 0);

            totalPeso += pa;
            totalSemFrete += vs;
            totalComFrete += vc;

            aoa.push([index + 1, item.codigo_produto || "-", item.produto || "-", item.embalagem || "-", Math.round(pu), q, Math.round(pa), vs, vc]);
        });

        aoa.push(["TOTAL ACUMULADO", "", "", "", "", "", Math.round(totalPeso), totalSemFrete, totalComFrete]);

    } else if (activeReport === "gerencial") {
        aoa.push(["#", "CNPJ/CPF", "Nome Cliente", "Município", "Vendedor", "Data Última Compra", "Observação"]);
        filename = "relatorio_gerencial";

        listagemVendas.forEach((item, index) => {
            aoa.push([index + 1, fmtDoc(item.documento) || "-", limparNomeCliente(item.nome_cliente), item.municipio || "-", item.vendedor || "-", fmtData(item.data_ultima_compra), item.observacao || "-"]);
        });
    } else if (activeReport === "gerencial2") {
        let row1 = ["Cód. Cliente", "Cliente"];
        let row2 = ["", ""];
        
        gerencial2Meses.forEach(m => {
            const [ano, mes] = m.split('-');
            row1.push(`${mes}/${ano}`, "");
            row2.push("Peso (kg)", "Valor (R$)");
        });
        
        aoa.push(row1, row2);
        filename = "relatorio_gerencial2_evolucao";
        
        listagemVendas.forEach((item, index) => {
            let row = [item.codigo_cliente || "-", limparNomeCliente(item.cliente)];
            gerencial2Meses.forEach(m => {
                row.push(item.meses?.[m]?.peso || 0);
                row.push(item.meses?.[m]?.valor || 0);
            });
            aoa.push(row);
        });
    }

    const ws = XLSX.utils.aoa_to_sheet(aoa);

    // Apply merges for gerencial2
    if (activeReport === "gerencial2") {
        ws['!merges'] = [
            { s: {r:0, c:0}, e: {r:1, c:0} },
            { s: {r:0, c:1}, e: {r:1, c:1} }
        ];
        
        let cIndex = 2;
        gerencial2Meses.forEach(m => {
            ws['!merges'].push({ s: {r:0, c:cIndex}, e: {r:0, c:cIndex+1} });
            cIndex += 2;
        });
        
        // Formatação (SheetJS open-source ignora cores, mas aceita number format `z` e as vezes alignment `s`)
        for (let cell in ws) {
            if (cell[0] === '!') continue;
            
            const row = parseInt(cell.replace(/\D/g, ''));
            if (!ws[cell].s) ws[cell].s = {};
            
            if (row === 1 || row === 2) {
                // Tenta centralizar e negrito nos cabeçalhos
                ws[cell].s = { alignment: { horizontal: "center", vertical: "center" }, font: { bold: true } };
            } else if (typeof ws[cell].v === 'number') {
                // Formato de número com 2 casas decimais e separador de milhar para pesos e valores
                ws[cell].z = '#,##0.00';
            }
        }
        
        // Configura largura das colunas
        ws['!cols'] = [{ wch: 15 }, { wch: 45 }]; // Cód Cliente e Cliente
        for (let i = 0; i < gerencial2Meses.length * 2; i++) {
            ws['!cols'].push({ wch: 15 }); // Peso e Valor
        }
    }

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Relatorio");
    XLSX.writeFile(wb, `${filename}_${new Date().toISOString().slice(0, 10)}.xlsx`);
}

let gerencial2Meses = [];
function generateLastXMonths(x) {
    let months = [];
    const date = new Date();
    date.setDate(1);
    for (let i = x - 1; i >= 0; i--) {
        const d = new Date(date.getFullYear(), date.getMonth() - i, 1);
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        months.push(`${y}-${m}`);
    }
    return months;
}
