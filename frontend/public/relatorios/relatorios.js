/**
 * relatorios.js
 * Gerencia a lógica da visualização de 2 colunas do Módulo "Exportar Relatórios"
 */

const API_BASE = window.API_BASE || window.location.origin;

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
// RELATÓRIO 1: FORMAÇÃO DE CARGAS E GERENCIAMENTO
// -----------------------------------------------------

let cargaEmGerenciamento = null;

async function renderFormacaoCargas() {
    // Garante controle de exibição
    document.getElementById('painel-gerenciar-carga').style.display = 'none';
    document.getElementById('painel-listagem').style.display = 'block';

    // Remove listener antigo do clone para evitar bugs
    const oldBtn = document.getElementById("btn-novo");
    const newBtn = oldBtn.cloneNode(true);
    oldBtn.parentNode.replaceChild(newBtn, oldBtn);

    const btnNovoRef = document.getElementById("btn-novo");
    btnNovoRef.textContent = "+ Nova Carga";
    btnNovoRef.style.display = 'inline-block';

    btnNovoRef.addEventListener('click', async () => {
        const numCarga = prompt("Digite um código ou descrição para a Nova Carga:");
        if (!numCarga) return;

        const nwResp = await fetch(`${API_BASE}/api/relatorios/cargas`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}`
            },
            body: JSON.stringify({ numero_carga: numCarga })
        });

        if (nwResp.ok) {
            renderFormacaoCargas();
        } else {
            const err = await nwResp.json();
            alert("Erro: " + (err.detail || "Falha ao criar carga"));
        }
    });

    thead.innerHTML = `
        <tr>
            <th>Nº / Nome da Carga</th>
            <th>Data Cadastro</th>
            <th>Veículo/Motorista</th>
            <th>Qtd Pedidos</th>
            <th>Ações</th>
        </tr>
    `;

    try {
        const [cargasResp, transResp] = await Promise.all([
            fetch(`${API_BASE}/api/relatorios/cargas`, { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } }),
            fetch(`${API_BASE}/api/transporte`, { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } })
        ]);

        if (!cargasResp.ok) throw new Error("Falha ao buscar cargas");

        const cargas = await cargasResp.json();
        const transportes = await transResp.json();

        if (cargas.length === 0) {
            emptyStateEl.style.display = "block";
            return;
        }

        let html = "";
        cargas.forEach(c => {
            const dispData = c.data_criacao ? new Date(c.data_criacao).toLocaleDateString('pt-BR') : "-";
            const trans = transportes.find(t => t.id === c.id_transporte);
            const dispTrans = trans ? `${trans.motorista} - ${trans.veiculo_placa}` : "Pendente";
            const totalPed = c.pedidos ? c.pedidos.length : 0;

            html += `
                <tr>
                    <td><strong>${c.numero_carga}</strong></td>
                    <td>${dispData}</td>
                    <td>${dispTrans}</td>
                    <td>${totalPed}</td>
                    <td>
                       <button class="os-btn os-btn-sm os-btn-secondary btn-gerenciar-carga" data-id="${c.id}" data-nome="${c.numero_carga}">Gerenciar Pedidos</button>
                       <button class="os-btn os-btn-sm os-btn-danger btn-excluir-carga" data-id="${c.id}" style="color:red; border-color:red; margin-left:5px;">Excluir</button>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;

        document.querySelectorAll('.btn-gerenciar-carga').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.target.dataset.id;
                const nome = e.target.dataset.nome;
                abrirGerenciadorDeCarga(id, nome);
            });
        });

        document.querySelectorAll('.btn-excluir-carga').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if (confirm("Excluir definitivamente esta Carga do mapa de expedição?")) {
                    const id = e.target.dataset.id;
                    await fetch(`${API_BASE}/api/relatorios/cargas/${id}`, {
                        method: "DELETE",
                        headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
                    });
                    renderFormacaoCargas();
                }
            });
        });

    } catch (e) {
        console.error(e);
        emptyStateEl.textContent = "Erro ao carregar as cargas. Verifique sua conexão.";
        emptyStateEl.style.display = "block";
    }
}

// -----------------------------------------------------
// FUNÇÕES DE SUB-TELA "Gerenciar Carga"
// -----------------------------------------------------

