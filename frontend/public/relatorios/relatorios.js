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

// Botões (Sendo dinâmicos, buscaremos via document quando necessário ou atualizaremos a ref)
let btnNovo = document.getElementById("btn-novo");
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
// FUNÇÃO PADRÃO PARA LISTA DE CARGAS
// -----------------------------------------------------

async function renderStandardCargaList(tipo) {
    document.getElementById('painel-gerenciar-carga').style.display = 'none';
    document.getElementById('painel-listagem').style.display = 'block';

    // Remove listener antigo do clone para evitar bugs
    const oldBtn = document.getElementById("btn-novo");
    const newBtn = oldBtn.cloneNode(true);
    oldBtn.parentNode.replaceChild(newBtn, oldBtn);

    const btnNovoRef = document.getElementById("btn-novo");
    btnNovo = btnNovoRef;

    if (activeRelatorio === "formacao") {
        btnNovoRef.textContent = "+ Nova Carga";
        btnNovoRef.style.display = 'inline-block';
        btnNovoRef.addEventListener('click', abrirModalNovaCarga);
    } else {
        btnNovoRef.style.display = 'none';
    }

    thead.innerHTML = `
        <tr>
            <th style="width: 40px; text-align: center;"><input type="checkbox" id="chk-all-cargas"></th>
            <th>Nº Carga</th>
            <th>Nome / Descrição</th>
            <th>Data Cadastro</th>
            <th>Ações</th>
        </tr>
    `;

    try {
        const resp = await fetch(`${API_BASE}/api/relatorios/cargas`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        if (!resp.ok) throw new Error("Erro");
        const cargas = await resp.json();

        if (cargas.length === 0) {
            emptyStateEl.style.display = "block";
            return;
        }

        let html = "";
        cargas.forEach(c => {
            const dispData = c.data_criacao ? new Date(c.data_criacao).toLocaleDateString('pt-BR') : "-";
            html += `
                <tr>
                    <td style="text-align: center;"><input type="checkbox" class="chk-carga-item" value="${c.id}"></td>
                    <td><strong>${c.numero_carga}</strong></td>
                    <td>${c.nome_carga || '-'}</td>
                    <td>${dispData}</td>
                    <td>
                       <button class="os-btn os-btn-sm os-btn-secondary btn-gerenciar-carga" data-id="${c.id}" data-nome="${c.numero_carga}">Gerenciar / Ver ${tipo}</button>
                       ${activeRelatorio === 'formacao' ? `<button class="os-btn os-btn-sm os-btn-danger btn-excluir-carga" data-id="${c.id}">Excluir</button>` : ''}
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
                if (confirm("Excluir definitivamente esta Carga?")) {
                    const id = e.target.dataset.id;
                    const row = e.target.closest('tr');
                    await fetch(`${API_BASE}/api/relatorios/cargas/${id}`, {
                        method: "DELETE",
                        headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
                    });
                    if (row) row.remove();
                }
            });
        });
    } catch (e) {
        console.error(e);
        emptyStateEl.style.display = "block";
    }
}

async function renderFormacaoCargas() { await renderStandardCargaList("Carga"); }
async function renderRomaneio() { await renderStandardCargaList("Romaneio"); }
async function renderResumoProdutos() { await renderStandardCargaList("Resumo"); }

function abrirModalNovaCarga() {
    const modalNovaCarga = document.getElementById('modal-nova-carga');
    modalNovaCarga.classList.add('active');

    const inNum = document.getElementById('input-nova-carga-numero');
    const inNome = document.getElementById('input-nova-carga-nome');
    inNum.value = ''; inNome.value = '';

    const closeNovaCarga = () => modalNovaCarga.classList.remove('active');
    document.getElementById('modal-nova-carga-close').onclick = closeNovaCarga;
    document.getElementById('btn-cancelar-nova-carga').onclick = closeNovaCarga;

    const btnSalvar = document.getElementById('btn-salvar-nova-carga');
    const newBtnSalvar = btnSalvar.cloneNode(true);
    btnSalvar.parentNode.replaceChild(newBtnSalvar, btnSalvar);

    newBtnSalvar.addEventListener('click', async () => {
        const numCarga = inNum.value.trim();
        const nomeCarga = inNome.value.trim();
        if (!numCarga) { alert("O número da Carga é obrigatório."); return; }

        const nwResp = await fetch(`${API_BASE}/api/relatorios/cargas`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}`
            },
            body: JSON.stringify({ numero_carga: numCarga, nome_carga: nomeCarga })
        });

        if (nwResp.ok) { closeNovaCarga(); renderFormacaoCargas(); }
        else { alert("Falha ao criar carga"); }
    });
}

