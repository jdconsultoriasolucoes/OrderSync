/**
 * relatorios.js
 * Gerencia a lógica da visualização de 2 colunas do Módulo "Exportar Relatórios"
 */

const relatoriosDict = {
    "formacao": {
        title: "Manutenção de Pedidos / Formação de Cargas",
        desc: "Organizar os pedidos para formação de cargas e planejamento de rota de entrega."
    },
    "romaneio": {
        title: "Romaneio",
        desc: "Gerar documento com informações da carga montada para transporte e frotista."
    },
    "resumo": {
        title: "Resumo de Produtos",
        desc: "Resumo consolidado e somatório de produtos baseados em uma Carga montada."
    },
    "completo": {
        title: "Relatório Completo (Romaneio + Produtos)",
        desc: "Documento agregando os dados do Transporte e todos os Itens consolidados."
    }
};

let activeRelatorio = "formacao";

// DOM Elements
const menuBtns = document.querySelectorAll('.relatorios-menu button');
const uiTitle = document.getElementById("relatorio-titulo-view");
const uiDesc = document.getElementById("relatorio-desc-view");
const thead = document.getElementById("tabela-head");
const tbody = document.getElementById("tabela-body");
const loadingEl = document.getElementById("loading");
const emptyStateEl = document.getElementById("empty-state");

// Botões
const btnNovo = document.getElementById("btn-novo");
const btnExport = document.getElementById("btn-export-pdf");
const inputSearch = document.getElementById("relatorio-pesquisa");

document.addEventListener("DOMContentLoaded", () => {
    // Registra clique no menu lateral
    menuBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Remove active dos outros
            menuBtns.forEach(b => b.classList.remove('active'));
            // Coloca active no atual
            e.currentTarget.classList.add('active');

            activeRelatorio = e.currentTarget.dataset.rel;
            renderRelatorioView(activeRelatorio);
        });
    });

    // Primeira carga
    renderRelatorioView(activeRelatorio);
});

async function renderRelatorioView(relKey) {
    // 1. Altera Cabeçalho
    uiTitle.textContent = relatoriosDict[relKey].title;
    uiDesc.textContent = relatoriosDict[relKey].desc;

    // 2. Limpa Tabela
    thead.innerHTML = "";
    tbody.innerHTML = "";
    emptyStateEl.style.display = "none";
    loadingEl.style.display = "block";

    // 3. Invoca a lógica de renderização específica
    try {
        if (relKey === "formacao") {
            await renderFormacaoCargas();
        } else if (relKey === "romaneio") {
            await renderRomaneio();
        } else if (relKey === "resumo") {
            await renderResumoProdutos();
        } else if (relKey === "completo") {
            await renderRelatorioCompleto();
        }
    } catch (err) {
        console.error("Erro ao carregar relatório:", err);
        emptyStateEl.textContent = "Erro ao carregar dados do relatório.";
        emptyStateEl.style.display = "block";
    } finally {
        loadingEl.style.display = "none";
    }
}

