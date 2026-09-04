
// -----------------------------------------------------
// MODAL EXPORT NOVO (ENTREGAS/RETIRADAS)
// -----------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
    const btnExportNovo = document.getElementById("btn-export-pdf-novo");
    const modalExportOpcoes = document.getElementById("modal-export-opcoes");
    const modalExportOpcoesClose = document.getElementById("modal-export-opcoes-close");
    const btnExportRomaneio = document.getElementById("btn-export-romaneio-novo");
    const btnExportResumo = document.getElementById("btn-export-resumo-novo");

    if (btnExportNovo) {
        btnExportNovo.addEventListener('click', () => {
            // Check if valid state
            const isListagem = document.getElementById('painel-listagem').style.display !== 'none';
            const isRetTab = window.activeRelatorio === "retiradas" || window.activeRelatorio === "historico-retiradas";
            
            if (isListagem && !isRetTab) {
                // Entregas: Needs a selected checkbox
                const firstChecked = document.querySelector('.chk-carga-item:checked');
                if (!firstChecked) {
                    alert('Você precisa selecionar uma carga (marcar o checkbox) para exportar.');
                    return;
                }
            } else if (!isListagem && !isRetTab) {
                // Inside Entregas form
                if (!window.cargaEmGerenciamento) {
                    alert("Selecione uma carga ou entre em um relatório.");
                    return;
                }
            }
            // For Retiradas (Lote), we don't need validation here, it will just get all.
            
            // Adjust buttons text based on context
            if (isRetTab) {
                btnExportRomaneio.innerHTML = "📄 Exportar Romaneio em Lote";
                btnExportResumo.innerHTML = "📦 Exportar Resumo em Lote";
            } else {
                btnExportRomaneio.innerHTML = "📄 Exportar Romaneio";
                btnExportResumo.innerHTML = "📦 Exportar Resumo de Produtos";
            }

            modalExportOpcoes.style.display = "flex";
        });
    }

    if (modalExportOpcoesClose) {
        modalExportOpcoesClose.addEventListener('click', () => {
            modalExportOpcoes.style.display = "none";
        });
    }

    // Helper to get all IDs on screen for Retiradas
    function getAllRetiradaIdsOnScreen() {
        // As rows have chk-carga-item with value = id
        const checkboxes = document.querySelectorAll('.chk-carga-item');
        const ids = Array.from(checkboxes).map(chk => chk.value).filter(val => val);
        return ids;
    }

    function doNovoExport(tipo) {
        let endpoint = "";
        const isRetTab = window.activeRelatorio === "retiradas" || window.activeRelatorio === "historico-retiradas";
        
        if (isRetTab) {
            const ids = getAllRetiradaIdsOnScreen();
            if (ids.length === 0) {
                alert("Nenhuma retirada encontrada na tela para exportar.");
                return;
            }
            const idsStr = ids.join(',');
            if (tipo === 'romaneio') {
                endpoint = `${window.API_BASE}/api/retiradas/romaneio-lote/pdf?ids=${idsStr}`;
            } else {
                endpoint = `${window.API_BASE}/api/retiradas/resumo-lote/pdf?ids=${idsStr}`;
            }
        } else {
            // Entregas
            let cargaId = "";
            const isListagem = document.getElementById('painel-listagem').style.display !== 'none';
            if (isListagem) {
                const firstChecked = document.querySelector('.chk-carga-item:checked');
                if (firstChecked) cargaId = firstChecked.value;
            } else {
                cargaId = window.cargaEmGerenciamento;
            }

            if (!cargaId) return;

            if (tipo === 'romaneio') {
                endpoint = `${window.API_BASE}/api/relatorios/romaneio-novo/${cargaId}/pdf`;
            } else {
                endpoint = `${window.API_BASE}/api/relatorios/resumo-produtos-novo/${cargaId}/pdf`;
            }
        }

        if (endpoint) {
            const token = window.Auth ? window.Auth.getToken() : '';
            const sep = endpoint.includes('?') ? '&' : '?';
            window.open(`${endpoint}${sep}token=${token}`, '_blank');
        }
        
        modalExportOpcoes.style.display = "none";
    }

    if (btnExportRomaneio) {
        btnExportRomaneio.addEventListener('click', () => doNovoExport('romaneio'));
    }
    if (btnExportResumo) {
        btnExportResumo.addEventListener('click', () => doNovoExport('resumo'));
    }
});