// -----------------------------------------------------
// FUNÇÕES DE SUB-TELA "Gerenciar Carga"
// -----------------------------------------------------

async function abrirGerenciadorDeCarga(idCarga, numCarga) {
    cargaEmGerenciamento = idCarga;
    numCargaAtiva = numCarga;
    document.getElementById('painel-listagem').style.display = 'none';
    document.getElementById('painel-gerenciar-carga').style.display = 'block';

    const uiActiveHeader = document.getElementById('titulo-carga-ativa');
    uiActiveHeader.innerHTML = 'Carregando detalhes da carga...';

    // Carregar Detalhes da Carga e Transportes
    try {
        const [respCarga, respTransp] = await Promise.all([
            fetch(`${API_BASE}/api/relatorios/cargas/${idCarga}`, {
                headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
            }),
            fetch(`${API_BASE}/api/transporte`, {
                headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
            })
        ]);

        const carga = await respCarga.json();
        const transportes = await respTransp.json();

        const dataCarregamentoVal = carga.data_carregamento ? carga.data_carregamento.split('T')[0] : "";

        let transpOptions = '<option value="">Selecione um Transporte...</option>';
        transportes.forEach(t => {
            const selected = (t.id === carga.id_transporte) ? 'selected' : '';
            transpOptions += `<option value="${t.id}" ${selected}>${t.transportadora} - ${t.motorista} (${t.veiculo_placa})</option>`;
        });

        if (activeRelatorio === "formacao") {
            const firstPed = (carga.pedidos_detalhes && carga.pedidos_detalhes.length > 0) ? carga.pedidos_detalhes[0] : null;
            const filialFornecedor = firstPed ? (firstPed.fornecedor || "Matriz SUPRA LOG") : "Matriz SUPRA LOG";

            uiActiveHeader.style.display = 'block';
            uiActiveHeader.innerHTML = `
                <div class="compact-header-container">
                    <div class="compact-header-info">
                        <div class="ch-field" style="min-width: 150px;">
                            <label>Filial</label>
                            <input type="text" id="in-header-filial" class="os-input os-input-sm" value="Carregando..." disabled>
                        </div>
                        <div class="ch-field" style="width: 80px;">
                            <label>Nº Carga</label>
                            <input type="text" class="os-input os-input-sm" value="${numCarga}" disabled>
                        </div>
                    </div>
                </div>
            `;
        } else {
            uiActiveHeader.style.display = 'block';
            uiActiveHeader.innerHTML = `
            <div class="compact-header-container">
                <div class="compact-header-info">
                    <div class="ch-field" style="min-width: 150px;">
                        <label>Filial</label>
                        <input type="text" id="in-header-filial" class="os-input os-input-sm" value="Matriz SUPRA LOG" disabled>
                    </div>
                    <div class="ch-field" style="width: 80px;">
                        <label>Nº Carga</label>
                        <input type="text" class="os-input os-input-sm" value="${numCarga}" disabled>
                    </div>
                    <div class="ch-field">
                        <label>Data Carregamento</label>
                        <input type="date" id="in-header-data" class="os-input os-input-sm" value="${dataCarregamentoVal}" ${activeRelatorio === 'resumo' ? 'disabled' : ''}>
                    </div>
                    <div class="ch-field" style="flex: 1;">
                        <label>Transporte (Transportadora / Motorista / Veículo / Placa)</label>
                        <select id="sel-header-transporte" class="os-input os-input-sm" ${activeRelatorio === 'resumo' ? 'disabled' : ''}>
                            ${transpOptions}
                        </select>
                    </div>
                    <div class="ch-actions">
                        <button class="os-btn os-btn-primary os-btn-sm" id="btn-save-carga-header">Salvar Cabeçalho</button>
                    </div>
                </div>
            </div>
        `;
        }

        if (document.getElementById('btn-save-carga-header') && activeRelatorio !== 'resumo') {
            document.getElementById('btn-save-carga-header').addEventListener('click', async () => {
                const dt = document.getElementById('in-header-data').value;
                const tr = document.getElementById('sel-header-transporte').value;

                const btn = document.getElementById('btn-save-carga-header');
                btn.textContent = "Salvando...";

                const updateResp = await fetch(`${API_BASE}/api/relatorios/cargas/${idCarga}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}`
                    },
                    body: JSON.stringify({
                        data_carregamento: dt || null,
                        id_transporte: parseInt(tr) || null
                    })
                });

                if (updateResp.ok) {
                    btn.textContent = "Salvo!";
                    setTimeout(() => { btn.textContent = "Salvar Dados do Cabeçalho"; }, 2000);
                } else {
                    alert("Erro ao salvar cabeçalho");
                    btn.textContent = "Erro!";
                }
            });
        }

    } catch (e) {
        console.error(e);
        uiActiveHeader.textContent = "Gerenciando Carga: " + numCarga;
    }

    document.getElementById('btn-voltar-listagem').onclick = () => renderRelatorioView(activeRelatorio);

    const btnBusca = document.getElementById('btn-buscar-pedidos');
    if (activeRelatorio === "resumo") {
        btnBusca.style.display = 'none';
        await carregarResumoProdutosDaCargaAtiva();
    } else {
        btnBusca.style.display = 'inline-block';
        btnBusca.onclick = () => abrirModalBuscaPedidos();
        await carregarPedidosDaCargaAtiva();
    }
}

