/**
 * dashboards.js
 * Controls the Dashboards UI (Geral, Vendas, Logística, Pivot Table)
 */

var API_BASE = window.API_BASE || window.location.origin;

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    loadDashboardGeral(); // default
});

function initTabs() {
    const btns = document.querySelectorAll(".dashboard-menu button");
    btns.forEach(btn => {
        btn.addEventListener("click", (e) => {
            btns.forEach(b => b.classList.remove("active"));
            e.currentTarget.classList.add("active");
            
            const tab = e.currentTarget.dataset.tab;
            showPanel(tab);
        });
    });
}

function showPanel(tab) {
    document.getElementById("panel-geral").style.display = "none";
    document.getElementById("panel-vendas").style.display = "none";
    document.getElementById("panel-logistica").style.display = "none";
    document.getElementById("panel-dinamica").style.display = "none";
    
    document.getElementById("dash-title").innerText = "Carregando...";
    document.getElementById("dash-desc").innerText = "Buscando dados em tempo real.";

    if (tab === "geral") {
        document.getElementById("panel-geral").style.display = "block";
        document.getElementById("dash-title").innerText = "Visão Geral";
        document.getElementById("dash-desc").innerText = "Resumo executivo de pedidos e faturamento.";
        loadDashboardGeral();
    } else if (tab === "vendas") {
        document.getElementById("panel-vendas").style.display = "block";
        document.getElementById("dash-title").innerText = "Performance de Vendas";
        document.getElementById("dash-desc").innerText = "Análise detalhada de vendas, tickets e mapa.";
        loadDashboardVendas();
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

// ----------------------------------------------------------------------------------
// 1. Visão Geral
// ----------------------------------------------------------------------------------
let chartGeralInst = null;
async function loadDashboardGeral() {
    try {
        const resp = await fetch(`${API_BASE}/api/dashboard/geral`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        if (!resp.ok) throw new Error("Erro Geral");
        const data = await resp.json();

        document.getElementById("kpi-pedidos-mes").innerText = data.kpis.pedidos_mes;
        document.getElementById("kpi-faturamento-mes").innerText = `R$ ${data.kpis.faturamento_mes.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
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
async function loadDashboardVendas() {
    try {
        const resp = await fetch(`${API_BASE}/api/dashboard/vendas`, {
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

    } catch(e) { console.error(e); }
}

// ----------------------------------------------------------------------------------
// 3. Logística
// ----------------------------------------------------------------------------------
let chartLogisticaInst = null;
async function loadDashboardLogistica() {
    try {
        const resp = await fetch(`${API_BASE}/api/dashboard/logistica`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        if (!resp.ok) throw new Error("Erro Log");
        const data = await resp.json();

        document.getElementById("kpi-cargas-mes").innerText = data.kpis.cargas_enviadas_mes;
        document.getElementById("kpi-peso-medio").innerText = `${data.kpis.peso_medio_carga.toLocaleString('pt-BR')} kg`;

        const ctx = document.getElementById("chart-cargas-historico").getContext("2d");
        if(chartLogisticaInst) chartLogisticaInst.destroy();
        chartLogisticaInst = new Chart(ctx, {
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

    } catch(e) { console.error(e); }
}

// ----------------------------------------------------------------------------------
// 4. Análise Dinâmica (Pivot Table)
// ----------------------------------------------------------------------------------
async function loadDashboardPivot() {
    const container = document.getElementById("pivot-table-container");
    container.innerHTML = "Carregando dados, aguarde...";
    try {
        const resp = await fetch(`${API_BASE}/api/dashboard/pivot`, {
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
