var API_BASE = window.API_BASE || window.location.origin;

let currentTab = "geral";
// Estado independente por aba
let tabFilters = {
    geral: { periodo: "mes", status: "Todos" },
    vendas: { periodo: "mes", status: "Todos" },
    produtos: { periodo: "mes", status: "Todos" },
    clientes: { periodo: "mes", status: "Todos" },
    logistica: { periodo: "mes", status: "Todos" },
    dinamica: { periodo: "mes", status: "Todos" }
};

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initFilters();
    loadActivePanel(); // default
});

function initFilters() {
    const selPeriodo = document.getElementById("filter-periodo");
    const selStatus = document.getElementById("filter-status");

    if (selPeriodo) {
        selPeriodo.addEventListener("change", () => {
            tabFilters[currentTab].periodo = selPeriodo.value;
            loadActivePanel();
        });
    }

    if (selStatus) {
        selStatus.addEventListener("change", () => {
            tabFilters[currentTab].status = selStatus.value;
            loadActivePanel();
        });
    }
}

function initTabs() {
    const btns = document.querySelectorAll(".dashboard-menu button");
    btns.forEach(btn => {
        btn.addEventListener("click", (e) => {
            btns.forEach(b => b.classList.remove("active"));
            e.currentTarget.classList.add("active");
            
            currentTab = e.currentTarget.dataset.tab;
            showPanel(currentTab);
        });
    });
}

function showPanel(tab) {
    document.getElementById("panel-geral").style.display = "none";
    document.getElementById("panel-vendas").style.display = "none";
    document.getElementById("panel-produtos").style.display = "none";
    document.getElementById("panel-clientes").style.display = "none";
    document.getElementById("panel-logistica").style.display = "none";
    document.getElementById("panel-dinamica").style.display = "none";
    
    document.getElementById("dash-title").innerText = "Carregando...";
    document.getElementById("dash-desc").innerText = "Buscando dados em tempo real.";

    // Sincroniza a barra de filtros com os valores salvos para esta aba
    document.getElementById("filter-periodo").value = tabFilters[tab].periodo;
    document.getElementById("filter-status").value = tabFilters[tab].status;

    if (tab === "geral") {
        document.getElementById("panel-geral").style.display = "block";
        document.getElementById("dash-title").innerText = "Visão Geral";
        document.getElementById("dash-desc").innerText = "Resumo executivo de pedidos e faturamento conforme filtros aplicados.";
        loadDashboardGeral();
    } else if (tab === "vendas") {
        document.getElementById("panel-vendas").style.display = "block";
        document.getElementById("dash-title").innerText = "Performance de Vendas";
        document.getElementById("dash-desc").innerText = "Análise detalhada de vendas, tickets e mapa.";
        loadDashboardVendas();
    } else if (tab === "produtos") {
        document.getElementById("panel-produtos").style.display = "block";
        document.getElementById("dash-title").innerText = "Produtos & Categorias";
        document.getElementById("dash-desc").innerText = "Performance dos itens mais vendidos e distribuição por famílias.";
        loadDashboardProdutos();
    } else if (tab === "clientes") {
        document.getElementById("panel-clientes").style.display = "block";
        document.getElementById("dash-title").innerText = "Inteligência de Clientes";
        document.getElementById("dash-desc").innerText = "Ranking dos melhores clientes e análise de conversão do funil de vendas.";
        loadDashboardClientes();
    } else if (tab === "logistica") {
        document.getElementById("panel-logistica").style.display = "block";
        document.getElementById("dash-title").innerText = "Logística & Cargas";
        document.getElementById("dash-desc").innerText = "Acompanhamento de entregas, pesos e rotas.";
        loadDashboardLogistica();
    } else if (tab === "dinamica") {
        document.getElementById("panel-dinamica").style.display = "block";
        document.getElementById("dash-title").innerText = "Análise Dinâmica";
        document.getElementById("dash-desc").innerText = "Monte a tabela que quiser arrastando as colunas e linhas (Pivot Table).";
        loadDashboardPivot();
    }
}

function loadActivePanel() {
    showPanel(currentTab);
}

function getQueryString() {
    const f = tabFilters[currentTab];
    return `periodo=${f.periodo}&status=${f.status}`;
}