async function abrirGerenciadorDeCarga(idCarga, numCarga) {
    cargaEmGerenciamento = idCarga;
    document.getElementById('painel-listagem').style.display = 'none';
    document.getElementById('painel-gerenciar-carga').style.display = 'block';
    document.getElementById('titulo-carga-ativa').textContent = "Gerenciando Carga: " + numCarga;

    document.getElementById('btn-voltar-listagem').onclick = () => renderFormacaoCargas();
    document.getElementById('btn-buscar-pedidos').onclick = () => abrirModalBuscaPedidos();

    await carregarPedidosDaCargaAtiva();
}

async function carregarPedidosDaCargaAtiva() {
    const tbodyPedidos = document.getElementById('tbody-pedidos-carga');
    const emptyPedidos = document.getElementById('empty-carga-pedidos');
    tbodyPedidos.innerHTML = '<tr><td colspan="7" style="text-align:center;">Carregando...</td></tr>';

    try {
        const resp = await fetch(`${API_BASE}/api/relatorios/cargas/${cargaEmGerenciamento}/pedidos-detalhes`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        const ped = await resp.json();

        if (ped.length === 0) {
            tbodyPedidos.innerHTML = '';
            emptyPedidos.style.display = 'block';
            return;
        }

        emptyPedidos.style.display = 'none';
        let h = "";
        ped.forEach(p => {
            const peso = p.peso_total ? p.peso_total.toFixed(2).replace('.', ',') : "0,00";
            h += `
                <tr>
                    <td><strong>${p.numero_pedido}</strong></td>
                    <td>${p.cliente_nome || '-'}</td>
                    <td>${p.status}</td>
                    <td>${p.municipio || '-'}</td>
                    <td>${p.rota_principal || '-'}</td>
                    <td>${peso}</td>
                    <td><button class="os-btn os-btn-sm btn-remover-pedido-carga" data-id="${p.id_carga_pedido}" style="color:red; border:1px solid red; background:transparent;">Remover</button></td>
                </tr>
            `;
        });
        tbodyPedidos.innerHTML = h;

        document.querySelectorAll('.btn-remover-pedido-carga').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const linkId = e.target.dataset.id;
                await fetch(`${API_BASE}/api/relatorios/cargas/pedidos/${linkId}`, {
                    method: 'DELETE',
                    headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
                });
                carregarPedidosDaCargaAtiva();
            });
        });
    } catch (e) {
        console.error(e);
        tbodyPedidos.innerHTML = '';
        emptyPedidos.textContent = "Erro de conexão ao carregar os pedidos.";
        emptyPedidos.style.display = 'block';
    }
}

// -----------------------------------------------------
// FUNÇÕES DE BUSCA LIVRE DE PEDIDOS NO MODAL
// -----------------------------------------------------