// -----------------------------------------------------
// RELATÓRIO 1: FORMAÇÃO DE CARGAS
// -----------------------------------------------------
async function renderFormacaoCargas() {
    // Exibe/Esconde botões específicos
    btnNovo.textContent = "+ Gerar Carga";

    thead.innerHTML = `
        <tr>
            <th>Nº Carga</th>
            <th>Nº Pedido</th>
            <th>Cliente</th>
            <th>Status Pedido</th>
            <th>Município/Rota</th>
            <th>Peso Líq.</th>
            <th>Ações</th>
        </tr>
    `;

    try {
        // Busca os pedidos confirmados e faturados 
        const response = await fetch('/api/pedidos?status=CONFIRMADO,FATURADO&pageSize=100', {
            headers: {
                "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}`
            }
        });

        if (!response.ok) throw new Error("Falha ao buscar pedidos");

        const json = await response.json();
        const pedidos = json.data || [];

        if (pedidos.length === 0) {
            emptyStateEl.style.display = "block";
            return;
        }

        let html = "";
        pedidos.forEach(p => {
            const isFaturado = p.status_codigo === "FATURADO";
            const badge = isFaturado
                ? `<span style="color: green; font-weight: 500;">Faturado</span>`
                : `<span class="badge-alert">⚠ Pedido não faturado</span>`;

            const destino = p.municipio
                ? `${p.municipio} - ${p.rota_principal || 'S/ Rota'}`
                : "A Combinar / Retirada";

            const peso = p.peso_total ? p.peso_total.toFixed(2).replace('.', ',') : "0,00";

            html += `
                <tr>
                    <!-- Assumindo placeholder livre para Carga -->
                    <td><input type="text" class="os-input input-carga" data-pedido="${p.numero_pedido}" style="width: 110px; padding: 4px;" placeholder="Em aberto"></td>
                    <td><strong>${p.numero_pedido}</strong></td>
                    <td>${p.cliente_nome}</td>
                    <td>${badge}</td>
                    <td>${destino}</td>
                    <td>${peso} kg</td>
                    <td>
                       <button class="os-btn os-btn-sm os-btn-primary btn-save-carga" data-pedido="${p.numero_pedido}">Vincular</button>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;

        // Listener para botão salvar carga
        document.querySelectorAll('.btn-save-carga').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const numPedido = e.target.dataset.pedido;
                const inputCarga = document.querySelector(`.input-carga[data-pedido="${numPedido}"]`);
                const numCarga = inputCarga.value.trim();

                if (!numCarga) {
                    alert("Digite um número ou código para a carga.");
                    return;
                }

                await salvarVinculoCarga(numCarga, numPedido, btn);
            });
        });

    } catch (e) {
        console.error(e);
        emptyStateEl.textContent = "Erro ao carregar os pedidos. Verifique sua conexão.";
        emptyStateEl.style.display = "block";
    }
}

// Helper: Tenta vincular o pedido à carga no backend
async function salvarVinculoCarga(numCarga, numPedido, btnRef) {
    btnRef.textContent = "...";
    btnRef.disabled = true;

    try {
        // Passo 1: Verifica/Cria a Carga (cabeçalho)
        let idCarga = await garantirCabecalhoCarga(numCarga);
        if (!idCarga) throw new Error("Carga Inválida");

        // Passo 2: Insere o Pedido na tb_cargas_pedidos 
        const linkResp = await fetch(`/relatorios/cargas/${idCarga}/pedidos`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}`
            },
            body: JSON.stringify({
                numero_pedido: numPedido.toString(),
                ordem_carregamento: 0
            })
        });

        if (!linkResp.ok) {
            const err = await linkResp.json();
            throw new Error(err.detail || "Erro ao vincular pedido na carga");
        }

        btnRef.textContent = "Salvo!";
        btnRef.classList.replace("os-btn-primary", "os-btn-secondary");
    } catch (e) {
        alert(e.message);
        btnRef.textContent = "Tentar Novamente";
        btnRef.disabled = false;
    }
}