// ----------------------------------------------------------------------------------
// 1. Visão Geral
// ----------------------------------------------------------------------------------
let chartGeralInst = null;
async function loadDashboardGeral() {
    try {
        const resp = await fetch(`${API_BASE}/api/dashboard/geral?${getQueryString()}`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        if (!resp.ok) throw new Error("Erro Geral");
        const data = await resp.json();

        document.getElementById("kpi-pedidos-mes").innerText = data.kpis.pedidos_mes;
        document.getElementById("kpi-faturamento-mes").innerText = `R$ ${data.kpis.faturamento_mes.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
        document.getElementById("kpi-ticket-medio-geral").innerText = `R$ ${data.kpis.ticket_medio.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
        document.getElementById("kpi-cargas-abertas").innerText = data.kpis.cargas_abertas;

        // Gráfico de Faturamento/Pedidos nos últimos 6 meses
        const ctx = document.getElementById("chart-historico-pedidos").getContext("2d");
        if(chartGeralInst) chartGeralInst.destroy();
        
        chartGeralInst = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.chart.labels,
                datasets: [
                    {
                        label: 'Faturamento (R$)',
                        data: data.chart.faturamento,
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Quantidade Pedidos',
                        data: data.chart.qtd_pedidos,
                        borderColor: '#10b981',
                        backgroundColor: 'transparent',
                        borderDash: [5, 5],
                        type: 'line',
                        tension: 0.1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { type: 'linear', display: true, position: 'left' },
                    y1: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false } }
                }
            }
        });
    } catch(e) { console.error(e); }
}

