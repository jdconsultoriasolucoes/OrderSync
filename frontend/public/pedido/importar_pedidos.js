document.addEventListener("DOMContentLoaded", () => {
    const uploadArea = document.getElementById("uploadArea");
    const fileInput = document.getElementById("fileInput");
    const loadingOverlay = document.getElementById("loadingOverlay");
    const resultsSection = document.getElementById("resultsSection");
    
    // Elements for KPI
    const kpiLidos = document.getElementById("kpiLidos");
    const kpiSucesso = document.getElementById("kpiSucesso");
    const kpiAjustados = document.getElementById("kpiAjustados");
    const kpiErros = document.getElementById("kpiErros");
    const kpiValorAjuste = document.getElementById("kpiValorAjuste");
    
    // Table Body
    const resultsBody = document.getElementById("resultsBody");

    // Formatter helpers
    function fmtMoney(value) {
        if (value === null || value === undefined) return "0,00";
        return parseFloat(value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
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
            const response = await fetch("/api/importacao/pedidos", {
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
        
        // Update KPIs
        kpiLidos.innerText = resumo.lidos || 0;
        kpiSucesso.innerText = resumo.sucesso || 0;
        kpiAjustados.innerText = resumo.ajustados || 0;
        kpiErros.innerText = resumo.erros || 0;
        kpiValorAjuste.innerText = fmtMoney(resumo.valor_total_ajustes || 0);

        // Render Table Rows
        if (!itens || itens.length === 0) {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td colspan="6" style="text-align: center; color: var(--os-text-secondary);">Nenhum pedido processado.</td>`;
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
                }

                // Build details list HTML
                let detalhesHtml = `<ul class="detail-list">`;
                if (Array.isArray(item.detalhes)) {
                    if (item.detalhes.length === 0) {
                        detalhesHtml += `<li style="color: var(--os-success);">Validado perfeitamente sem divergências.</li>`;
                    } else {
                        item.detalhes.forEach(d => {
                            detalhesHtml += `<li>${d}</li>`;
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

                tr.innerHTML = `
                    <td><strong>${item.pedido_supra || "-"}</strong></td>
                    <td>${item.cliente_codigo || "-"}</td>
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
    }
});
