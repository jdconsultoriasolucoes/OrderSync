
const API_BASE = window.API_BASE || "https://ordersync-backend-edjq.onrender.com";

let currentModule = null; // 'condicoes', 'descontos', 'familias'
let currentItem = null;   // Item sendo editado (null se novo)

// Maps for configuration
const CONFIG = {
    condicoes: {
        apiPath: '/system/condicoes',
        pk: 'codigo_prazo',
        cols: [
            { key: 'codigo_prazo', label: 'Código' },
            { key: 'prazo', label: 'Prazo' },
            { key: 'descricao', label: 'Descrição' },
            { key: 'custo', label: 'Custo (%)', fmt: v => (v || 0).toFixed(2) + '%' }
        ],
        modalId: 'modal-condicoes',
        fillForm: (item) => {
            document.getElementById('cond-id').value = item.codigo_prazo;
            document.getElementById('cond-id').disabled = true; // PK locked
            document.getElementById('cond-prazo').value = item.prazo;
            document.getElementById('cond-desc').value = item.descricao;
            document.getElementById('cond-custo').value = item.custo;
        },
        clearForm: () => {
            document.getElementById('cond-id').value = '';
            document.getElementById('cond-id').disabled = false;
            document.getElementById('cond-prazo').value = '';
            document.getElementById('cond-desc').value = '';
            document.getElementById('cond-custo').value = '';
        }
    },
    descontos: {
        apiPath: '/system/descontos',
        pk: 'id_desconto',
        cols: [
            { key: 'id_desconto', label: 'ID' },
            { key: 'fator_comissao', label: 'Fator Comiss. (%)', fmt: v => (v || 0).toFixed(2) + '%' }
        ],
        modalId: 'modal-descontos',
        fillForm: (item) => {
            document.getElementById('desc-id').value = item.id_desconto;
            document.getElementById('desc-id').disabled = true;
            document.getElementById('desc-fator').value = item.fator_comissao;
        },
        clearForm: () => {
            document.getElementById('desc-id').value = '';
            document.getElementById('desc-id').disabled = false;
            document.getElementById('desc-fator').value = '';
        }
    },
    familias: {
        apiPath: '/system/familias',
        pk: 'id',
        cols: [
            { key: 'id', label: 'ID' },
            { key: 'tipo', label: 'Tipo' },
            { key: 'familia', label: 'Família' },
            { key: 'marca', label: 'Grupo' }
        ],
        modalId: 'modal-familias',
        fillForm: (item) => {
            document.getElementById('fam-id').value = item.id;
            document.getElementById('fam-tipo').value = item.tipo;
            document.getElementById('fam-nome').value = item.familia;
            document.getElementById('fam-marca').value = item.marca || '';
        },
        clearForm: () => {
            document.getElementById('fam-id').value = '';
            document.getElementById('fam-tipo').value = '';
            document.getElementById('fam-nome').value = '';
            document.getElementById('fam-marca').value = '';
        }
    },
    transporte: {
        apiPath: '/api/transporte',
        pk: 'id',
        cols: [
            { key: 'id', label: 'ID' },
            { key: 'transportadora', label: 'Empresa' },
            { key: 'motorista', label: 'Motorista' },
            { key: 'modelo', label: 'Modelo' },
            { key: 'veiculo_placa', label: 'Placa' },
            { key: 'tipo_veiculo', label: 'Tipo', fmt: v => v === 'Proprio' ? 'Próprio' : 'Terceiro' },
            { key: 'capacidade_kg', label: 'Capacidade', fmt: v => v ? (v).toLocaleString('pt-BR') + ' kg' : '-' }
        ],
        modalId: 'modal-transporte',
        fillForm: (item) => {
            document.getElementById('trans-id').value = item.id;
            document.getElementById('trans-empresa').value = item.transportadora;
            document.getElementById('trans-motorista').value = item.motorista;
            document.getElementById('trans-modelo').value = item.modelo || '';
            document.getElementById('trans-placa').value = item.veiculo_placa;
            document.getElementById('trans-tipo').value = item.tipo_veiculo || 'Proprio';
            document.getElementById('trans-capacidade').value = item.capacidade_kg || '';
        },
        clearForm: () => {
            document.getElementById('trans-id').value = '';
            document.getElementById('trans-empresa').value = '';
            document.getElementById('trans-motorista').value = '';
            document.getElementById('trans-modelo').value = '';
            document.getElementById('trans-placa').value = '';
            document.getElementById('trans-tipo').value = 'Proprio';
            document.getElementById('trans-capacidade').value = '';
        }
    },
    vendedores: {
        apiPath: '/vendedores',
        pk: 'id',
        cols: [
            { key: 'id', label: 'ID' },
            { key: 'nome', label: 'Nome' },
            { key: 'email', label: 'E-mail' }
        ],
        modalId: 'modal-vendedores',
        fillForm: (item) => {
            document.getElementById('vend-id').value = item.id;
            document.getElementById('vend-nome').value = item.nome;
            document.getElementById('vend-email').value = item.email || '';
        },
        clearForm: () => {
            document.getElementById('vend-id').value = '';
            document.getElementById('vend-nome').value = '';
            document.getElementById('vend-email').value = '';
        }
    },
    previsao_semanal: {
        apiPath: '/captacao-pedidos/previsao-semanal',
        customRender: (data, container) => {
            if (!data || !data.dados || data.dados.length === 0) {
                container.innerHTML = `<p style="padding: 16px;">Nenhuma previsão de vendas para a semana (${data?.semana_inicio || ''} a ${data?.semana_fim || ''}).</p>`;
                return;
            }
            
            let html = `<h4 style="margin: 0 0 16px 0; color: var(--os-text-secondary);">Período: ${data.semana_inicio} a ${data.semana_fim}</h4>`;
            
            data.dados.forEach(vendedorGrupo => {
                html += `<div style="margin-top: 24px; margin-bottom: 8px;">
                            <h5 style="margin: 0; color: var(--os-primary); font-size: 16px; border-bottom: 2px solid var(--os-border); padding-bottom: 8px;">
                                Vendedor: ${vendedorGrupo.vendedor} <span style="font-size: 13px; color: var(--os-text-secondary); float: right;">${vendedorGrupo.clientes.length} cliente(s)</span>
                            </h5>
                         </div>`;
                         
                html += `<table class="data-table" style="margin-bottom: 20px;">
                            <thead>
                                <tr>
                                    <th>Cód</th>
                                    <th>Cliente</th>
                                    <th>Município</th>
                                    <th>Rota</th>
                                    <th>Últ. Compra</th>
                                    <th>Previsão</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>`;
                            
                vendedorGrupo.clientes.forEach(c => {
                    let badgeColor = '#6b7280';
                    let bgColor = '#f3f4f6';
                    if (c.status_cor === 'verde') { badgeColor = '#15803d'; bgColor = '#dcfce7'; }
                    else if (c.status_cor === 'amarelo') { badgeColor = '#b45309'; bgColor = '#fef3c7'; }
                    else if (c.status_cor === 'vermelho') { badgeColor = '#b91c1c'; bgColor = '#fee2e2'; }
                    
                    const badge = `<span style="background-color: ${bgColor}; color: ${badgeColor}; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;">${c.status_cor.toUpperCase()}</span>`;
                    
                    html += `<tr>
                                <td>${c.codigo_cliente}</td>
                                <td><strong>${c.cliente}</strong><br><span style="font-size: 11px; color: #6b7280;">${c.nome_fantasia || '-'}</span></td>
                                <td>${c.municipio || '-'}</td>
                                <td><span style="font-size: 11px;">Geral: ${c.rota_geral || '-'}<br>Aprox: ${c.rota_aproximacao || '-'}</span></td>
                                <td>${c.data_ultima_compra || '-'}</td>
                                <td style="color: var(--os-primary); font-weight: 600;">${c.data_previsao_proxima || '-'}</td>
                                <td>${badge}</td>
                             </tr>`;
                });
                html += `</tbody></table>`;
            });
            container.innerHTML = html;
        }
    },
    automacao: {
        apiPath: '/admin/automacao/config',
        customRender: (data, container) => {
            let html = `
                <div class="card" style="max-width: 600px; margin: 20px auto; border: 1px solid var(--os-border); box-shadow: var(--os-shadow);">
                    <div style="padding: var(--os-space-3); border-bottom: 1px solid var(--os-border);">
                        <h3 style="margin:0; font-size:18px; color:var(--os-text);">Agendamento: Relatório de Prospecção</h3>
                        <p style="margin:5px 0 0 0; font-size:13px; color:var(--os-text-secondary);">Configure o envio automático do PDF de prospecção para os vendedores toda semana.</p>
                    </div>
                    <div style="padding: var(--os-space-3);">
                        <form id="form-automacao" onsubmit="saveAutomacao(event)">
                            <div style="margin-bottom: 20px;">
                                <label style="display:flex; align-items:center; gap:8px; font-weight:600; cursor:pointer;">
                                    <input type="checkbox" id="auto-ativa" style="width:18px; height:18px;" ${data.prospeccao_ativa ? 'checked' : ''} />
                                    Habilitar Envio Automático
                                </label>
                            </div>

                            <div style="display: flex; gap: 16px; margin-bottom: 20px;">
                                <div style="flex:1;">
                                    <label style="display:block; margin-bottom:6px; font-weight:600; font-size:13px;">Dia da Semana</label>
                                    <select id="auto-dia" required style="width:100%; padding:10px; border:1px solid var(--os-border); border-radius:4px; font-family:var(--os-font);">
                                        <option value="0" ${data.prospeccao_dia_semana === 0 ? 'selected' : ''}>Segunda-feira</option>
                                        <option value="1" ${data.prospeccao_dia_semana === 1 ? 'selected' : ''}>Terça-feira</option>
                                        <option value="2" ${data.prospeccao_dia_semana === 2 ? 'selected' : ''}>Quarta-feira</option>
                                        <option value="3" ${data.prospeccao_dia_semana === 3 ? 'selected' : ''}>Quinta-feira</option>
                                        <option value="4" ${data.prospeccao_dia_semana === 4 ? 'selected' : ''}>Sexta-feira</option>
                                        <option value="5" ${data.prospeccao_dia_semana === 5 ? 'selected' : ''}>Sábado</option>
                                        <option value="6" ${data.prospeccao_dia_semana === 6 ? 'selected' : ''}>Domingo</option>
                                    </select>
                                </div>
                                <div style="flex:1;">
                                    <label style="display:block; margin-bottom:6px; font-weight:600; font-size:13px;">Horário de Envio</label>
                                    <input type="time" id="auto-hora" required step="60" value="${data.prospeccao_horario ? data.prospeccao_horario.substring(0, 5) : '08:00'}" style="width:100%; padding:10px; border:1px solid var(--os-border); border-radius:4px; font-family:var(--os-font);" />
                                </div>
                            </div>

                            <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top:20px; padding-top:20px; border-top:1px solid var(--os-border);">
                                <button type="button" class="btn" onclick="testarAutomacaoAgora()">Disparar Agora (Teste)</button>
                                <button type="submit" class="btn btn-primary">Salvar Configuração</button>
                            </div>
                        </form>
                    </div>
                </div>
            `;
            container.innerHTML = html;
        }
    }
};

