
const API_BASE = window.API_BASE || "https://ordersync-backend-59d2.onrender.com";

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
            { key: 'marca', label: 'Marca' }
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
    }
};

function selectModule(mod) {
    currentModule = mod;

    // Highlight sidebar
    document.querySelectorAll('.mgmt-sidebar button').forEach(b => b.classList.remove('active'));
    document.getElementById(`nav-${mod}`).classList.add('active');

    // Set Header
    const titles = { condicoes: 'Condições de Pagamento', descontos: 'Descontos', familias: 'Famílias de Produtos' };
    document.getElementById('module-title').textContent = titles[mod];
    document.getElementById('btn-novo').disabled = false;

    loadData();
}

async function loadData() {
    const cfg = CONFIG[currentModule];
    const container = document.getElementById('table-container');
    container.innerHTML = '<p>Carregando...</p>';

    try {
        const token = localStorage.getItem("ordersync_token");
        const res = await fetch(`${API_BASE}${cfg.apiPath}`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Erro ao buscar dados");
        const data = await res.json();

        renderGrid(data);
    } catch (e) {
        container.innerHTML = `<p style="color:red">Erro: ${e.message}</p>`;
    }
}

function renderGrid(rows) {
    const cfg = CONFIG[currentModule];
    const container = document.getElementById('table-container');

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
                <button class="action-btn btn-edit" onclick="editItem('${pkVal}')">&#9998;</button>
                <button class="action-btn btn-delete" onclick="deleteItem('${pkVal}')">&#128465;</button>
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

    modal.style.display = 'block';
}

function closeModals() {
    document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
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

