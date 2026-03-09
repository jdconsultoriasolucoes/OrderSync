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
        const resp = await fetch(\`\${API_BASE}/api/relatorios/cargas\`, { 
            headers: { "Authorization": \`Bearer \${window.Auth ? window.Auth.getToken() : ''}\` } 
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
            html += \`
                <tr>
                    <td style="text-align: center;"><input type="checkbox" class="chk-carga-item" value="\${c.id}"></td>
                    <td><strong>\${c.numero_carga}</strong></td>
                    <td>\${c.nome_carga || '-'}</td>
                    <td>\${dispData}</td>
                    <td>
                       <button class="os-btn os-btn-sm os-btn-secondary btn-gerenciar-carga" data-id="\${c.id}" data-nome="\${c.numero_carga}">Gerenciar / Ver \${tipo}</button>
                       \${activeRelatorio === 'formacao' ? \`<button class="os-btn os-btn-sm os-btn-danger btn-excluir-carga" data-id="\${c.id}">Excluir</button>\` : ''}
                    </td>
                </tr>
            \`;
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
                    await fetch(\`\${API_BASE}/api/relatorios/cargas/\${id}\`, {
                        method: "DELETE",
                        headers: { "Authorization": \`Bearer \${window.Auth ? window.Auth.getToken() : ''}\` }
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

        const nwResp = await fetch(\`\${API_BASE}/api/relatorios/cargas\`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": \`Bearer \${window.Auth ? window.Auth.getToken() : ''}\`
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

let cargaEmGerenciamento = null;

async function abrirGerenciadorDeCarga(idCarga, numCarga) {
    cargaEmGerenciamento = idCarga;
    document.getElementById('painel-listagem').style.display = 'none';
    document.getElementById('painel-gerenciar-carga').style.display = 'block';
    document.getElementById('titulo-carga-ativa').textContent = "Gerenciando Carga: " + numCarga;

    document.getElementById('btn-voltar-listagem').onclick = () => renderRelatorioView(activeRelatorio);
    document.getElementById('btn-buscar-pedidos').onclick = () => abrirModalBuscaPedidos();

    await carregarPedidosDaCargaAtiva();
}

async function carregarPedidosDaCargaAtiva() {
    const tbodyPedidos = document.getElementById('tbody-pedidos-carga');
    const emptyPedidos = document.getElementById('empty-carga-pedidos');
    const theadTable = tbodyPedidos.closest('table').querySelector('thead');

    theadTable.innerHTML = \`
        <tr>
            <th>Ordem</th>
            <th>Nº Pedido</th>
            <th>Cliente</th>
            <th>Cidade</th>
            <th>Peso Kg</th>
            <th>Observações</th>
            <th>Ações</th>
        </tr>
    \`;

    tbodyPedidos.innerHTML = '<tr><td colspan="7" style="text-align:center;">Carregando...</td></tr>';

    try {
        const resp = await fetch(\`\${API_BASE}/api/relatorios/cargas/\${cargaEmGerenciamento}/pedidos-detalhes\`, {
            headers: { "Authorization": \`Bearer \${window.Auth ? window.Auth.getToken() : ''}\` }
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
            h += \`
                <tr>
                    <td style="width: 80px;"><input type="number" class="os-input os-input-sm in-ordem" value="\${p.ordem_carregamento || ''}" data-id="\${p.id_carga_pedido}" style="padding: 4px;"></td>
                    <td><strong>\${p.numero_pedido}</strong></td>
                    <td>\${p.cliente_nome || '-'}</td>
                    <td>\${p.municipio || '-'}</td>
                    <td>\${peso}</td>
                    <td><input type="text" class="os-input os-input-sm in-obs" value="\${p.observacoes || ''}" data-id="\${p.id_carga_pedido}" style="padding: 4px;"></td>
                    <td>
                        <button class="os-btn os-btn-sm os-btn-primary btn-save-item" data-id="\${p.id_carga_pedido}">Salvar</button>
                        <button class="os-btn os-btn-sm os-btn-danger btn-remover-pedido-carga" data-id="\${p.id_carga_pedido}">Remover</button>
                    </td>
                </tr>
            \`;
        });
        tbodyPedidos.innerHTML = h;

        document.querySelectorAll('.btn-save-item').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.target.dataset.id;
                const row = e.target.closest('tr');
                const ordem = row.querySelector('.in-ordem').value;
                const obs = row.querySelector('.in-obs').value;

                btn.textContent = "...";
                const r = await fetch(\`\${API_BASE}/api/relatorios/cargas/pedidos/\${id}\`, {
                    method: 'PUT',
                    headers: { 
                        'Content-Type': 'application/json',
                        "Authorization": \`Bearer \${window.Auth ? window.Auth.getToken() : ''}\` 
                    },
                    body: JSON.stringify({ ordem_carregamento: parseInt(ordem) || null, observacoes: obs })
                });
                if (r.ok) btn.textContent = "OK!";
                else { btn.textContent = "Erro"; alert("Falha ao salvar item"); }
            });
        });

        document.querySelectorAll('.btn-remover-pedido-carga').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if (!confirm("Remover este pedido da carga?")) return;
                const linkId = e.target.dataset.id;
                await fetch(\`\${API_BASE}/api/relatorios/cargas/pedidos/\${linkId}\`, {
                    method: 'DELETE',
                    headers: { "Authorization": \`Bearer \${window.Auth ? window.Auth.getToken() : ''}\` }
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

// -----------------------------------------------------
// MODAL BUSCA PEDIDOS (Simplificado)
// -----------------------------------------------------

function abrirModalBuscaPedidos() {
    const modal = document.getElementById('modal-buscar-pedido');
    modal.classList.add('active');
    document.getElementById('modal-buscar-close').onclick = () => modal.classList.remove('active');

    const tbodyRes = document.getElementById('tbody-resultado-busca');
    tbodyRes.innerHTML = '<tr><td colspan="8" style="text-align: center;">Carregando pedidos ativos...</td></tr>';

    fetch(\`\${API_BASE}/api/pedidos?status=CONFIRMADO,FATURADO&pageSize=300\`, { 
        headers: { "Authorization": \`Bearer \${window.Auth ? window.Auth.getToken() : ''}\` } 
    })
    .then(r => r.json())
    .then(json => {
        const res = json.data || [];
        let html = "";
        res.forEach(p => {
            html += \`
                <tr>
                    <td><input type="checkbox" class="chk-pedido-item" value="\${p.numero_pedido}"></td>
                    <td><strong>\${p.numero_pedido}</strong></td>
                    <td>\${p.cliente_nome}</td>
                    <td>\${p.municipio || '-'}</td>
                    <td>\${p.status_codigo}</td>
                    <td>\${(p.peso_total || 0).toFixed(2)} kg</td>
                </tr>
            \`;
        });
        tbodyRes.innerHTML = html;
    });

    document.getElementById('btn-vincular-selecionados').onclick = async () => {
        const checked = document.querySelectorAll('.chk-pedido-item:checked');
        for (const chk of checked) {
            await fetch(\`\${API_BASE}/api/relatorios/cargas/\${cargaEmGerenciamento}/pedidos\`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": \`Bearer \${window.Auth ? window.Auth.getToken() : ''}\`
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

    if (activeRelatorio === "formacao") endpoint = \`\${API_BASE}/api/relatorios/carga/\${cargaId}/pdf\`;
    else if (activeRelatorio === "romaneio") endpoint = \`\${API_BASE}/api/relatorios/romaneio/\${cargaId}/pdf\`;
    else if (activeRelatorio === "resumo") endpoint = \`\${API_BASE}/api/relatorios/resumo-produtos/\${cargaId}/pdf\`;

    if (endpoint) {
        const token = window.Auth ? window.Auth.getToken() : '';
        window.open(\`\${endpoint}?token=\${token}\`, '_blank');
    }
});