// Garante que o cabeçalho "Carga X" exista. Se não existir, ele cria. (Upsert)
async function garantirCabecalhoCarga(numCarga) {
    // Tenta buscar se existe 
    const cResp = await fetch(`/relatorios/cargas`, {
        headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
    });
    const cargas = await cResp.json();
    const existe = cargas.find(c => c.numero_carga === numCarga);
    if (existe) return existe.id;

    // Se não existe, posta uma nova
    const nwResp = await fetch(`/relatorios/cargas`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}`
        },
        body: JSON.stringify({ numero_carga: numCarga })
    });

    if (nwResp.ok) {
        const js = await nwResp.json();
        return js.id;
    }
    return null;
}

// -----------------------------------------------------
// RELATÓRIO 2: ROMANEIO
// -----------------------------------------------------
async function renderRomaneio() {
    btnNovo.textContent = "+ Criar Romaneio";

    thead.innerHTML = `
        <tr>
            <th>Nº Carga</th>
            <th>Motorista / Veículo</th>
            <th>Cliente</th>
            <th>Município</th>
            <th>Peso total</th>
            <th>Ações</th>
        </tr>
    `;

    try {
        const [cargasResp, transResp] = await Promise.all([
            fetch('/relatorios/cargas', { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } }),
            fetch('/transporte', { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } })
        ]);

        if (!cargasResp.ok || !transResp.ok) throw new Error("Erro ao buscar dados do Romaneio");

        const cargas = await cargasResp.json();
        const transportes = await transResp.json();

        if (cargas.length === 0) {
            emptyStateEl.style.display = "block";
            return;
        }

        // Constrói Dropdown de Transportes para reutilizar em todas as linhas
        let optTrans = `<option value="">-- Selecione o Veículo/Motorista --</option>`;
        transportes.forEach(t => {
            optTrans += `<option value="${t.id}">${t.veiculo_placa} - ${t.motorista} (${t.transportadora})</option>`;
        });

        let html = "";
        cargas.forEach(c => {
            // Em uma implementação real avançada, o peso da carga = soma(peso do pedido em tb_cargas_pedidos). 
            // Para o visual inicial, vamos simular ou deixar o usuário ciente que a agregação ocorre.

            const transSelecionado = c.id_transporte || "";

            html += `
                <tr>
                    <td><strong>${c.numero_carga}</strong></td>
                    <td>
                        <select class="os-input sel-transporte" data-carga="${c.id}" style="max-width:300px;">
                            ${optTrans}
                        </select>
                    </td>
                    <td>-</td>
                    <td>-</td>
                    <td><em>Agrupado</em></td>
                    <td>
                        <button class="os-btn os-btn-sm os-btn-primary btn-save-romaneio" data-carga="${c.id}">Salvar Motorista</button>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;

        // Recupera valores selecionados no banco
        cargas.forEach(c => {
            if (c.id_transporte) {
                const sel = document.querySelector(`.sel-transporte[data-carga="${c.id}"]`);
                if (sel) sel.value = c.id_transporte;
            }
        });

        // Botões salvar
        document.querySelectorAll('.btn-save-romaneio').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const idCarga = e.target.dataset.carga;
                const sel = document.querySelector(`.sel-transporte[data-carga="${idCarga}"]`);

                btn.textContent = "...";
                try {
                    const resp = await fetch(`/relatorios/cargas/${idCarga}`, {
                        method: "PUT",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}`
                        },
                        body: JSON.stringify({ id_transporte: parseInt(sel.value) || null })
                    });

                    if (!resp.ok) throw new Error("Erro");

                    btn.textContent = "Salvo!";
                    btn.classList.replace("os-btn-primary", "os-btn-secondary");
                } catch (err) {
                    alert("Erro ao vincular transporte à carga.");
                    btn.textContent = "Salvar Motorista";
                }
            });
        });

    } catch (e) {
        console.error(e);
        emptyStateEl.textContent = "Erro ao carregar os dados de Cargas e Transportes.";
        emptyStateEl.style.display = "block";
    }
}

// -----------------------------------------------------
// RELATÓRIO 3: RESUMO DE PRODUTOS
// -----------------------------------------------------
async function renderResumoProdutos() {
    try {
        // Carrega as cargas para o dropdown (Filtro)
        const cResp = await fetch('/relatorios/cargas', { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } });
        if (!cResp.ok) throw new Error("Erro");
        const cargas = await cResp.json();

        if (cargas.length === 0) {
            emptyStateEl.style.display = "block";
            emptyStateEl.textContent = "Nenhuma carga formada no sistema ainda.";
            return;
        }

        let optCargas = `<option value="">-- Escolha uma Carga --</option>`;
        cargas.forEach(c => { optCargas += `<option value="${c.id}">${c.numero_carga}</option>`; });

        // Injeta a Carga no Head para visualização e filtro
        thead.innerHTML = `
            <tr><td colspan="6" style="background:#f8fafc; padding: 12px; border-bottom: 2px solid var(--os-border);">
                <span style="font-weight: 600; margin-right: 12px;">Filtrar Carga:</span>
                <select class="os-input" id="sel-resumo-carga" style="max-width: 300px; display:inline-block;">
                    ${optCargas}
                </select>
            </td></tr>
            <tr>
                <th>Código</th>
                <th>Descrição</th>
                <th>Qtd Total</th>
                <th>Unidade</th>
                <th>Embalagem</th>
                <th>Peso Liq. Total</th>
            </tr>
        `;

        emptyStateEl.style.display = "block";
        emptyStateEl.textContent = "Selecione uma carga acima para carregar o resumo dos produtos.";

        // Listener do Select
        const sel = document.getElementById("sel-resumo-carga");
        sel.addEventListener("change", async (e) => {
            const idCarga = e.target.value;
            if (!idCarga) {
                tbody.innerHTML = "";
                emptyStateEl.style.display = "block";
                return;
            }

            loadingEl.style.display = "block";
            emptyStateEl.style.display = "none";
            tbody.innerHTML = "";

            try {
                const rResp = await fetch(`/relatorios/cargas/${idCarga}/resumo-produtos`, {
                    headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
                });
                if (!rResp.ok) throw new Error("Falha ao buscar resumo de produtos");

                const prods = await rResp.json();
                if (prods.length === 0) {
                    emptyStateEl.style.display = "block";
                    emptyStateEl.textContent = "Esta carga não possui produtos listados.";
                } else {
                    let h = "";
                    prods.forEach(p => {
                        const pesoStr = p.peso_liquido_total ? p.peso_liquido_total.toFixed(3).replace('.', ',') : "0,000";
                        h += `
                            <tr>
                                <td><strong>${p.codigo || '-'}</strong></td>
                                <td>${p.descricao}</td>
                                <td>${p.qtd_total}</td>
                                <td>${p.unidade || 'UN'}</td>
                                <td>${p.embalagem || '-'}</td>
                                <td>${pesoStr} kg</td>
                            </tr>
                        `;
                    });
                    tbody.innerHTML = h;
                }
            } catch (err) {
                console.error(err);
                emptyStateEl.style.display = "block";
                emptyStateEl.textContent = "Erro de conexão ao buscar resumo.";
            } finally {
                loadingEl.style.display = "none";
            }
        });

    } catch (e) {
        console.error(e);
        emptyStateEl.style.display = "block";
        emptyStateEl.textContent = "Erro ao buscar dados.";
    }
}

// -----------------------------------------------------
// RELATÓRIO 4: RELATÓRIO COMPLETO
// -----------------------------------------------------
async function renderRelatorioCompleto() {
    try {
        const cResp = await fetch('/relatorios/cargas', { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } });
        if (!cResp.ok) throw new Error("Erro");
        const cargas = await cResp.json();

        if (cargas.length === 0) {
            emptyStateEl.style.display = "block";
            return;
        }

        let optCargas = `<option value="">-- Escolha uma Carga --</option>`;
        cargas.forEach(c => { optCargas += `<option value="${c.id}">${c.numero_carga}</option>`; });

        thead.innerHTML = `
            <tr><td colspan="4" style="background:#f8fafc; padding: 12px; border-bottom: 2px solid var(--os-border);">
                <span style="font-weight: 600; margin-right: 12px;">Carregar Documento Unificado da Carga:</span>
                <select class="os-input" id="sel-completo-carga" style="max-width: 300px; display:inline-block;">
                    ${optCargas}
                </select>
            </td></tr>
        `;

        emptyStateEl.style.display = "block";
        emptyStateEl.textContent = "Selecione uma carga para unificar o documento (Romaneio da Carga + Resumo de Produtos).";

        const sel = document.getElementById("sel-completo-carga");
        sel.addEventListener("change", async (e) => {
            const idCarga = e.target.value;
            if (!idCarga) {
                tbody.innerHTML = "";
                emptyStateEl.style.display = "block";
                return;
            }

            loadingEl.style.display = "block";
            emptyStateEl.style.display = "none";
            tbody.innerHTML = "";

            try {
                // Fetch Triplo: Detalhes Carga, Transporte específico e Produtos
                const cargaObj = cargas.find(c => c.id == idCarga);

                const [rResp, tResp] = await Promise.all([
                    fetch(`/relatorios/cargas/${idCarga}/resumo-produtos`, { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } }),
                    cargaObj.id_transporte ? fetch(`/transporte/${cargaObj.id_transporte}`, { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } }) : Promise.resolve({ ok: true, json: () => null })
                ]);

                const prods = rResp.ok ? await rResp.json() : [];
                const trans = tResp.ok ? await tResp.json() : null;

                const dt = new Date().toLocaleDateString('pt-BR');
                document.querySelector('.relatorios-content').setAttribute('data-date', dt);

                let h = `
                    <tr style="background:#f1f5f9; border-top: 2px solid #ccc;"><td colspan="4"><strong>CABEÇALHO DA CARGA - ROMANEIO DE TRANSPORTE</strong></td></tr>
                    <tr>
                        <td width="25%"><strong>Nº Identificação Carga:</strong></td>
                        <td width="25%">${cargaObj.numero_carga}</td>
                        <td width="25%"><strong>Data Carregamento:</strong></td>
                        <td width="25%">${cargaObj.data_carregamento ? new Date(cargaObj.data_carregamento).toLocaleDateString('pt-BR') : "-"}</td>
                    </tr>
                    <tr>
                        <td><strong>Motorista / Veículo:</strong></td>
                        <td>${trans ? (trans.motorista + " - " + trans.veiculo_placa) : "Transporte Não Informado"}</td>
                        <td><strong>Transportadora:</strong></td>
                        <td>${trans ? trans.transportadora : "-"}</td>
                    </tr>
                    
                    <tr style="background:#f1f5f9; border-top: 2px solid #ccc; border-bottom: 2px solid #ccc;">
                        <td colspan="4"><strong>CONSOLIDADO DE PRODUTOS A CARREGAR</strong></td>
                    </tr>
                `;

                if (prods.length > 0) {
                    h += `
                        <tr style="background: #fafafa">
                            <th>Código / Descrição</th>
                            <th>Embalagem</th>
                            <th>Quantidade (Unid)</th>
                            <th>Peso Liq. Consolidado</th>
                        </tr>
                    `;
                    let pesoTotalCarga = 0;
                    prods.forEach(p => {
                        pesoTotalCarga += p.peso_liquido_total;
                        h += `
                            <tr>
                                <td>${p.codigo || '-'} - ${p.descricao}</td>
                                <td>${p.embalagem || '-'}</td>
                                <td>${p.qtd_total} ${p.unidade || 'UN'}</td>
                                <td>${(p.peso_liquido_total || 0).toFixed(3).replace('.', ',')} kg</td>
                            </tr>
                        `;
                    });
                    h += `
                        <tr style="background: #fafafa; font-weight: bold;">
                            <td colspan="3" style="text-align:right">TOTAL PESO LÍQUIDO DA CARGA:</td>
                            <td>${pesoTotalCarga.toFixed(3).replace('.', ',')} kg</td>
                        </tr>
                    `;
                } else {
                    h += `<tr><td colspan="4" style="text-align:center; padding: 20px;">Não há produtos faturados associados nesta carga.</td></tr>`;
                }

                tbody.innerHTML = h;
            } catch (err) {
                console.error(err);
                emptyStateEl.style.display = "block";
                emptyStateEl.textContent = "Erro de conexão ao montar o relatório estrutural.";
            } finally {
                loadingEl.style.display = "none";
            }
        });

    } catch (e) {
        console.error(e);
        emptyStateEl.style.display = "block";
        emptyStateEl.textContent = "Erro ao buscar dados.";
    }
}

// Global Event para impressão em tela
btnExport.addEventListener('click', () => {
    window.print();
});
