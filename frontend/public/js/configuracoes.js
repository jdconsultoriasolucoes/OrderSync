const MODULOS_SISTEMA = [
    { id: 'usuarios_e_perfis', nome: 'Usuários e Perfis' },
    { id: 'pedidos', nome: 'Pedidos' },
    { id: 'calendario', nome: 'Calendário' },
    { id: 'produtos', nome: 'Produtos' },
    { id: 'clientes', nome: 'Clientes' },
    { id: 'tabelas', nome: 'Tabelas de Preço' },
    { id: 'relatorios', nome: 'Relatórios' },
    { id: 'config_email', nome: 'Configurações de E-mail' }
];

document.addEventListener("DOMContentLoaded", () => {
    // 1. Tab Switching Logic
    const navBtns = document.querySelectorAll('.config-nav-btn');
    const views = document.querySelectorAll('.config-view');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active from all
            navBtns.forEach(b => b.classList.remove('active'));
            views.forEach(v => v.classList.remove('active'));

            // Add active to clicked
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // 2. Perfis de Acesso Logic
    carregarPerfis();

    // Form de Novo/Editar Perfil
    document.getElementById("form-perfil").addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const id = document.getElementById("perfil-id").value;
        const nome = document.getElementById("perfil-nome").value;
        const descricao = document.getElementById("perfil-descricao").value;
        
        // Coletar permissões da tabela
        const permissoes = [];
        MODULOS_SISTEMA.forEach(mod => {
            permissoes.push({
                modulo: mod.id,
                pode_visualizar: document.getElementById(`perm_${mod.id}_vis`).checked,
                pode_criar: document.getElementById(`perm_${mod.id}_cri`).checked,
                pode_editar: document.getElementById(`perm_${mod.id}_edi`).checked,
                pode_excluir: document.getElementById(`perm_${mod.id}_exc`).checked
            });
        });

        const payload = { nome, descricao, permissoes };
        const isEdit = !!id;
        
        try {
            let url = `${API_URL}/api/perfis/`;
            let method = "POST";
            if (isEdit) {
                url += id;
                method = "PUT";
            }

            const res = await fetch(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Erro ao salvar perfil");
            }

            alert(isEdit ? "Perfil atualizado!" : "Perfil criado!");
            document.getElementById("modal-perfil").style.display = "none";
            carregarPerfis();
            
            // Se existir a função de recarregar opções de perfil no form de usuários
            if (typeof carregarOpcoesPerfis === 'function') {
                carregarOpcoesPerfis();
            }

        } catch (err) {
            alert("Erro: " + err.message);
        }
    });
});

async function carregarPerfis() {
    const tbody = document.getElementById("tabela-perfis");
    const loading = document.getElementById("loading-perfis");
    const errorMsg = document.getElementById("error-msg-perfis");

    tbody.innerHTML = "";
    loading.style.display = "block";
    errorMsg.style.display = "none";

    try {
        const res = await fetch(`${API_URL}/api/perfis/`);
        if (!res.ok) throw new Error("Falha ao buscar perfis");
        
        const perfis = await res.json();
        window._perfisCarregados = perfis; // Guarda para uso global se necessário

        loading.style.display = "none";

        perfis.forEach(p => {
            const tr = document.createElement("tr");
            const btnExcluir = p.is_system ? 
                `<button class="btn btn-sm btn-secondary" disabled title="Perfil de sistema não pode ser excluído">🗑️</button>` :
                `<button class="btn btn-sm btn-danger" onclick="excluirPerfil(${p.id})">🗑️</button>`;

            tr.innerHTML = `
                <td>${p.id}</td>
                <td>${p.nome} ${p.is_system ? '<span class="badge bg-warning text-dark">Sistema</span>' : ''}</td>
                <td>${p.descricao || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick='abrirModalEditarPerfil(${JSON.stringify(p)})'>✏️</button>
                    ${btnExcluir}
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        loading.style.display = "none";
        errorMsg.innerText = err.message;
        errorMsg.style.display = "block";
    }
}

function gerarTabelaPermissoes(permissoesAtuais = []) {
    const tbody = document.querySelector("#tabela-permissoes-perfil tbody");
    tbody.innerHTML = "";

    MODULOS_SISTEMA.forEach(mod => {
        const perm = permissoesAtuais.find(p => p.modulo === mod.id) || {
            pode_visualizar: false, pode_criar: false, pode_editar: false, pode_excluir: false
        };

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${mod.nome}</td>
            <td class="text-center"><input type="checkbox" class="form-check-input" id="perm_${mod.id}_vis" ${perm.pode_visualizar ? 'checked' : ''}></td>
            <td class="text-center"><input type="checkbox" class="form-check-input" id="perm_${mod.id}_cri" ${perm.pode_criar ? 'checked' : ''}></td>
            <td class="text-center"><input type="checkbox" class="form-check-input" id="perm_${mod.id}_edi" ${perm.pode_editar ? 'checked' : ''}></td>
            <td class="text-center"><input type="checkbox" class="form-check-input" id="perm_${mod.id}_exc" ${perm.pode_excluir ? 'checked' : ''}></td>
        `;
        tbody.appendChild(tr);
    });
}

window.abrirModalNovoPerfil = () => {
    document.getElementById("form-perfil").reset();
    document.getElementById("perfil-id").value = "";
    document.getElementById("titulo-modal-perfil").innerText = "Novo Perfil";
    document.getElementById("perfil-nome").disabled = false;
    
    gerarTabelaPermissoes([]); // Zera os checks
    document.getElementById("modal-perfil").style.display = "flex";
};

window.abrirModalEditarPerfil = (p) => {
    document.getElementById("perfil-id").value = p.id;
    document.getElementById("perfil-nome").value = p.nome;
    document.getElementById("perfil-descricao").value = p.descricao || "";
    
    // Se for de sistema, talvez não deixar alterar nome
    document.getElementById("perfil-nome").disabled = p.is_system;

    document.getElementById("titulo-modal-perfil").innerText = "Editar Perfil";
    
    gerarTabelaPermissoes(p.permissoes);
    document.getElementById("modal-perfil").style.display = "flex";
};

window.excluirPerfil = async (id) => {
    if (confirm("Tem certeza que deseja excluir este perfil? Usuários vinculados a ele podem perder acesso.")) {
        try {
            const res = await fetch(`${API_URL}/api/perfis/${id}`, { method: "DELETE" });
            if (!res.ok) throw new Error((await res.json()).detail || "Erro ao excluir perfil");
            alert("Perfil excluído!");
            carregarPerfis();
        } catch (err) {
            alert("Erro: " + err.message);
        }
    }
};
