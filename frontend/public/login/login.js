const API_URL = "http://127.0.0.1:8000";

document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const errorBox = document.getElementById("error-box");
    const btnSubmit = document.getElementById("btn-submit");

    errorBox.style.display = "none";
    btnSubmit.disabled = true;
    btnSubmit.innerText = "Entrando...";

    try {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const response = await fetch(`${API_URL}/token`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error("Credenciais inválidas");
        }

        const data = await response.json();
        const token = data.access_token;

        // Use global Auth from auth.js
        window.Auth.login(token);

    } catch (err) {
        errorBox.innerText = "Erro: Usuário ou senha incorretos.";
        errorBox.style.display = "block";
        btnSubmit.disabled = false;
        btnSubmit.innerText = "Entrar";
    }
});
