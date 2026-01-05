// Use global API_BASE from config.js or fallback
const API_URL = window.API_BASE || "http://127.0.0.1:8000";

document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const errorBox = document.getElementById("error-box");
    const btnSubmit = document.getElementById("btn-submit");

    errorBox.style.display = "none";
    errorBox.innerText = "";
    btnSubmit.disabled = true;
    btnSubmit.innerText = "Entrando...";

    try {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        console.log(`Attempting login to ${API_URL}/token...`);

        const response = await fetch(`${API_URL}/token`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || "Credenciais inválidas");
        }

        const data = await response.json();
        const token = data.access_token;

        console.log("Login successful! Saving token...", data);
        // Use global Auth from auth.js
        window.Auth.login(token, {
            nome: data.nome,
            funcao: data.funcao,
            reset_senha_obrigatorio: data.reset_senha_obrigatorio
        });

        // Check forced reset
        if (data.reset_senha_obrigatorio) {
            console.log("Forced password reset required.");
            // We need to show the modal. Since we are on login.html, we might need to load it specially or handle it.
            // But wait, login.html redirects to / on success (in Auth.login).
            // We should modify Auth.login to NOT redirect if reset is required? 
            // OR handle it on the dashboard?

            // The requirement says "when first login is made, it must request password change automatically".
            // If Auth.login redirects immediately, checking it here is useless unless we pass a flag to the next page.
            // Better approach: Store 'reset_required' in localStorage and check it in global Auth.checkAuth or similar.

            localStorage.setItem("ordersync_reset_required", "true");
        }


    } catch (err) {
        console.error("Login Error:", err);
        btnSubmit.disabled = false;
        btnSubmit.innerText = "Entrar";

        errorBox.style.display = "block";
        if (err.message.includes("Failed to fetch")) {
            errorBox.innerText = "Erro de Conexão: O servidor backend parece estar offline.";
        } else {
            errorBox.innerText = `Erro: ${err.message}`;
        }
    }
});
