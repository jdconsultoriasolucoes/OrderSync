/**
 * relatorios.js
 * Gerencia a lógica da visualização de 2 colunas do Módulo "Exportar Relatórios"
 */

var API_BASE = window.API_BASE || window.location.origin;

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
let cargaEmGerenciamento = null;
let numCargaAtiva = null;

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
    cargaEmGerenciamento = null;
    numCargaAtiva = null;
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
            }),
            fetch(`${API_BASE}/api/pedidos/status`, {
                headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
            })
        ]);

        const carga = await respCarga.json();
        const transportes = await respTransp.json();
        
        const statusRaw = await respStatus.json();
        window.relatoriosStatusList = Array.isArray(statusRaw) ? statusRaw : (statusRaw.data || statusRaw.items || []);

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
                        <input type="date" id="in-header-data" class="os-input os-input-sm" value="${dataCarregamentoVal}" min="${new Date().toISOString().split('T')[0]}" ${activeRelatorio === 'resumo' ? 'disabled' : ''}>
                    </div>
                    <div class="ch-field" style="flex: 1;">
                        <label>Transporte (Transportadora / Motorista / Modelo / Placa)</label>
                        <select id="sel-header-transporte" class="os-input os-input-sm" ${activeRelatorio === 'resumo' ? 'disabled' : ''}>
                            ${transpOptions}
                        </select>
                    </div>
                    <div class="ch-actions">
                        <button class="os-btn os-btn-primary os-btn-sm" id="btn-save-carga-header">Salvar Tela</button>
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

                // Save items sequentially/parallel
                const promises = [];
                document.querySelectorAll('#tbody-pedidos-carga tr').forEach(row => {
                    const id = row.querySelector('.in-ordem')?.dataset?.id;
                    const statusSel = row.querySelector('.in-status');
                    
                    if (statusSel && statusSel.value && statusSel.value !== String(statusSel.dataset.original)) {
                         const numPedido = statusSel.dataset.numeroPedido;
                         promises.push(fetch(`${API_BASE}/api/pedidos/${numPedido}/status`, {
                             method: 'POST',
                             headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` },
                             body: JSON.stringify({ para: statusSel.value, motivo: "Alteração via Gerenciamento de Carga", user_id: "sistema" })
                         }));
                    }

                    if (id) {
                        const ordem = row.querySelector('.in-ordem') ? row.querySelector('.in-ordem').value : null;
                        const obs = row.querySelector('.in-obs') ? row.querySelector('.in-obs').value : null;
                        promises.push(fetch(`${API_BASE}/api/relatorios/cargas/pedidos/${id}`, {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json',
                                "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}`
                            },
                            body: JSON.stringify({ ordem_carregamento: parseInt(ordem) || null, observacoes: obs })
                        }));
                    }
                });

                if (promises.length > 0) {
                    await Promise.allSettled(promises);
                }

                if (updateResp.ok) {
                    btn.textContent = "Salvo!";
                    setTimeout(() => { btn.textContent = "Salvar Tela"; }, 2000);
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
    const tableEl = tableWrap.querySelector('table');

    // Cabeçalho dinâmico baseado no tipo de relatório
    if (activeRelatorio === "formacao") {
        tableEl.style.tableLayout = "fixed";
        tableEl.style.width = "100%";
        theadTable.innerHTML = `
            <tr>
                <th style="font-size: 11px; width: 40px; padding: 12px 4px;">Carga</th>
                <th style="font-size: 11px; width: 50px; padding: 12px 4px;">Pedido</th>
                <th style="font-size: 11px; width: 60px; padding: 12px 4px;">Peso Líq.</th>
                <th style="font-size: 11px; width: 120px; padding: 12px 4px;">
                    Status<br>
                    <select id="sel-mass-status" class="os-input os-input-sm" style="font-size: 9px; padding: 2px; height: 22px; margin-top: 4px;">
                        <option value="">Alterar Todos...</option>
                    </select>
                </th>
                <th style="font-size: 11px; width: 50px; padding: 12px 4px;">Cód.</th>
                <th style="font-size: 11px; width: auto; min-width: 180px;">Cliente</th>
                <th style="font-size: 11px; width: 25%; min-width: 120px;">Nome Fantasia</th>
                <th style="font-size: 11px; width: 80px; padding: 12px 4px;">Município</th>
                <th style="font-size: 11px; width: 50px; padding: 12px 4px;">Rota G.</th>
                <th style="font-size: 11px; width: 50px; padding: 12px 4px;">Rota A.</th>
                <th style="font-size: 11px; width: 30px; text-align: center; padding: 12px 4px;">&nbsp;</th>
            </tr>
        `;
    } else if (activeRelatorio === "romaneio") {
        tableEl.style.tableLayout = "auto";
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

            let statusOptionsHtml = "";
            (window.relatoriosStatusList || []).forEach(s => {
                 const codigo = s.codigo || s.code || s.id || s;
                 const rotulo = s.rotulo || s.label || s.nome || codigo;
                 const selected = (String(codigo) === String(p.status_codigo) || String(rotulo) === String(p.status_codigo)) ? 'selected' : '';
                 statusOptionsHtml += `<option value="${codigo}" ${selected}>${rotulo}</option>`;
            });

            if (activeRelatorio === "formacao") {
                // "tabelão" layout
                h += `
                    <tr>
                        <td style="font-size: 12px; padding: 12px 4px;">${numCargaAtiva || ''}</td>
                        <td style="font-size: 12px; padding: 12px 4px;"><strong>${p.numero_pedido}</strong></td>
                        <td style="white-space: nowrap; font-size: 12px; padding: 12px 4px;">${peso} kg</td>
                        <td style="padding: 12px 4px;">
                            <select class="os-input os-input-sm in-status" data-numero-pedido="${p.numero_pedido}" data-original="${p.status_codigo}" style="font-size: 10px; padding: 4px; height: 26px; width: 100%;">
                                ${statusOptionsHtml}
                            </select>
                        </td>
                        <td style="font-size: 12px; padding: 12px 4px;">${p.codigo_cliente || '-'}</td>
                        <td style="font-size: 12px; width: auto; min-width: 250px; white-space: normal;">${p.cliente_nome || '-'}</td>
                        <td style="font-size: 12px; width: 25%; min-width: 150px; white-space: normal;">${p.nome_fantasia || '-'}</td>
                        <td style="font-size: 12px; padding: 12px 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100px;" title="${p.municipio || '-'}">${p.municipio || '-'}</td>
                        <td style="font-size: 12px; padding: 12px 4px;">${p.rota_principal || '-'}</td>
                        <td style="font-size: 12px; padding: 12px 4px;">${p.rota_aproximacao || '-'}</td>
                        <td style="white-space: nowrap; padding: 12px 4px; text-align: center;">
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
                        <td style="vertical-align: top;"><input type="number" class="os-input os-input-sm in-ordem" value="${p.ordem_carregamento || ''}" data-id="${p.id_carga_pedido}" style="padding: 2px; font-size: 12px; height: 32px; text-align: right; width: 60px;"></td>
                        <td style="white-space: nowrap; font-size: 12px; vertical-align: top;">${peso} kg</td>
                        <td style="vertical-align: top;"><textarea class="os-input os-input-sm in-obs" data-id="${p.id_carga_pedido}" style="padding: 4px; font-size: 12px; height: 38px; resize: vertical; width: 100%; min-width: 200px;">${p.observacoes || ''}</textarea></td>
                        <td style="white-space: nowrap; vertical-align: top;">
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

        // No row save listeners anymore.

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

        const selMassStatus = document.getElementById('sel-mass-status');
        if (selMassStatus) {
            let opts = '<option value="">Massa...</option>';
            (window.relatoriosStatusList || []).forEach(s => {
                 const codigo = s.codigo || s.code || s.id || s;
                 const rotulo = s.rotulo || s.label || s.nome || codigo;
                 opts += `<option value="${codigo}">${rotulo}</option>`;
            });
            selMassStatus.innerHTML = opts;

            selMassStatus.addEventListener('change', (e) => {
                const val = e.target.value;
                if (!val) return;
                document.querySelectorAll('.in-status').forEach(sel => {
                    sel.value = val;
                });
            });
        }
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
        
        if (!resp.ok) {
            throw new Error(`Erro do servidor: ${resp.status}`);
        }
        
        const prods = await resp.json();

        if (!Array.isArray(prods) || prods.length === 0) {
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

    // Inicializa datas
    const dtIniEl = document.getElementById('input-busca-pedido-data-ini');
    const dtFimEl = document.getElementById('input-busca-pedido-data-fim');
    if (dtIniEl && dtFimEl && !dtIniEl.value) {
        const hoje = new Date();
        const inicio = new Date();
        inicio.setDate(hoje.getDate() - 30);
        dtIniEl.value = inicio.toISOString().slice(0, 10);
        dtFimEl.value = hoje.toISOString().slice(0, 10);
    }

    const btnAtualizar = document.getElementById('btn-atualizar-busca-pedidos');
    if (btnAtualizar) btnAtualizar.style.display = 'none';

    // Auto-search on typing
    const txtBox = document.getElementById('input-busca-pedido-livre');
    if (txtBox) {
        txtBox.removeEventListener('input', carregarPedidosParaModal);
        txtBox.addEventListener('input', () => {
            clearTimeout(txtBox.searchTimeout);
            txtBox.searchTimeout = setTimeout(() => carregarPedidosParaModal(), 400);
        });
    }

    // Auto-search on date changes
    if (dtIniEl) {
        dtIniEl.removeEventListener('change', carregarPedidosParaModal);
        dtIniEl.addEventListener('change', carregarPedidosParaModal);
    }
    if (dtFimEl) {
        dtFimEl.removeEventListener('change', carregarPedidosParaModal);
        dtFimEl.addEventListener('change', carregarPedidosParaModal);
    }

    // Clear Filters Button Action
    const btnLimpar = document.getElementById('btn-limpar-busca-pedidos');
    if (btnLimpar) {
        btnLimpar.addEventListener('click', () => {
             const dtIniEl = document.getElementById('input-busca-pedido-data-ini');
             const dtFimEl = document.getElementById('input-busca-pedido-data-fim');
             const txtBox = document.getElementById('input-busca-pedido-livre');

             if (dtIniEl && dtFimEl) {
                 const hoje = new Date();
                 const inicio = new Date();
                 inicio.setDate(hoje.getDate() - 30);
                 dtIniEl.value = inicio.toISOString().slice(0, 10);
                 dtFimEl.value = hoje.toISOString().slice(0, 10);
             }
             if (txtBox) txtBox.value = "";
             carregarPedidosParaModal();
        });
    }

    carregarPedidosParaModal();

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

function carregarPedidosParaModal() {
    const tbodyRes = document.getElementById('tbody-resultado-busca');
    tbodyRes.innerHTML = '<tr><td colspan="7" style="text-align: center;">Carregando pedidos ativos...</td></tr>';

    const dtIniEl = document.getElementById('input-busca-pedido-data-ini');
    const dtFimEl = document.getElementById('input-busca-pedido-data-fim');
    const txtBox = document.getElementById('input-busca-pedido-livre');

    const dtIni = dtIniEl ? dtIniEl.value : null;
    const dtFim = dtFimEl ? dtFimEl.value : null;
    const txt = txtBox ? txtBox.value.trim() : "";

    let url = `${API_BASE}/api/pedidos?exclude_status=FATURADO,CANCELADO&pageSize=100`;
    if (dtIni) url += `&from=${dtIni}`;
    if (dtFim) url += `&to=${dtFim}`;
    if (txt) url += `&cliente=${encodeURIComponent(txt)}`;

    fetch(url, {
        headers: { "Authorization": `Bearer ${window.Auth ? window.Auth.getToken() : ''}` }
    })
        .then(r => r.json())
        .then(json => {
            const res = json.data || [];
            let html = "";
            res.forEach(p => {
                const modalidade = p.modalidade || (p.usar_valor_com_frete === false ? "RETIRADA" : "ENTREGA");
                html += `
                <tr>
                    <td><input type="checkbox" class="chk-pedido-item" value="${p.numero_pedido}"></td>
                    <td><strong>${p.numero_pedido}</strong></td>
                    <td>${p.cliente_nome}</td>
                    <td><span class="badge-alert" style="color:#374151; background:#e5e7eb; border-color:#d1d5db;">${modalidade}</span></td>
                    <td>${p.municipio || '-'}</td>
                    <td>${p.status_codigo}</td>
                    <td>${Math.round(p.peso_total || 0).toString()} kg</td>
                </tr>
            `;
            });
            tbodyRes.innerHTML = html;
        });
}

// -----------------------------------------------------
// BOTÃO EXPORTAR PDF
// -----------------------------------------------------

btnExport.addEventListener('click', () => {
    let endpoint = "";
    let cargaId = "";

    const isListagem = document.getElementById('painel-listagem').style.display !== 'none';

    if (isListagem) {
        const firstChecked = document.querySelector('.chk-carga-item:checked');
        if (!firstChecked) {
            alert("Você precisa selecionar uma carga (marcar o checkbox) para exportar.");
            return;
        }
        cargaId = firstChecked.value;
    } else {
        if (!cargaEmGerenciamento) {
            alert("Selecione uma carga ou entre em um relatório.");
            return;
        }
        cargaId = cargaEmGerenciamento;
    }

    if (activeRelatorio === "formacao") endpoint = `${API_BASE}/api/relatorios/carga/${cargaId}/pdf`;
    else if (activeRelatorio === "romaneio") endpoint = `${API_BASE}/api/relatorios/romaneio/${cargaId}/pdf`;
    else if (activeRelatorio === "resumo") endpoint = `${API_BASE}/api/relatorios/resumo-produtos/${cargaId}/pdf`;

    if (endpoint) {
        const token = window.Auth ? window.Auth.getToken() : '';
        window.open(`${endpoint}?token=${token}`, '_blank');
    }
});