// ----------------------------------------------------------------------------------
// 2. Vendas
// ----------------------------------------------------------------------------------
let chartVendasRegInst = null;
let chartVendasStatusInst = null;
let chartEvolucaoTicketInst = null;
async function loadDashboardVendas() {
    try {
        const resp = await fetch(`${API_BASE}/api/dashboard/vendas?${getQueryString()}`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        if (!resp.ok) throw new Error("Erro Vendas");
        const data = await resp.json();

        document.getElementById("kpi-ticket-medio").innerText = `R$ ${data.kpis.ticket_medio.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
        document.getElementById("kpi-vendedores").innerText = data.kpis.vendedores_ativos;

        const ctx1 = document.getElementById("chart-vendas-por-regiao").getContext("2d");
        if(chartVendasRegInst) chartVendasRegInst.destroy();
        chartVendasRegInst = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: data.chart_regioes.labels,
                datasets: [{
                    label: 'Vendas por Município (R$)',
                    data: data.chart_regioes.data,
                    backgroundColor: '#3b82f6'
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });

        const ctx2 = document.getElementById("chart-vendas-por-status").getContext("2d");
        if(chartVendasStatusInst) chartVendasStatusInst.destroy();
        chartVendasStatusInst = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: data.chart_status.labels,
                datasets: [{
                    data: data.chart_status.data,
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#6b7280', '#3b82f6']
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });

        const ctx3 = document.getElementById("chart-evolucao-ticket").getContext("2d");
        if(chartEvolucaoTicketInst) chartEvolucaoTicketInst.destroy();
        chartEvolucaoTicketInst = new Chart(ctx3, {
            type: 'line',
            data: {
                labels: data.chart_evolucao_ticket.labels,
                datasets: [{
                    label: 'Ticket Médio (R$)',
                    data: data.chart_evolucao_ticket.data,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Evolução do Ticket Médio Mês a Mês'} } }
        });

    } catch(e) { console.error(e); }
}

// ----------------------------------------------------------------------------------
// 2A. Produtos
// ----------------------------------------------------------------------------------
let chartTopProdutosInst = null;
let chartFamiliasInst = null;
async function loadDashboardProdutos() {
    try {
        const resp = await fetch(`${API_BASE}/api/dashboard/produtos?${getQueryString()}`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        if (!resp.ok) throw new Error("Erro Produtos");
        const data = await resp.json();

        const ctx1 = document.getElementById("chart-top-produtos").getContext("2d");
        if(chartTopProdutosInst) chartTopProdutosInst.destroy();
        chartTopProdutosInst = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: data.top_produtos.labels,
                datasets: [{
                    label: 'Faturamento (R$)',
                    data: data.top_produtos.faturamento,
                    backgroundColor: '#10b981'
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y' }
        });

        const ctx2 = document.getElementById("chart-familias").getContext("2d");
        if(chartFamiliasInst) chartFamiliasInst.destroy();
        chartFamiliasInst = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: data.familias.labels,
                datasets: [{
                    data: data.familias.faturamento,
                    backgroundColor: ['#3b82f6', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316', '#eab308']
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });

    } catch(e) { console.error(e); }
}

// ----------------------------------------------------------------------------------
// 2B. Clientes
// ----------------------------------------------------------------------------------
let chartTopClientesInst = null;
let chartEvolucaoClientesInst = null;
async function loadDashboardClientes() {
    try {
        const resp = await fetch(`${API_BASE}/api/dashboard/clientes?${getQueryString()}`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        if (!resp.ok) throw new Error("Erro Clientes");
        const data = await resp.json();

        document.getElementById("kpi-orcamentos-funil").innerText = data.funil.orcamentos;
        document.getElementById("kpi-convertidos-funil").innerText = data.funil.convertidos;
        document.getElementById("kpi-ticket-top10").innerText = `R$ ${data.kpis.ticket_record.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;

        const ctx = document.getElementById("chart-top-clientes").getContext("2d");
        if(chartTopClientesInst) chartTopClientesInst.destroy();
        chartTopClientesInst = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.top_clientes.labels,
                datasets: [{
                    label: 'Faturamento Total (R$)',
                    data: data.top_clientes.faturamento,
                    backgroundColor: '#8b5cf6'
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });

        const ctx2 = document.getElementById("chart-evolucao-clientes").getContext("2d");
        if(chartEvolucaoClientesInst) chartEvolucaoClientesInst.destroy();
        chartEvolucaoClientesInst = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: data.chart_evolucao_clientes.labels,
                datasets: [
                    {
                        label: 'Novos Orçamentos',
                        data: data.chart_evolucao_clientes.orcamentos,
                        backgroundColor: '#9ca3af'
                    },
                    {
                        label: 'Pedidos Confirmados',
                        data: data.chart_evolucao_clientes.confirmados,
                        backgroundColor: '#8b5cf6'
                    }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Evolução do Funil Mês a Mês'} } }
        });

    } catch(e) { console.error(e); }
}

// ----------------------------------------------------------------------------------
// 3. Logística
// ----------------------------------------------------------------------------------
let chartLogisticaInst = null;
let chartModalidadeInst = null;
let chartFrotaInst = null;
async function loadDashboardLogistica() {
    try {
        const resp = await fetch(`${API_BASE}/api/dashboard/logistica?${getQueryString()}`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        if (!resp.ok) throw new Error("Erro Log");
        const data = await resp.json();

        document.getElementById("kpi-cargas-mes").innerText = data.kpis.cargas_enviadas_mes;
        document.getElementById("kpi-peso-medio").innerText = `${data.kpis.peso_medio_carga.toLocaleString('pt-BR')} kg`;
        document.getElementById("kpi-custo-frete").innerText = `R$ ${data.kpis.custo_frete_mes.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;

        const ctx1 = document.getElementById("chart-cargas-historico").getContext("2d");
        if(chartLogisticaInst) chartLogisticaInst.destroy();
        chartLogisticaInst = new Chart(ctx1, {
            type: 'line',
            data: {
                labels: data.chart_historico.labels,
                datasets: [{
                    label: 'Peso Total Transportado (Kg)',
                    data: data.chart_historico.data,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });

        const ctx2 = document.getElementById("chart-modalidade").getContext("2d");
        if(chartModalidadeInst) chartModalidadeInst.destroy();
        chartModalidadeInst = new Chart(ctx2, {
            type: 'pie',
            data: {
                labels: data.chart_modalidade.labels,
                datasets: [{
                    data: data.chart_modalidade.data,
                    backgroundColor: ['#10b981', '#6b7280']
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Modalidade (Entrega vs Retirada)'} } }
        });

        const ctx3 = document.getElementById("chart-eficiencia-frota").getContext("2d");
        if(chartFrotaInst) chartFrotaInst.destroy();
        chartFrotaInst = new Chart(ctx3, {
            type: 'doughnut',
            data: {
                labels: data.chart_frota.labels,
                datasets: [{
                    data: data.chart_frota.data,
                    backgroundColor: ['#2563eb', '#f43f5e', '#eab308']
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Eficiência de Frota (Próprio vs Terceiro)'} } }
        });

    } catch(e) { console.error(e); }
}

// ----------------------------------------------------------------------------------
// 4. Análise Dinâmica (Pivot Table)
// ----------------------------------------------------------------------------------
async function loadDashboardPivot() {
    const container = document.getElementById("pivot-table-container");
    container.innerHTML = "Carregando dados, aguarde...";
    try {
        const resp = await fetch(`${API_BASE}/api/dashboard/pivot?${getQueryString()}`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        if (!resp.ok) throw new Error("Erro Pivot");
        const rawData = await resp.json();

        if(!rawData || rawData.length === 0) {
            container.innerHTML = "Não há dados suficientes para montar a análise.";
            return;
        }

        // Initialize Pivot Table
        // The PivotTable.js uses jQuery natively
        $(function() {
            var derivers = $.pivotUtilities.derivers;
            var renderers = $.extend($.pivotUtilities.renderers, $.pivotUtilities.plotly_renderers);

            $("#pivot-table-container").pivotUI(rawData, {
                renderers: renderers,
                cols: ["Status"], 
                rows: ["Municipio", "Cliente"],
                vals: ["Valor_Total"],
                aggregatorName: "Sum",
                rendererName: "Table",
            }, true, "pt"); // localized in Portuguese
        });

    } catch(e) {
        console.error(e);
        container.innerHTML = "Ocorreu um erro ao carregar os dados brutos.";
    }
}
