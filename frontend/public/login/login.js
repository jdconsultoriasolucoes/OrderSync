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

        console.log("Login successful! Saving token...");
        // Use global Auth from auth.js
        window.Auth.login(token);

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
