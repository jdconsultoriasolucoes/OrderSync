// dashboard.js

let currentFilter = 'mes'; // 'mes' ou 'ano'

document.addEventListener("DOMContentLoaded", () => {
    const toggleCheckbox = document.getElementById("kpi-toggle-checkbox");

    if (toggleCheckbox) {
        toggleCheckbox.addEventListener("change", (e) => {
            currentFilter = e.target.checked ? 'ano' : 'mes';

            // Opcional: Atualizar classes text-active se quiser forçar via JS, 
            // mas o CSS já cuida da cor com o seletor :checked ~ .option-mes
            const optionMes = document.querySelector(".option-mes");
            const optionAno = document.querySelector(".option-ano");
            const lblFaturamento = document.querySelector("#kpi-faturamento").previousElementSibling;

            if (optionMes && optionAno) {
                if (currentFilter === 'ano') {
                    optionMes.classList.remove("active");
                    optionAno.classList.add("active");
                    if (lblFaturamento) lblFaturamento.textContent = "Faturamento do ano";
                } else {
                    optionAno.classList.remove("active");
                    optionMes.classList.add("active");
                    if (lblFaturamento) lblFaturamento.textContent = "Faturamento do mês";
                }
            }

            carregarKPIs();
        });
    }

    carregarKPIs();
});

async function carregarKPIs() {
    try {
        // Usa o config da API global se existir, senão tenta do window.location
        const apiBase = (window.API_BASE || "") + "/api/dashboard";
        const token = localStorage.getItem("ordersync_token");

        if (!token) return; // Auth.js fará o redirecionamento

        // Ler o filtro selecionado (Mês Atual ou Ano Atual)
        let queryParams = "";
        const hoje = new Date();
        const ano = hoje.getFullYear();

        if (currentFilter === 'mes') {
            const mes = hoje.getMonth() + 1;
            queryParams = `?month=${mes}&year=${ano}`;
        } else if (currentFilter === 'ano') {
            // Se for 'Ano Atual', passamos apenas o ano para o backend
            queryParams = `?year=${ano}`;
        }

        const response = await fetch(`${apiBase}/kpis${queryParams}`, {
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
        const elTicketMedio = document.getElementById("kpi-ticket-medio");
        const elClientesSemCodigo = document.getElementById("kpi-clientes-sem-codigo");

        // Formatador BRL
        const formatter = new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        });

        if (elFaturamento) elFaturamento.innerText = formatter.format(data.faturamento_mes || 0);
        if (elPedidosPendentes) elPedidosPendentes.innerText = data.pedidos_pendentes || 0;
        if (elTicketMedio) elTicketMedio.innerText = formatter.format(data.ticket_medio || 0);
        if (elClientesSemCodigo) elClientesSemCodigo.innerText = data.clientes_sem_codigo || 0;

    } catch (error) {
        console.error("Erro ao buscar KPIs do Dashboard:", error);
    }
}