async function carregarPedidosDaCargaAtiva() {
    const tbodyPedidos = document.getElementById('tbody-pedidos-carga');
    const emptyPedidos = document.getElementById('empty-carga-pedidos');
    const tableWrap = tbodyPedidos.closest('.os-table-wrap');
    const theadTable = tableWrap.querySelector('table thead');

    // Cabeçalho dinâmico baseado no tipo de relatório
    if (activeRelatorio === "formacao") {
        theadTable.innerHTML = `
            <tr>
                <th style="font-size: 11px; width: 80px;">Nº Carga</th>
                <th style="font-size: 11px;">Nº Pedido</th>
                <th style="font-size: 11px;">Peso Líq. Total</th>
                <th style="font-size: 11px;">Código</th>
                <th style="font-size: 11px;">Cliente</th>
                <th style="font-size: 11px;">Nome Fantasia</th>
                <th style="font-size: 11px;">Município</th>
                <th style="font-size: 11px;">Rota Geral</th>
                <th style="font-size: 11px;">Rota Aprox.</th>
                <th style="font-size: 11px;">Ações</th>
            </tr>
        `;
    } else if (activeRelatorio === "romaneio") {
        theadTable.innerHTML = `
            <tr>
                <th style="font-size: 11px;">Cód. Cliente</th>
                <th style="font-size: 11px;">Cliente</th>
                <th style="font-size: 11px;">Nome Fantasia</th>
                <th style="font-size: 11px;">Município</th>
                <th style="width: 70px; font-size: 11px;">Ordem</th>
                <th style="font-size: 11px;">Peso Líq.</th>
                <th style="font-size: 11px;">Observações</th>
                <th style="font-size: 11px;">Ações</th>
            </tr>
        `;
    } else {
        theadTable.innerHTML = `
            <tr>
                <th>Ordem</th>
                <th>Nº Pedido</th>
                <th>Cliente</th>
                <th>Cidade</th>
                <th>Peso Kg</th>
                <th>Observações</th>
                <th>Ações</th>
            </tr>
        `;
    }

    tbodyPedidos.innerHTML = `<tr><td colspan="${activeRelatorio === 'resumo' ? 6 : 9}" style="text-align:center;">Carregando pedidos...</td></tr>`;

    try {
        const resp = await fetch(`${API_BASE}/api/relatorios/cargas/${cargaEmGerenciamento}/pedidos-detalhes`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        const ped = await resp.json();

        // Round 3: Atuallizar Filial com o Fornecedor do primeiro pedido (se for Formação de Carga)
        if (activeRelatorio === "formacao" && ped.length > 0) {
            const elFilial = document.getElementById('in-header-filial');
            if (elFilial) elFilial.value = ped[0].fornecedor || "Matriz SUPRA LOG";
        }

        // Também precisamos da data da carga para exibir na coluna "Data"
        const respCarga = await fetch(`${API_BASE}/api/relatorios/cargas/${cargaEmGerenciamento}`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        const cargaInfo = await respCarga.json();
        const dispDataCarga = cargaInfo.data_carregamento ? new Date(cargaInfo.data_carregamento).toLocaleDateString('pt-BR') : "-";

        if (ped.length === 0) {
            tbodyPedidos.innerHTML = '';
            emptyPedidos.style.display = 'block';
            return;
        }

        emptyPedidos.style.display = 'none';
        let h = "";
        ped.forEach(p => {
            const peso = p.peso_total ? Math.round(p.peso_total).toString() : "0";

            if (activeRelatorio === "formacao") {
                // "tabelão" layout
                h += `
                    <tr>
                        <td style="font-size: 12px;">${numCargaAtiva || ''}</td>
                        <td style="font-size: 12px;"><strong>${p.numero_pedido}</strong></td>
                        <td style="white-space: nowrap; font-size: 12px;">${peso} kg</td>
                        <td style="font-size: 12px;">${p.codigo_cliente || '-'}</td>
                        <td style="font-size: 12px;">${p.cliente_nome || '-'}</td>
                        <td style="font-size: 12px;">${p.nome_fantasia || '-'}</td>
                        <td style="font-size: 12px;">${p.municipio || '-'}</td>
                        <td style="font-size: 12px;">${p.rota_principal || '-'}</td>
                        <td style="font-size: 12px;">${p.rota_aproximacao || '-'}</td>
                        <td style="white-space: nowrap;">
                            <button class="os-btn os-btn-sm os-btn-danger btn-remover-pedido-carga" data-id="${p.id_carga_pedido}" title="Remover">&times;</button>
                        </td>
                    </tr>
                `;
            } else if (activeRelatorio === "romaneio") {
                h += `
                    <tr>
                        <td style="font-size: 12px;">${p.codigo_cliente || '-'}</td>
                        <td style="font-size: 12px;">${p.cliente_nome || '-'}</td>
                        <td style="font-size: 12px;">${p.nome_fantasia || '-'}</td>
                        <td style="font-size: 12px;">${p.municipio || '-'}</td>
                        <td><input type="number" class="os-input os-input-sm in-ordem" value="${p.ordem_carregamento || ''}" data-id="${p.id_carga_pedido}" style="padding: 2px; font-size: 12px; height: 28px;"></td>
                        <td style="white-space: nowrap; font-size: 12px;">${peso} kg</td>
                        <td><input type="text" class="os-input os-input-sm in-obs" value="${p.observacoes || ''}" data-id="${p.id_carga_pedido}" style="padding: 2px; font-size: 12px; height: 28px;"></td>
                        <td style="white-space: nowrap;">
                            <button class="os-btn os-btn-sm os-btn-primary btn-save-item" data-id="${p.id_carga_pedido}" title="Salvar Ordem/Obs">√</button>
                            <button class="os-btn os-btn-sm os-btn-danger btn-remover-pedido-carga" data-id="${p.id_carga_pedido}" title="Remover">&times;</button>
                        </td>
                    </tr>
                `;
            } else {
                // Caso genérico ou fallbacks
                h += `
                    <tr>
                        <td style="width: 80px;"><input type="number" class="os-input os-input-sm in-ordem" value="${p.ordem_carregamento || ''}" data-id="${p.id_carga_pedido}"></td>
                        <td><strong>${p.numero_pedido}</strong></td>
                        <td>${p.cliente_nome || '-'}</td>
                        <td>${p.municipio || '-'}</td>
                        <td>${peso}</td>
                        <td><input type="text" class="os-input os-input-sm in-obs" value="${p.observacoes || ''}" data-id="${p.id_carga_pedido}"></td>
                        <td>
                            <button class="os-btn os-btn-sm os-btn-primary btn-save-item" data-id="${p.id_carga_pedido}">Salvar</button>
                            <button class="os-btn os-btn-sm os-btn-danger btn-remover-pedido-carga" data-id="${p.id_carga_pedido}">Remover</button>
                        </td>
                    </tr>
                `;
            }
        });
        tbodyPedidos.innerHTML = h;

        document.querySelectorAll('.btn-save-item').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.currentTarget.dataset.id;
                const row = e.currentTarget.closest('tr');
                const ordem = row.querySelector('.in-ordem').value;
                const obs = row.querySelector('.in-obs').value;

                const origText = btn.textContent;
                btn.textContent = "...";
                const r = await fetch(`${API_BASE}/api/relatorios/cargas/pedidos/${id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}`
                    },
                    body: JSON.stringify({ ordem_carregamento: parseInt(ordem) || null, observacoes: obs })
                });
                if (r.ok) {
                    btn.textContent = "OK";
                    setTimeout(() => { btn.textContent = origText; }, 1500);
                } else {
                    btn.textContent = "!!";
                    alert("Falha ao salvar item");
                }
            });
        });

        document.querySelectorAll('.btn-remover-pedido-carga').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if (!confirm("Remover este pedido da carga?")) return;
                const linkId = e.currentTarget.dataset.id;
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
        emptyPedidos.style.display = 'block';
    }
}

