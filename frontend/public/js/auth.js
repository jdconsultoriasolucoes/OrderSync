const AUTH_TOKEN_KEY = "ordersync_token";

// Dynamic LOGIN_URL based on auth.js location
function getLoginUrl() {
    const scripts = document.getElementsByTagName('script');
    for (let script of scripts) {
        if (script.src.includes('auth.js')) {
            // script.src is absolute (http://.../public/js/auth.js)
            // We want to go from /public/js/auth.js to /public/login/login.html
            // So: up one level (../js) -> up one level (../public) -> down (login/login.html)
            // Wait: auth.js is in public/js/. login is in public/login/.
            // So ../login/login.html relative to auth.js
            return new URL('../login/login.html', script.src).href;
        }
    }
    return "/public/login/login.html"; // Fallback
}

const LOGIN_URL = getLoginUrl();

const Auth = {
    // Save token
    login: (token) => {
        localStorage.setItem(AUTH_TOKEN_KEY, token);
        window.location.href = "/";
    },

    // Remove token and redirect
    logout: () => {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        window.location.href = LOGIN_URL;
    },

    // Get raw token
    getToken: () => {
        return localStorage.getItem(AUTH_TOKEN_KEY);
    },

    // Check if user is authenticated (simple check)
    isAuthenticated: () => {
        return !!localStorage.getItem(AUTH_TOKEN_KEY);
    },

    // Enforce auth on protected pages
    checkAuth: () => {
        const path = window.location.pathname;

        // Allow public pages
        if (window.location.href.includes("/login/") || window.location.href.includes("login.html")) {
            return;
        }

        if (!Auth.isAuthenticated()) {
            console.log("Not authenticated, redirecting to:", LOGIN_URL);
            window.location.href = LOGIN_URL;
        }
    }
};

// --- Fetch Interceptor ---
const originalFetch = window.fetch;

window.fetch = async (url, options = {}) => {
    // 1. Inject Header
    const token = Auth.getToken();
    if (token) {
        if (!options.headers) {
            options.headers = {};
        }
        // Ensure headers is an object or Headers object
        if (options.headers instanceof Headers) {
            options.headers.append("Authorization", `Bearer ${token}`);
        } else {
            options.headers["Authorization"] = `Bearer ${token}`;
        }
    }

    // 2. Make Request
    try {
        const response = await originalFetch(url, options);

        // 3. Handle 401
        if (response.status === 401) {
            console.warn("Unauthorized! Redirecting to login...");
            if (!window.location.pathname.includes(LOGIN_URL)) {
                Auth.logout();
            }
        }

        return response;
    } catch (error) {
        throw error;
    }
};

// Check Auth on Load (if not excluded)
// We might want to call this manually in pages, or run it here.
// For now, let's expose Auth globally.
window.Auth = Auth;

// Inject Modal HTML automatically
document.addEventListener("DOMContentLoaded", () => {
    if (!document.getElementById("modal-trocar-senha")) {
        const modalHtml = `
            <div id="modal-trocar-senha" class="custom-modal" style="display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5); align-items: center; justify-content: center; z-index: 2000;">
                <div class="custom-modal-dialog" style="background: white; padding: 24px; border-radius: 12px; width: 90%; max-width: 400px;">
                    <div class="custom-modal-header" style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                        <h5 class="custom-modal-title" style="font-weight: 600; font-size: 1.25rem; margin:0;">Trocar Minha Senha</h5>
                        <button class="close-btn" style="background: none; border: none; font-size: 1.5rem; cursor: pointer;" onclick="window.Auth.closeChangePasswordModal()">&times;</button>
                    </div>
                    <form id="form-trocar-senha" onsubmit="window.Auth.confirmarTrocaSenha(event)">
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem;">Senha Atual</label>
                            <input type="password" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;" id="senha-atual" required>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem;">Nova Senha</label>
                            <input type="password" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;" id="nova-senha" required minlength="6">
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem;">Confirmar Nova Senha</label>
                            <input type="password" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;" id="confirm-nova-senha" required minlength="6">
                        </div>
                        <div style="display: flex; justify-content: flex-end; gap: 0.5rem;">
                            <button type="button" style="padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; background: #6c757d; color: white;" onclick="window.Auth.closeChangePasswordModal()">Cancelar</button>
                            <button type="submit" style="padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; background: #2563eb; color: white;">Salvar Nova Senha</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML("beforeend", modalHtml);
    }
});
