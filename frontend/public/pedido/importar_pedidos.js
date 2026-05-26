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
        if (value === null || value === undefined) return "0";
        let formatted = parseFloat(value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (formatted.endsWith(",00")) {
            return formatted.slice(0, -3);
        }
        return formatted;
    }

    // Obter data atual no formato YYYY-MM-DD para o input type="date"
    function obterDataAtualIso() {
        const hoje = new Date();
        const dia = String(hoje.getDate()).padStart(2, '0');
        const mes = String(hoje.getMonth() + 1).padStart(2, '0');
        const ano = hoje.getFullYear();
        return `${ano}-${mes}-${dia}`;
    }

    // Converte data DD/MM/YYYY para YYYY-MM-DD
    function converterDataBrParaIso(dataBrStr) {
        if (!dataBrStr || dataBrStr === "-") return "";
        const parts = dataBrStr.split('/');
        if (parts.length === 3) {
            const dia = parts[0].padStart(2, '0');
            const mes = parts[1].padStart(2, '0');
            const ano = parts[2];
            return `${ano}-${mes}-${dia}`;
        }
        return "";
    }

    // Converte data YYYY-MM-DD para DD/MM/YYYY
    function converterDataIsoParaBr(dataIsoStr) {
        if (!dataIsoStr) return "";
        const parts = dataIsoStr.split('-');
        if (parts.length === 3) {
            const ano = parts[0];
            const mes = parts[1];
            const dia = parts[2];
            return `${dia}/${mes}/${ano}`;
        }
        return "";
    }

    // Encontra a data de faturamento mais recente/atual no formato DD/MM/YYYY
    function obterDataMaisRecenteBr(itens) {
        if (!itens || itens.length === 0) return "";
        let maxDate = null;
        let maxDateStr = "";
        
        itens.forEach(item => {
            const fatDateStr = item.data_faturamento;
            if (fatDateStr && fatDateStr !== "-") {
                const parts = fatDateStr.split('/');
                if (parts.length === 3) {
                    const day = parseInt(parts[0], 10);
                    const month = parseInt(parts[1], 10) - 1; // 0-indexed
                    const year = parseInt(parts[2], 10);
                    const dateObj = new Date(year, month, day);
                    if (!maxDate || dateObj > maxDate) {
                        maxDate = dateObj;
                        maxDateStr = fatDateStr;
                    }
                }
            }
        });
        return maxDateStr;
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
        
        // Obter o dia mais recente presente no arquivo carregado (ou data de hoje como fallback)
        const maisRecenteBr = obterDataMaisRecenteBr(itens);
        const maisRecenteIso = maisRecenteBr ? converterDataBrParaIso(maisRecenteBr) : obterDataAtualIso();

        // Limpar todos os campos de filtros ao renderizar uma nova carga para exibir todos os resultados por padrão
        ["filterPedidoSistema", "filterPedido", "filterDanfe", "filterCliente", "filterDataPedido", "filterDataFat", "filterValor", "filterValorDif", "filterPeso", "filterPesoDif", "filterResultado", "filterStatus"].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.value = "";
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
        const btnExportVal = document.getElementById("btnExportValidation");
        if (btnExportVal) {
            btnExportVal.style.display = "inline-block";
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
            tr.innerHTML = `<td colspan="12" style="text-align: center; color: var(--os-text-secondary);">Nenhum pedido processado.</td>`;
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

                // Formatar valores e pesos
                const valorPlanilha = item.valor_planilha || 0;
                const valorSistema = item.valor_sistema || 0;
                const precoDif = valorPlanilha - valorSistema;

                const pesoPlanilha = item.peso_planilha || 0;
                const pesoSistema = item.peso_sistema || 0;
                const pesoDif = pesoPlanilha - pesoSistema;

                const pesoPlanilhaStr = item.peso_planilha != null ? fmtMoney(item.peso_planilha) : "-";
                const pesoSistemaStr = item.peso_sistema != null ? fmtMoney(item.peso_sistema) : "-";
                const pesoDifStr = fmtMoney(pesoDif) + " kg";

                // Textos normalizados para facilitar busca rápida
                const textoStatus = item.novo_status_pedido === "PEDIDO_NAO_COMPLETO" 
                    ? "Pedido Não Completo" 
                    : (item.novo_status_pedido === "FATURADO_SUPRA" ? "Faturado Supra" : "-");
                const textoDetalhes = Array.isArray(item.detalhes) ? item.detalhes.join(" ") : (item.detalhes || "");

                // Atributos de dados para filtragem ultra-rápida no client-side
                tr.dataset.pedido_sistema = item.id_pedido || "";
                tr.dataset.pedido = item.pedido_supra || "";
                tr.dataset.danfe = item.danfe || "";
                tr.dataset.cliente = item.cliente_codigo || "";
                tr.dataset.data_pedido = item.data_pedido || "";
                tr.dataset.data_fat = item.data_faturamento || "";
                tr.dataset.preco = `R$ ${fmtMoney(valorPlanilha)} / R$ ${fmtMoney(valorSistema)}`;
                tr.dataset.preco_dif = `R$ ${fmtMoney(precoDif)}`;
                tr.dataset.peso = `${pesoPlanilhaStr} / ${pesoSistemaStr}`;
                tr.dataset.peso_dif = pesoDifStr;
                tr.dataset.resultado = resultText;
                tr.dataset.status = textoStatus;
                tr.dataset.detalhes = textoDetalhes;

                tr.innerHTML = `
                    <td><strong>${item.id_pedido || "-"}</strong></td>
                    <td><strong>${item.pedido_supra || "-"}</strong></td>
                    <td>${item.danfe || "-"}</td>
                    <td>${item.cliente_codigo || "-"}</td>
                    <td>${item.data_pedido || "-"}</td>
                    <td>${item.data_faturamento || "-"}</td>
                    <td>R$ ${fmtMoney(valorPlanilha)} / R$ ${fmtMoney(valorSistema)}</td>
                    <td style="font-weight: 600; color: ${precoDif === 0 ? 'var(--os-text)' : (precoDif > 0 ? 'var(--os-warning)' : 'var(--os-error)')};">R$ ${fmtMoney(precoDif)}</td>
                    <td>${pesoPlanilhaStr} / ${pesoSistemaStr}</td>
                    <td style="font-weight: 600; color: ${pesoDif === 0 ? 'var(--os-text)' : (pesoDif > 0 ? 'var(--os-warning)' : 'var(--os-error)')};">${pesoDifStr}</td>
                    <td><span class="${badgeClass}">${resultText}</span></td>
                    <td>${badgeNovoStatus}</td>
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
        const fPedidoSistema = document.getElementById("filterPedidoSistema").value.toLowerCase().trim();
        const fPedido = document.getElementById("filterPedido").value.toLowerCase().trim();
        const fDanfe = document.getElementById("filterDanfe").value.toLowerCase().trim();
        const fCliente = document.getElementById("filterCliente").value.toLowerCase().trim();
        
        // Converter data do calendário (ISO YYYY-MM-DD) para padrão brasileiro para filtrar na tabela
        const fDataPedidoRaw = document.getElementById("filterDataPedido").value;
        const fDataFatRaw = document.getElementById("filterDataFat").value;
        const fDataPedido = converterDataIsoParaBr(fDataPedidoRaw).toLowerCase();
        const fDataFat = converterDataIsoParaBr(fDataFatRaw).toLowerCase();
        
        const fPreco = document.getElementById("filterValor").value.toLowerCase().trim();
        const fPrecoDif = document.getElementById("filterValorDif").value.toLowerCase().trim();
        const fPeso = document.getElementById("filterPeso").value.toLowerCase().trim();
        const fPesoDif = document.getElementById("filterPesoDif").value.toLowerCase().trim();
        const fResultado = document.getElementById("filterResultado").value.toLowerCase().trim();
        const fStatus = document.getElementById("filterStatus").value.toLowerCase().trim();

        const rows = resultsBody.querySelectorAll("tr");
        rows.forEach(tr => {
            // Se for o tr informativo de tabela vazia, ignora
            if (tr.querySelector("td[colspan]")) return;

            const matchPedidoSistema = !fPedidoSistema || String(tr.dataset.pedido_sistema).toLowerCase().includes(fPedidoSistema);
            const matchPedido = !fPedido || String(tr.dataset.pedido).toLowerCase().includes(fPedido);
            const matchDanfe = !fDanfe || String(tr.dataset.danfe).toLowerCase().includes(fDanfe);
            const matchCliente = !fCliente || String(tr.dataset.cliente).toLowerCase().includes(fCliente);
            const matchDataPedido = !fDataPedido || String(tr.dataset.data_pedido).toLowerCase().includes(fDataPedido);
            const matchDataFat = !fDataFat || String(tr.dataset.data_fat).toLowerCase().includes(fDataFat);
            const matchPreco = !fPreco || String(tr.dataset.preco).toLowerCase().includes(fPreco);
            const matchPrecoDif = !fPrecoDif || String(tr.dataset.preco_dif).toLowerCase().includes(fPrecoDif);
            const matchPeso = !fPeso || String(tr.dataset.peso).toLowerCase().includes(fPeso);
            const matchPesoDif = !fPesoDif || String(tr.dataset.peso_dif).toLowerCase().includes(fPesoDif);
            const matchResultado = !fResultado || String(tr.dataset.resultado).toLowerCase() === fResultado;
            const matchStatus = !fStatus || String(tr.dataset.status).toLowerCase().includes(fStatus);

            if (matchPedidoSistema && matchPedido && matchDanfe && matchCliente && matchDataPedido && matchDataFat && matchPreco && matchPrecoDif && matchPeso && matchPesoDif && matchResultado && matchStatus) {
                tr.style.display = "";
            } else {
                tr.style.display = "none";
            }
        });
    }

    // Vincular os inputs de filtros aos event listeners
    ["filterPedidoSistema", "filterPedido", "filterDanfe", "filterCliente", "filterDataPedido", "filterDataFat", "filterValor", "filterValorDif", "filterPeso", "filterPesoDif", "filterResultado", "filterStatus"].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("input", applyFilters);
            if (el.tagName === "SELECT" || el.type === "date") {
                el.addEventListener("change", applyFilters);
            }
        }
    });

    // No carregamento inicial, os filtros de data começam vazios para listar todos os resultados por padrão
    const inputFat = document.getElementById("filterDataFat");
    if (inputFat) {
        inputFat.value = "";
    }

    // Carregar dados salvos do localStorage se existirem
    const savedData = localStorage.getItem("lastImportData");
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            // Se for cache legado sem o campo id_pedido, limpa automaticamente para evitar exibição de colunas vazias
            if (data && data.itens && data.itens.length > 0 && typeof data.itens[0].id_pedido === 'undefined') {
                localStorage.removeItem("lastImportData");
            } else {
                renderResults(data);
            }
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
                const btnExportVal = document.getElementById("btnExportValidation");
                if (btnExportVal) btnExportVal.style.display = "none";
                if (duplicateAlert) duplicateAlert.style.display = "none";
            }
        });
    }

    // Exportação do Relatório de Validação para CSV
    function exportValidationCSV() {
        const rows = resultsBody.querySelectorAll("tr");
        if (!rows.length || (rows.length === 1 && rows[0].querySelector("td[colspan]"))) {
            alert("Não há dados para exportar.");
            return;
        }
        
        let csv = "Nº Pedido Sistema;Nº Pedido Supra;Danfe;Cód. Cliente;Data Pedido;Data Faturamento;Preço (Planilha / Sistema);Preço Dif;Peso (Planilha / Sistema);Peso Dif;Resultado;Status Atualizado (Banco)\n";
        rows.forEach(tr => {
            if (tr.querySelector("td[colspan]")) return;
            // Se a linha estiver oculta por algum filtro ativo, não exporta
            if (tr.style.display === "none") return;

            const cells = tr.querySelectorAll("td");
            if (cells.length < 12) return;
            
            const pedSis = cells[0].innerText.trim().replace(/;/g, ",");
            const pedSup = cells[1].innerText.trim().replace(/;/g, ",");
            const danfe = cells[2].innerText.trim().replace(/;/g, ",");
            const cli = cells[3].innerText.trim().replace(/;/g, ",");
            const dtPed = cells[4].innerText.trim().replace(/;/g, ",");
            const dtFat = cells[5].innerText.trim().replace(/;/g, ",");
            const preco = cells[6].innerText.trim().replace(/;/g, ",");
            const precoDif = cells[7].innerText.trim().replace(/;/g, ",");
            const peso = cells[8].innerText.trim().replace(/;/g, ",");
            const pesoDif = cells[9].innerText.trim().replace(/;/g, ",");
            const res = cells[10].innerText.trim().replace(/;/g, ",");
            const status = cells[11].innerText.trim().replace(/;/g, ",");
            
            csv += `"${pedSis}";"${pedSup}";"${danfe}";"${cli}";"${dtPed}";"${dtFat}";"${preco}";"${precoDif}";"${peso}";"${pesoDif}";"${res}";"${status}"\n`;
        });
        
        const blob = new Blob(["\ufeff" + csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `relatorio_validacao_import_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    const btnExportVal = document.getElementById("btnExportValidation");
    if (btnExportVal) {
        btnExportVal.addEventListener("click", exportValidationCSV);
    }
});