function abrirModalBuscaPedidos() {
    const modal = document.getElementById('modal-buscar-pedido');
    modal.classList.add('active');

    const inputBusca = document.getElementById('input-busca-pedido-livre');
    const tbodyRes = document.getElementById('tbody-resultado-busca');
    const btnVincular = document.getElementById('btn-vincular-selecionados');
    const chkSelectAll = document.getElementById('chk-select-all-pedidos');

    document.getElementById('modal-buscar-close').onclick = () => {
        modal.classList.remove('active');
        carregarPedidosDaCargaAtiva(); // atualiza a grid atrás ao fechar
    }

    // Função interna para carregar os pedidos ativos
    async function fetchPedidosAbertos() {
        tbodyRes.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px;">Carregando pedidos ativos...</td></tr>';
        inputBusca.value = '';
        if (chkSelectAll) chkSelectAll.checked = false;

        try {
            // Buscamos um número grande de pedidos pendentes para filtro rápido no frontend
            const url = `${API_BASE}/api/pedidos?status=CONFIRMADO,FATURADO&pageSize=300`;
            const resp = await fetch(url, { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } });
            const json = await resp.json();
            const resultados = json.data || [];

            if (resultados.length === 0) {
                tbodyRes.innerHTML = '<tr><td colspan="7" style="text-align: center;">Nenhum pedido compatível encontrado (Nenhum Confirmado ou Faturado localizável).</td></tr>';
                return;
            }

            let html = "";
            resultados.forEach(p => {
                const destMuni = p.municipio || '-';
                const destRota = p.rota_principal || '-';
                const peso = p.peso_total ? p.peso_total.toFixed(2).replace('.', ',') : "0,00";

                const isFaturado = p.status_codigo === "FATURADO";
                const badge = isFaturado
                    ? `<span style="color: green; font-weight: 500;">Faturado</span>`
                    : `<span class="badge-alert">⚠ Confirmado</span>`;

                // Adiciona data attributes para facilitar a busca de texto
                const termoBusca = `${p.numero_pedido} ${p.cliente_nome} ${destMuni} ${destRota}`.toLowerCase();

                html += `
                    <tr class="row-pedido-busca" data-termo="${termoBusca}">
                        <td style="text-align: center;">
                             <input type="checkbox" class="chk-pedido-item" value="${p.numero_pedido}" />
                        </td>
                        <td><strong>${p.numero_pedido}</strong></td>
                        <td>${p.cliente_nome}</td>
                        <td>${destMuni}</td>
                        <td>${destRota}</td>
                        <td>${badge}</td>
                        <td>${peso} kg</td>
                    </tr>
                `;
            });
            tbodyRes.innerHTML = html;
        } catch (e) {
            tbodyRes.innerHTML = '<tr><td colspan="7" style="text-align: center; color: red;">Erro ao buscar pedidos do servidor.</td></tr>';
        }
    }

    // Aciona a busca inicial
    fetchPedidosAbertos();

    // Filtro Local Rápido
    inputBusca.oninput = (e) => {
        const val = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('.row-pedido-busca');
        rows.forEach(r => {
            if (r.dataset.termo.includes(val)) {
                r.style.display = 'table-row';
            } else {
                r.style.display = 'none';
            }
        });
    };

    // Lógica do Checkbox "Selecionar Todos" (Apenas nos visíveis)
    if (chkSelectAll) {
        chkSelectAll.onchange = (e) => {
            const isChecked = e.target.checked;
            const rows = document.querySelectorAll('.row-pedido-busca');
            rows.forEach(r => {
                if (r.style.display !== 'none') {
                    const chk = r.querySelector('.chk-pedido-item');
                    if (chk) chk.checked = isChecked;
                }
            });
        };
    }

    // Botão de Vincular Selecionados
    // Remoção do listener antigo caso o modal seja reaberto e recriado
    if (btnVincular) {
        const newBtnVincular = btnVincular.cloneNode(true);
        btnVincular.parentNode.replaceChild(newBtnVincular, btnVincular);

        newBtnVincular.addEventListener('click', async () => {
            const checkedBoxes = document.querySelectorAll('.chk-pedido-item:checked');
            if (checkedBoxes.length === 0) {
                alert("Selecione pelo menos um pedido!");
                return;
            }

            newBtnVincular.textContent = "Vinculando...";
            newBtnVincular.disabled = true;

            let concluidos = 0;
            let erros = 0;

            // Itera sobre todos os selecionados e envia as requisições
            const chamadas = Array.from(checkedBoxes).map(async (chk) => {
                const numPed = chk.value;
                try {
                    const linkResp = await fetch(`${API_BASE}/api/relatorios/cargas/${cargaEmGerenciamento}/pedidos`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}`
                        },
                        body: JSON.stringify({
                            numero_pedido: numPed.toString(),
                            ordem_carregamento: 0
                        })
                    });

                    if (!linkResp.ok) throw new Error("Erro");

                    // Remove visualmente a linha se o vinculo foi feito com sucesso
                    chk.closest('tr').remove();
                    concluidos++;
                } catch (err) {
                    erros++;
                }
            });

            await Promise.all(chamadas);

            newBtnVincular.textContent = "Vincular Selecionados";
            newBtnVincular.disabled = false;

            if (erros > 0) {
                alert(`${concluidos} adicionados. Houve falha ao adicionar ${erros} pedidos (talvez já vinculados).`);
            }

            // Atualiza a grid por trás, mas mantém modal aberto pra próximas buscas
            carregarPedidosDaCargaAtiva();
        });
    }
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
            fetch(`${API_BASE}/api/relatorios/cargas`, { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } }),
            fetch(`${API_BASE}/api/transporte`, { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } })
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
                    const resp = await fetch(`${API_BASE}/api/relatorios/cargas/${idCarga}`, {
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
        const cResp = await fetch(`${API_BASE}/api/relatorios/cargas`, { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } });
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
                const rResp = await fetch(`${API_BASE}/api/relatorios/cargas/${idCarga}/resumo-produtos`, {
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
        const cResp = await fetch(`${API_BASE}/api/relatorios/cargas`, { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } });
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
                    fetch(`${API_BASE}/api/relatorios/cargas/${idCarga}/resumo-produtos`, { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } }),
                    cargaObj.id_transporte ? fetch(`${API_BASE}/api/transporte/${cargaObj.id_transporte}`, { headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` } }) : Promise.resolve({ ok: true, json: () => null })
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