async function carregarResumoProdutosDaCargaAtiva() {
    const tbodyPedidos = document.getElementById('tbody-pedidos-carga');
    const emptyPedidos = document.getElementById('empty-carga-pedidos');
    const tableWrap = tbodyPedidos.closest('.os-table-wrap');
    const theadTable = tableWrap.querySelector('table thead');

    theadTable.innerHTML = `
        <tr>
            <th>Código</th>
            <th>Descrição</th>
            <th>Embalagem</th>
            <th style="text-align: center;">Quantidade</th>
            <th>Unidade</th>
            <th style="text-align: right;">Peso Total</th>
            <th style="text-align: right;">Peso Acum.</th>
        </tr>
    `;

    tbodyPedidos.innerHTML = '<tr><td colspan="7" style="text-align:center;">Carregando resumo de produtos...</td></tr>';

    try {
        const resp = await fetch(`${API_BASE}/api/relatorios/cargas/${cargaEmGerenciamento}/resumo-produtos`, {
            headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
        });
        const prods = await resp.json();

        if (prods.length === 0) {
            tbodyPedidos.innerHTML = '';
            emptyPedidos.textContent = "Não há produtos faturados para os pedidos desta carga.";
            emptyPedidos.style.display = 'block';
            return;
        }

        emptyPedidos.style.display = 'none';
        let h = "";
        prods.forEach(p => {
            const pesoUnit = p.peso_unitario || 0;
            const pesoRow = p.peso_liquido_total || 0;
            const pesoStr = Math.round(pesoUnit).toString();
            const acumStr = Math.round(pesoRow).toString();
            h += `
                <tr>
                    <td><strong>${p.codigo || '-'}</strong></td>
                    <td>${p.descricao}</td>
                    <td>${p.embalagem || '-'}</td>
                    <td style="text-align: center;">${p.qtd_total}</td>
                    <td>${p.unidade || 'UN'}</td>
                    <td style="text-align: right;">${pesoStr} kg</td>
                    <td style="text-align: right;">${acumStr} kg</td>
                </tr>
            `;
        });
        tbodyPedidos.innerHTML = h;
    } catch (e) {
        console.error(e);
        tbodyPedidos.innerHTML = '';
        emptyPedidos.textContent = "Erro ao carregar o resumo de produtos.";
        emptyPedidos.style.display = 'block';
    }
}

