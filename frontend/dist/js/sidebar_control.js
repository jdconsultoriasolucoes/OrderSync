// sidebar_control.js
// Controls visibility of sidebar items based on user role (e.g. Vendedor cannot see Users or Config Email)

document.addEventListener("DOMContentLoaded", () => {
    // Wait slightly to ensure Auth is ready or Sidebar is rendered
    setTimeout(applyAccessControl, 100);
});

function applyAccessControl() {
    if (!window.Auth) return;

    const user = window.Auth.getUser();
    if (!user) return; // Not logged in?

    const role = (user.funcao || "").toLowerCase(); // "admin", "gerente", "vendedor"

    if (role === "vendedor") {
        console.log("[AccessControl] Hiding restricted items for Vendedor.");

        // Items to hide: 
        // 1. Usuarios (Gerenciar Usuarios) -> href="/usuarios.html" or similar
        // 2. Config Email -> href="/config_email/config_email.html"

        const sidebarLinks = document.querySelectorAll("#sidebar ul li a");

        sidebarLinks.forEach(link => {
            const href = link.getAttribute("href");
            if (!href) return;

            // Normalize checks
            if (href.includes("usuarios.html") || href.includes("config_email")) {
                // Hide the parent LI
                const li = link.closest("li");
                if (li) {
                    li.style.display = "none";
                }
            }
        });
    }
}
