// dashboard.js

document.addEventListener("DOMContentLoaded", () => {
    carregarKPIs();
});

async function carregarKPIs() {
    try {
        // Usa o config da API global se existir, senão tenta do window.location
        const apiBase = (window.API_BASE || "") + "/api/dashboard";
        const token = localStorage.getItem("ordersync_token");

        if (!token) return; // Auth.js fará o redirecionamento

        const response = await fetch(`${apiBase}/kpis`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error("Erro ao carregar KPIs");
        }

        const data = await response.json();

        // Elementos DOM
        const elFaturamento = document.getElementById("kpi-faturamento");
        const elPedidosPendentes = document.getElementById("kpi-pedidos-pendentes");
        const elContasPagar = document.getElementById("kpi-contas-pagar");
        const elContasReceber = document.getElementById("kpi-contas-receber");
        const elTicketMedio = document.getElementById("kpi-ticket-medio");

        // Formatador BRL
        const formatter = new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        });

        if (elFaturamento) elFaturamento.innerText = formatter.format(data.faturamento_mes || 0);
        if (elPedidosPendentes) elPedidosPendentes.innerText = data.pedidos_pendentes || 0;
        if (elContasPagar) elContasPagar.innerText = formatter.format(data.contas_pagar || 0);
        if (elContasReceber) elContasReceber.innerText = formatter.format(data.contas_receber || 0);
        if (elTicketMedio) elTicketMedio.innerText = formatter.format(data.ticket_medio || 0);

    } catch (error) {
        console.error("Erro ao buscar KPIs do Dashboard:", error);
    }
}