// -----------------------------------------------------
// MODAL BUSCA PEDIDOS (Simplificado)
// -----------------------------------------------------

function abrirModalBuscaPedidos() {
    const modal = document.getElementById('modal-buscar-pedido');
    modal.classList.add('active');
    document.getElementById('modal-buscar-close').onclick = () => modal.classList.remove('active');

    const tbodyRes = document.getElementById('tbody-resultado-busca');
    tbodyRes.innerHTML = '<tr><td colspan="8" style="text-align: center;">Carregando pedidos ativos...</td></tr>';

    fetch(`${API_BASE}/api/pedidos?status=CONFIRMADO,FATURADO&pageSize=300`, {
        headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
    })
        .then(r => r.json())
        .then(json => {
            const res = json.data || [];
            let html = "";
            res.forEach(p => {
                html += `
                <tr>
                    <td><input type="checkbox" class="chk-pedido-item" value="${p.numero_pedido}"></td>
                    <td><strong>${p.numero_pedido}</strong></td>
                    <td>${p.cliente_nome}</td>
                    <td>${p.municipio || '-'}</td>
                    <td>${p.status_codigo}</td>
                    <td>${Math.round(p.peso_total || 0).toString()} kg</td>
                </tr>
            `;
            });
            tbodyRes.innerHTML = html;
        });

    document.getElementById('btn-vincular-selecionados').onclick = async () => {
        const checked = document.querySelectorAll('.chk-pedido-item:checked');
        for (const chk of checked) {
            await fetch(`${API_BASE}/api/relatorios/cargas/${cargaEmGerenciamento}/pedidos`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}`
                },
                body: JSON.stringify({ numero_pedido: chk.value, ordem_carregamento: 0 })
            });
        }
        modal.classList.remove('active');
        carregarPedidosDaCargaAtiva();
    };
}

// -----------------------------------------------------
// BOTÃO EXPORTAR PDF
// -----------------------------------------------------

btnExport.addEventListener('click', () => {
    let endpoint = "";
    let cargaId = "";

    const firstChecked = document.querySelector('.chk-carga-item:checked');
    if (firstChecked) cargaId = firstChecked.value;
    else cargaId = cargaEmGerenciamento;

    if (!cargaId) {
        alert("Selecione uma carga (checkbox) ou entre em um relatório.");
        return;
    }

    if (activeRelatorio === "formacao") endpoint = `${API_BASE}/api/relatorios/carga/${cargaId}/pdf`;
    else if (activeRelatorio === "romaneio") endpoint = `${API_BASE}/api/relatorios/romaneio/${cargaId}/pdf`;
    else if (activeRelatorio === "resumo") endpoint = `${API_BASE}/api/relatorios/resumo-produtos/${cargaId}/pdf`;

    if (endpoint) {
        const token = window.Auth ? window.Auth.getToken() : '';
        window.open(`${endpoint}?token=${token}`, '_blank');
    }
});
