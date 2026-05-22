document.addEventListener("DOMContentLoaded", () => {
    const uploadArea = document.getElementById("uploadArea");
    const fileInput = document.getElementById("fileInput");
    const loadingOverlay = document.getElementById("loadingOverlay");
    const resultsSection = document.getElementById("resultsSection");
    
    // Elements for KPI
    const kpiLidos = document.getElementById("kpiLidos");
    const kpiSucesso = document.getElementById("kpiSucesso");
    const kpiSemAlteracao = document.getElementById("kpiSemAlteracao");
    const kpiAjustados = document.getElementById("kpiAjustados");
    const kpiErros = document.getElementById("kpiErros");
    const kpiValorAjuste = document.getElementById("kpiValorAjuste");
    
    // Duplicate Alert Banner
    const duplicateAlert = document.getElementById("duplicateAlert");
    const duplicateAlertText = document.getElementById("duplicateAlertText");
    
    // Table Body
    const resultsBody = document.getElementById("resultsBody");

    // Formatter helpers
    function fmtMoney(value) {
        if (value === null || value === undefined) return "0,00";
        return parseFloat(value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    // Obter data atual no formato DD/MM/YYYY
    function obterDataAtualFmt() {
        const hoje = new Date();
        const dia = String(hoje.getDate()).padStart(2, '0');
        const mes = String(hoje.getMonth() + 1).padStart(2, '0');
        const ano = hoje.getFullYear();
        return `${dia}/${mes}/${ano}`;
    }

    // Drag and Drop events
    uploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadArea.classList.add("dragover");
    });

    uploadArea.addEventListener("dragleave", () => {
        uploadArea.classList.remove("dragover");
    });

    uploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadArea.classList.remove("dragover");
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
            handleFile(e.target.files[0]);
        }
    });

    async function handleFile(file) {
        if (!file.name.endsWith('.xlsm') && !file.name.endsWith('.xlsx')) {
            alert("Apenas arquivos Excel (.xlsm, .xlsx) são suportados!");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        loadingOverlay.style.display = "flex";
        resultsSection.style.display = "none";
        resultsBody.innerHTML = ""; // Clear old results

        try {
            const token = localStorage.getItem("token") || "";
            const API_BASE = window.API_BASE || window.location.origin;
            const response = await fetch(`${API_BASE}/api/importacao/pedidos`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`
                },
                body: formData
            });

            const textData = await response.text();
            let data;
            try {
                data = JSON.parse(textData);
            } catch (err) {
                throw new Error(`Falha ao ler resposta do servidor. Código HTTP: ${response.status}. Resposta crua: ${textData}`);
            }

            if (!response.ok) {
                throw new Error(data.detail || "Erro ao processar planilha.");
            }

            // Salvar no cache do localStorage para persistir na tela
            localStorage.setItem("lastImportData", JSON.stringify(data));

            renderResults(data);

        } catch (error) {
            console.error(error);
            alert("Erro durante a importação: " + error.message);
        } finally {
            loadingOverlay.style.display = "none";
            // Reset input so the same file can be uploaded again if needed
            fileInput.value = "";
        }
    }

    function renderResults(data) {
        const { resumo, itens } = data;
        
        // Limpar os campos de filtros ao renderizar uma nova carga (e definir data atual como default no de faturamento)
        ["filterPedido", "filterCliente", "filterDataPedido", "filterDataFat", "filterValor", "filterResultado", "filterStatus", "filterDetalhes"].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                if (id === "filterDataFat") {
                    el.value = obterDataAtualFmt();
                } else {
                    el.value = "";
                }
            }
        });
        
        // Exibir/Ocultar Banner de Aviso de Duplicidade Geral
        if (duplicateAlert && duplicateAlertText) {
            if (resumo.aviso) {
                duplicateAlertText.innerText = resumo.aviso;
                duplicateAlert.style.display = "flex";
            } else {
                duplicateAlert.style.display = "none";
            }
        }
        
        // Update KPIs
        kpiLidos.innerText = resumo.lidos || 0;
        kpiSucesso.innerText = resumo.sucesso || 0;
        if (kpiSemAlteracao) {
            kpiSemAlteracao.innerText = resumo.sem_alteracao || 0;
        }
        kpiAjustados.innerText = resumo.ajustados || 0;
        kpiErros.innerText = resumo.erros || 0;
        kpiValorAjuste.innerText = fmtMoney(resumo.valor_total_ajustes || 0);

        // Exibir botão premium de limpar resultados
        const btnClear = document.getElementById("btnClearCache");
        if (btnClear) {
            btnClear.style.display = "inline-block";
        }

        // Ordenação inteligente de status (Erros e Ajustados primeiro)
        function getStatusPriority(status) {
            if (status === "ERRO_NAO_ENCONTRADO") return 1;
            if (status === "AJUSTADO") return 2;
            if (status === "SUCESSO") return 3;
            if (status === "SEM_ALTERACAO") return 4;
            return 5;
        }

        if (itens && itens.length > 0) {
            itens.sort((a, b) => getStatusPriority(a.status) - getStatusPriority(b.status));
        }

        // Render Table Rows
        if (!itens || itens.length === 0) {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td colspan="8" style="text-align: center; color: var(--os-text-secondary);">Nenhum pedido processado.</td>`;
            resultsBody.appendChild(tr);
        } else {
            itens.forEach(item => {
                const tr = document.createElement("tr");

                // Define Badge classes
                let badgeClass = "badge-status success";
                let resultText = "Sucesso";
                if (item.status === "AJUSTADO") {
                    badgeClass = "badge-status warning";
                    resultText = "Divergência / Ajustado";
                } else if (item.status === "ERRO_NAO_ENCONTRADO") {
                    badgeClass = "badge-status error";
                    resultText = "Não Encontrado";
                } else if (item.status === "SEM_ALTERACAO") {
                    badgeClass = "badge-status neutral";
                    resultText = "Sem Alterações";
                }

                // Build details list HTML
                let detalhesHtml = `<ul class="detail-list">`;
                if (Array.isArray(item.detalhes)) {
                    if (item.detalhes.length === 0) {
                        detalhesHtml += `<li style="color: var(--os-success);">Validado perfeitamente sem divergências.</li>`;
                    } else {
                        item.detalhes.forEach(d => {
                            if (item.status === "SEM_ALTERACAO") {
                                detalhesHtml += `<li style="color: var(--os-text-secondary);">${d}</li>`;
                            } else {
                                detalhesHtml += `<li>${d}</li>`;
                            }
                        });
                    }
                } else {
                    detalhesHtml += `<li>${item.detalhes || "-"}</li>`;
                }
                detalhesHtml += `</ul>`;

                const badgeNovoStatus = item.novo_status_pedido === "PEDIDO_NAO_COMPLETO" 
                    ? `<span style="color: var(--os-error); font-weight: 600;">Pedido Não Completo</span>`
                    : (item.novo_status_pedido === "FATURADO_SUPRA" 
                        ? `<span style="color: var(--os-primary); font-weight: 600;">Faturado Supra</span>` 
                        : `<span style="color: var(--os-text-secondary);">-</span>`);

                // Textos normalizados para facilitar busca rápida
                const textoStatus = item.novo_status_pedido === "PEDIDO_NAO_COMPLETO" 
                    ? "Pedido Não Completo" 
                    : (item.novo_status_pedido === "FATURADO_SUPRA" ? "Faturado Supra" : "-");
                const textoDetalhes = Array.isArray(item.detalhes) ? item.detalhes.join(" ") : (item.detalhes || "");

                // Atributos de dados para filtragem ultra-rápida no client-side
                tr.dataset.pedido = item.pedido_supra || "";
                tr.dataset.cliente = item.cliente_codigo || "";
                tr.dataset.data_pedido = item.data_pedido || "";
                tr.dataset.data_fat = item.data_faturamento || "";
                tr.dataset.valor = fmtMoney(item.valor_planilha);
                tr.dataset.resultado = resultText;
                tr.dataset.status = textoStatus;
                tr.dataset.detalhes = textoDetalhes;

                tr.innerHTML = `
                    <td><strong>${item.pedido_supra || "-"}</strong></td>
                    <td>${item.cliente_codigo || "-"}</td>
                    <td>${item.data_pedido || "-"}</td>
                    <td>${item.data_faturamento || "-"}</td>
                    <td>R$ ${fmtMoney(item.valor_planilha)}</td>
                    <td><span class="${badgeClass}">${resultText}</span></td>
                    <td>${badgeNovoStatus}</td>
                    <td>${detalhesHtml}</td>
                `;

                resultsBody.appendChild(tr);
            });
        }

        // Show Results section with animation
        resultsSection.style.display = "flex";
        resultsSection.style.animation = "fadeIn 0.5s ease-out forwards";

        // Aplicar filtros iniciais (como a data de faturamento padrão)
        applyFilters();
    }

    // Lógica client-side para filtragem dinâmica instantânea
    function applyFilters() {
        const fPedido = document.getElementById("filterPedido").value.toLowerCase().trim();
        const fCliente = document.getElementById("filterCliente").value.toLowerCase().trim();
        const fDataPedido = document.getElementById("filterDataPedido").value.toLowerCase().trim();
        const fDataFat = document.getElementById("filterDataFat").value.toLowerCase().trim();
        const fValor = document.getElementById("filterValor").value.toLowerCase().trim();
        const fResultado = document.getElementById("filterResultado").value.toLowerCase().trim();
        const fStatus = document.getElementById("filterStatus").value.toLowerCase().trim();
        const fDetalhes = document.getElementById("filterDetalhes").value.toLowerCase().trim();

        const rows = resultsBody.querySelectorAll("tr");
        rows.forEach(tr => {
            // Se for o tr informativo de tabela vazia, ignora
            if (tr.querySelector("td[colspan]")) return;

            const matchPedido = !fPedido || String(tr.dataset.pedido).toLowerCase().includes(fPedido);
            const matchCliente = !fCliente || String(tr.dataset.cliente).toLowerCase().includes(fCliente);
            const matchDataPedido = !fDataPedido || String(tr.dataset.data_pedido).toLowerCase().includes(fDataPedido);
            const matchDataFat = !fDataFat || String(tr.dataset.data_fat).toLowerCase().includes(fDataFat);
            const matchValor = !fValor || String(tr.dataset.valor).toLowerCase().includes(fValor);
            const matchResultado = !fResultado || String(tr.dataset.resultado).toLowerCase() === fResultado;
            const matchStatus = !fStatus || String(tr.dataset.status).toLowerCase().includes(fStatus);
            const matchDetalhes = !fDetalhes || String(tr.dataset.detalhes).toLowerCase().includes(fDetalhes);

            if (matchPedido && matchCliente && matchDataPedido && matchDataFat && matchValor && matchResultado && matchStatus && matchDetalhes) {
                tr.style.display = "";
            } else {
                tr.style.display = "none";
            }
        });
    }

    // Vincular os inputs de filtros aos event listeners
    ["filterPedido", "filterCliente", "filterDataPedido", "filterDataFat", "filterValor", "filterResultado", "filterStatus", "filterDetalhes"].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("input", applyFilters);
            if (el.tagName === "SELECT") {
                el.addEventListener("change", applyFilters);
            }
        }
    });

    // Definir data de faturamento padrão no carregamento inicial
    const inputFat = document.getElementById("filterDataFat");
    if (inputFat) {
        inputFat.value = obterDataAtualFmt();
    }

    // Carregar dados salvos do localStorage se existirem
    const savedData = localStorage.getItem("lastImportData");
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            renderResults(data);
        } catch (e) {
            console.error("Erro ao carregar dados salvos do localStorage:", e);
            localStorage.removeItem("lastImportData");
        }
    }

    // Ação do botão "Limpar Resultados"
    const btnClearCache = document.getElementById("btnClearCache");
    if (btnClearCache) {
        btnClearCache.addEventListener("click", () => {
            if (confirm("Deseja realmente limpar as informações da última importação da tela?")) {
                localStorage.removeItem("lastImportData");
                resultsBody.innerHTML = "";
                resultsSection.style.display = "none";
                btnClearCache.style.display = "none";
                if (duplicateAlert) duplicateAlert.style.display = "none";
            }
        });
    }
});