function selectModule(mod) {
    currentModule = mod;

    // Highlight menu button via JS if it's called programmatically without a click event
    document.querySelectorAll('.module-nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('onclick')?.includes(mod)) {
            btn.classList.add('active');
        }
    });

    // Set Header
    const titles = {
        condicoes: 'Condições de Pagamento',
        descontos: 'Descontos',
        familias: 'Grupo de Produtos',
        transporte: 'Transporte / Logística',
        vendedores: 'Vendedores',
        previsao_semanal: 'Previsão de Vendas Semanal',
        automacao: 'Automação de Relatórios'
    };

    const sectionTitle = document.getElementById('sectionTitle');
    if (sectionTitle) sectionTitle.textContent = titles[mod];

    const btnNovo = document.getElementById('btn-novo');
    if (btnNovo) {
        if (mod === 'previsao_semanal' || mod === 'automacao') {
            btnNovo.style.display = 'none';
        } else {
            btnNovo.style.display = 'inline-block';
            btnNovo.disabled = false;
        }
    }

    loadData();
}

async function loadData() {
    const cfg = CONFIG[currentModule];
    const container = document.getElementById('grid');
    container.innerHTML = '<p>Carregando...</p>';

    try {
        const token = localStorage.getItem("ordersync_token");
        const res = await fetch(`${API_BASE}${cfg.apiPath}`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Erro ao buscar dados");
        const data = await res.json();

        if (cfg.customRender) {
            cfg.customRender(data, container);
        } else {
            renderGrid(data);
        }
    } catch (e) {
        container.innerHTML = `<p style="color:red">Erro: ${e.message}</p>`;
    }
}

function renderGrid(rows) {
    const cfg = CONFIG[currentModule];
    const container = document.getElementById('grid');

    if (!rows || rows.length === 0) {
        container.innerHTML = '<p>Nenhum registro encontrado.</p>';
        return;
    }

    let html = '<table class="data-table"><thead><tr>';
    cfg.cols.forEach(c => html += `<th>${c.label}</th>`);
    html += '<th>Ações</th></tr></thead><tbody>';

    rows.forEach(r => {
        html += '<tr>';
        cfg.cols.forEach(c => {
            let val = r[c.key];
            if (c.fmt) val = c.fmt(val);
            html += `<td>${val != null ? val : ''}</td>`;
        });

        // Actions
        // Need to serialize item properly for passing to edit
        // Storing in data attr is easier or finding by ID from global list
        // Let's attach onclick with ID
        const pkVal = r[cfg.pk];
        html += `
            <td>
                <button class="os-btn os-btn-secondary os-btn-sm" style="margin-right: 4px;" onclick="editItem('${pkVal}')">Editar</button>
                <button class="os-btn os-btn-sm" style="background-color: var(--os-error-light); color: var(--os-error); border-color: #FECACA;" onclick="deleteItem('${pkVal}')">Excluir</button>
            </td>
        </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;

    // Store data globally to lookup for edit
    window._currentData = rows;
}

function openModal(pkVal = null) {
    const cfg = CONFIG[currentModule];
    const modal = document.getElementById(cfg.modalId);

    if (pkVal) {
        // Edit
        const item = window._currentData.find(r => String(r[cfg.pk]) === String(pkVal));
        if (!item) return;
        currentItem = item;
        cfg.fillForm(item);
    } else {
        // New
        currentItem = null;
        cfg.clearForm();
    }

    modal.style.display = 'flex';
}

function closeModals() {
    document.querySelectorAll('.custom-modal').forEach(m => m.style.display = 'none');
}

// --- Save Handlers ---

async function saveGeneric(payload, isUpdate, urlSuffix = '') {
    const cfg = CONFIG[currentModule];
    const token = localStorage.getItem("ordersync_token");
    const url = `${API_BASE}${cfg.apiPath}${isUpdate ? '/' + urlSuffix : ''}`;
    const method = isUpdate ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method,
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const txt = await res.text();
            throw new Error(txt);
        }

        alert("Salvo com sucesso!");
        closeModals();
        loadData();
    } catch (e) {
        alert("Erro ao salvar: " + e.message);
    }
}

async function saveCondicao(e) {
    e.preventDefault();
    const id = document.getElementById('cond-id').value;
    const prazo = document.getElementById('cond-prazo').value;
    const desc = document.getElementById('cond-desc').value;
    const custo = document.getElementById('cond-custo').value;

    if (!id) {
        alert("Obrigatório informar o código.");
        return;
    }

    const payload = {
        codigo_prazo: parseInt(id),
        prazo,
        descricao: desc,
        custo: parseFloat(custo)
    };

    const isUpdate = !!currentItem;
    if (isUpdate) {
        // payload can't change ID in body if used in URL usually, but backend schema has codigo_prazo in Create. 
        // Update schema doesn't have ID. 
        // Pydantic `CondicaoPagamentoUpdate` doesn't have ID. OK.
        delete payload.codigo_prazo;
    }

    await saveGeneric(payload, isUpdate, id);
}

async function saveDesconto(e) {
    e.preventDefault();
    const id = document.getElementById('desc-id').value;
    const fator = document.getElementById('desc-fator').value;

    if (!id) {
        alert("Obrigatório informar o ID.");
        return;
    }

    const payload = {
        id_desconto: parseInt(id),
        fator_comissao: parseFloat(fator)
    };

    const isUpdate = !!currentItem;
    if (isUpdate) delete payload.id_desconto;

    await saveGeneric(payload, isUpdate, id);
}

async function saveFamilia(e) {
    e.preventDefault();
    // ID is auto/hidden for new, present for edit
    const id = document.getElementById('fam-id').value;
    const tipo = document.getElementById('fam-tipo').value;
    const familia = document.getElementById('fam-nome').value;
    const marca = document.getElementById('fam-marca').value;

    // Create schema: tipo, familia, marca (id ignored/auto-gen in backend logic I wrote? 
    // Wait, backend logic for families: 
    // `new_id = max_id + 1`. So frontend doesn't send ID for create.

    const payload = {
        tipo,
        familia,
        marca: marca || null
    };

    const isUpdate = !!currentItem;

    await saveGeneric(payload, isUpdate, id);
}

async function saveTransporte(e) {
    e.preventDefault();
    const id = document.getElementById('trans-id').value;
    const empresa = document.getElementById('trans-empresa').value;
    const motorista = document.getElementById('trans-motorista').value;
    const placa = document.getElementById('trans-placa').value;
    const cap = document.getElementById('trans-capacidade').value;

    const payload = {
        transportadora: empresa,
        motorista: motorista,
        modelo: document.getElementById('trans-modelo').value || null,
        veiculo_placa: placa,
        tipo_veiculo: document.getElementById('trans-tipo').value,
        capacidade_kg: cap ? parseInt(cap) : null
    };

    const isUpdate = !!currentItem;
    await saveGeneric(payload, isUpdate, id);
}

async function saveVendedor(e) {
    e.preventDefault();
    const id = document.getElementById('vend-id').value;
    const nome = document.getElementById('vend-nome').value;
    const email = document.getElementById('vend-email').value;

    const payload = {
        nome: nome,
        email: email || null
    };

    const isUpdate = !!currentItem;
    await saveGeneric(payload, isUpdate, id);
}

async function saveAutomacao(e) {
    e.preventDefault();
    const ativa = document.getElementById('auto-ativa').checked;
    const dia = parseInt(document.getElementById('auto-dia').value);
    let hora = document.getElementById('auto-hora').value;
    if (hora.length === 5) hora += ":00"; // format HH:MM:SS

    const payload = {
        prospeccao_ativa: ativa,
        prospeccao_dia_semana: dia,
        prospeccao_horario: hora
    };

    const token = localStorage.getItem("ordersync_token");
    try {
        const res = await fetch(`${API_BASE}/admin/automacao/config`, {
            method: 'PUT',
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error(await res.text());
        alert("Configuração salva com sucesso!");
        loadData();
    } catch (err) {
        alert("Erro ao salvar configuração: " + err.message);
    }
}

async function testarAutomacaoAgora() {
    if (!confirm("Isso irá disparar os e-mails com PDFs imediatamente para os vendedores ativos. Tem certeza?")) return;
    
    const token = localStorage.getItem("ordersync_token");
    try {
        const res = await fetch(`${API_BASE}/admin/automacao/testar-prospeccao`, {
            method: 'POST',
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error(await res.text());
        alert("Rotina disparada com sucesso! Os e-mails serão enviados em plano de fundo.");
    } catch (err) {
        alert("Erro ao disparar teste: " + err.message);
    }
}

// --- Delete Handler ---
async function deleteItem(pkVal) {
    if (!confirm("Tem certeza que deseja remover (inativar) este item?")) return;

    const cfg = CONFIG[currentModule];
    const token = localStorage.getItem("ordersync_token");

    try {
        const res = await fetch(`${API_BASE}${cfg.apiPath}/${pkVal}`, {
            method: 'DELETE',
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error(await res.text());
        loadData();
    } catch (e) {
        alert("Erro ao remover: " + e.message);
    }
}

// Global hook for edit
window.editItem = function (pk) {
    openModal(pk);
};
window.deleteItem = deleteItem;


