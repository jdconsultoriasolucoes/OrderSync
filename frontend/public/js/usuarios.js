const API_URL = window.API_BASE || "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", () => {
    carregarUsuarios();

    // Novo Usuário Form
    document.getElementById("form-novo-usuario").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const data = Object.fromEntries(fd.entries());
        data.ativo = true; // Default

        if (confirm(`Criar usuário ${data.nome}?`)) {
            try {
                const res = await fetch(`${API_URL}/usuarios/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data)
                });
                if (!res.ok) throw new Error((await res.json()).detail || "Erro ao criar");
                alert("Usuário criado com sucesso!");
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
        const senha = document.getElementById("nova-senha").value;

        if (confirm("Confirma o reset de senha?")) {
            try {
                const res = await fetch(`${API_URL}/usuarios/${id}/reset-senha`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ senha_nova: senha })
                });
                if (!res.ok) throw new Error((await res.json()).detail || "Erro ao resetar");
                alert("Senha resetada com sucesso!");
                document.getElementById("modal-reset").style.display = "none";
            } catch (err) {
                alert("Erro: " + err.message);
            }
        }
    });
});

async function carregarUsuarios() {
    const tbody = document.getElementById("tabela-usuarios");
    const loading = document.getElementById("loading");
    const errorMsg = document.getElementById("error-msg");

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
                    <button class="btn btn-sm btn-warning" onclick="abrirModalReset(${u.id}, '${u.email}')">Resetar Senha</button>
                    <!-- <button class="btn btn-sm btn-danger">Inativar</button> (To be implemented) -->
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

// Global functions for HTML access
window.abrirModalNovoUsuario = () => {
    document.getElementById("modal-novo").style.display = "flex";
};

window.abrirModalReset = (id, email) => {
    document.getElementById("reset-user-id").value = id;
    document.getElementById("reset-user-email").innerText = email;
    document.getElementById("nova-senha").value = "";
    document.getElementById("modal-reset").style.display = "flex";
};
