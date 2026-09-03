const API_URL = window.API_BASE || "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", () => {
    carregarUsuarios();
    carregarOpcoesPerfis();

    // Novo Usuário Form
    // Novo/Editar Usuário Form
    document.getElementById("form-novo-usuario").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const data = Object.fromEntries(fd.entries());
        data.ativo = true;
        const isEdit = !!data.user_id;

        const actionText = isEdit ? `Atualizar usuário ${data.nome}?` : `Criar usuário ${data.nome}?`;

        if (confirm(actionText)) {
            try {
                let url = `${API_URL}/usuarios/`;
                let method = "POST";

                if (isEdit) {
                    url += data.user_id;
                    method = "PUT";
                    // No password update here, only create
                    delete data.senha;
                } else {
                    // Creation mode: remove empty user_id
                    delete data.user_id;
                }

                const res = await fetch(url, {
                    method: method,
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data)
                });

                if (!res.ok) {
                    const errData = await res.json();
                    let errorMsg = errData.detail || "Erro na operação";

                    // If detail is an array (Pydantic validation error)
                    if (Array.isArray(errorMsg)) {
                        errorMsg = errorMsg.map(e => `- ${e.msg}`).join("\n");
                    }

                    throw new Error(errorMsg);
                }

                alert(isEdit ? "Usuário atualizado!" : "Usuário criado!");
                document.getElementById("modal-novo").style.display = "none";
                e.target.reset();
                carregarUsuarios();
            } catch (err) {
                alert("Erro: " + err.message);
            }
        }
    });

    // Reset Senha Form
    document.getElementById("form-reset-senha").addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = document.getElementById("reset-user-id").value;
        const senha = document.getElementById("reset-nova-senha").value;

        if (confirm("Confirma o reset de senha?")) {
            try {
                const res = await fetch(`${API_URL}/usuarios/${id}/reset-senha`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ senha_nova: senha })
                });
                if (!res.ok) {
                    const errData = await res.json();
                    let errorMsg = errData.detail || "Erro ao resetar";
                    if (Array.isArray(errorMsg)) {
                        errorMsg = errorMsg.map(e => `- ${e.msg}`).join("\n");
                    }
                    throw new Error(errorMsg);
                }
                alert("Senha resetada com sucesso!");
                document.getElementById("modal-reset").style.display = "none";
            } catch (err) {
                alert("Erro: " + err.message);
            }
        }
    });
});

async function carregarOpcoesPerfis() {
    const select = document.getElementById("input-funcao");
    if (!select) return;
    try {
        const res = await fetch(`${API_URL}/api/perfis/`);
        if (res.ok) {
            const perfis = await res.json();
            select.innerHTML = "";
            perfis.forEach(p => {
                const opt = document.createElement("option");
                // For now, we still send the profile name to backend if backend expects string in funcao, 
                // but ideally backend should take perfil_id. We'll use nome as value to avoid breaking backend if it expects string, 
                // or we use id if backend is adapted. Let's send ID if we want, but backend update is needed.
                // Assuming we use `nome` as value for backward compatibility, or `id` if adapted.
                // I will update backend to use `perfil_id` or map `funcao` to it later. I will use `p.nome` for now.
                opt.value = p.nome; 
                opt.textContent = p.nome;
                opt.dataset.id = p.id;
                select.appendChild(opt);
            });
        }
    } catch (e) {
        console.error("Erro ao carregar perfis para o select", e);
    }
}

async function carregarUsuarios() {
    const tbody = document.getElementById("tabela-usuarios");
    const loading = document.getElementById("loading-usuarios") || document.getElementById("loading");
    const errorMsg = document.getElementById("error-msg-usuarios") || document.getElementById("error-msg");

    tbody.innerHTML = "";
    loading.style.display = "block";
    errorMsg.style.display = "none";

    try {
        const res = await fetch(`${API_URL}/usuarios/`);
        if (!res.ok) throw new Error("Falha ao buscar usuários (403 Forbidden se não for Admin)");

        const usuarios = await res.json();

        loading.style.display = "none";

        usuarios.forEach(u => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${u.id}</td>
                <td>${u.nome || '-'}</td>
                <td>${u.email}</td>
                <td><span class="badge bg-secondary">${u.funcao}</span></td>
                <td>${u.ativo ? '<span class="text-success">Ativo</span>' : '<span class="text-danger">Inativo</span>'}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick='abrirModalEditar(${JSON.stringify(u)})'>✏️</button>
                    <button class="btn btn-sm btn-warning" onclick="abrirModalReset(${u.id}, '${u.email}')">🔑</button>
                    <button class="btn btn-sm btn-danger" onclick="excluirUsuario(${u.id})">🗑️</button>
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

// Global functions
window.abrirModalNovoUsuario = () => {
    document.getElementById("user-id").value = "";
    document.getElementById("form-novo-usuario").reset();
    const titulo = document.getElementById("titulo-modal-usuario") || document.querySelector(".custom-modal-title");
    if(titulo) titulo.innerText = "Novo Usuário";
    document.getElementById("input-senha").disabled = false;
    document.getElementById("modal-novo").style.display = "flex";
};

window.abrirModalEditar = (u) => {
    document.getElementById("user-id").value = u.id;
    document.getElementById("input-nome").value = u.nome || "";
    document.getElementById("input-email").value = u.email;
    document.getElementById("input-funcao").value = u.funcao;

    // Password cannot be changed here
    const pwInput = document.getElementById("input-senha");
    pwInput.value = "";
    pwInput.placeholder = "Senha inalterada na edição";
    pwInput.disabled = true;

    const titulo = document.getElementById("titulo-modal-usuario") || document.querySelector(".custom-modal-title");
    if(titulo) titulo.innerText = "Editar Usuário";
    document.getElementById("modal-novo").style.display = "flex";
};

window.excluirUsuario = async (id) => {
    if (confirm("Tem certeza que deseja excluir este usuário? Esta ação não pode ser desfeita.")) {
        try {
            const res = await fetch(`${API_URL}/usuarios/${id}`, { method: "DELETE" });
            if (!res.ok) throw new Error((await res.json()).detail || "Erro ao excluir");
            alert("Usuário excluído!");
            carregarUsuarios();
        } catch (err) {
            alert("Erro: " + err.message);
        }
    }
};

window.abrirModalReset = (id, email) => {
    document.getElementById("reset-user-id").value = id;
    document.getElementById("reset-user-email").innerText = email;
    // Security Fix: Clear the password field to prevent showing previous input
    document.getElementById("reset-nova-senha").value = "";
    document.getElementById("modal-reset").style.display = "flex";
};

