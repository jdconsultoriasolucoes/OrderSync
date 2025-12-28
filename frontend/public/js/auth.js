const AUTH_TOKEN_KEY = "ordersync_token";
const LOGIN_URL = "/public/login.html"; // Considering simple file server structure

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
        // Allow public pages (login, public links)
        const path = window.location.pathname;
        if (path.includes("login.html") || path.includes("/public/")) {
            return;
        }

        if (!Auth.isAuthenticated()) {
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
