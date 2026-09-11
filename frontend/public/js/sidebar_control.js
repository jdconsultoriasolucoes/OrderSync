// sidebar_control.js
// Controls visibility of sidebar items based on user role (e.g. Vendedor cannot see Users or Config Email)

document.addEventListener("DOMContentLoaded", () => {
    // Wait slightly to ensure Auth is ready or Sidebar is rendered
    setTimeout(applyAccessControl, 100);
    initSidebarToggle();
});

function initSidebarToggle() {
    const menuButton = document.getElementById("menu-button");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");

    if (menuButton && sidebar) {
        // Toggle on button click
        menuButton.addEventListener("click", (e) => {
            e.stopPropagation();
            sidebar.classList.toggle("active");
            if (overlay) overlay.classList.toggle("active");
        });
    }

    // Global click listener to close sidebar on any click outside
    document.addEventListener("click", (e) => {
        if (!sidebar) return;

        if (sidebar.classList.contains("active")) {
            // If click is NOT inside sidebar AND NOT on menu button
            if (!sidebar.contains(e.target) && (!menuButton || !menuButton.contains(e.target))) {
                sidebar.classList.remove("active");
                if (overlay) overlay.classList.remove("active");
            }
        }
    });

    if (overlay) {
        overlay.addEventListener("click", () => {
            sidebar.classList.remove("active");
            overlay.classList.remove("active");
        });
    }
}

function applyAccessControl() {
    if (!window.Auth) return;
    // ... rest of the function stays the same ...

    const user = window.Auth.getUser();
    if (!user) return; // Not logged in?

    const role = (user.funcao || "").toLowerCase(); // "admin", "gerente", "vendedor"

    if (role === "vendedor") {
        console.log("[AccessControl] Hiding restricted items for Vendedor.");

        // Items to hide: 
        // 1. Configurações -> href="/configuracoes.html"

        const sidebarLinks = document.querySelectorAll("#sidebar ul li a");

        sidebarLinks.forEach(link => {
            const href = link.getAttribute("href");
            if (!href) return;



            // Normalize checks
            if (href.includes("configuracoes.html")) {
                // Hide the parent LI
                const li = link.closest("li");
                if (li) {
                    li.style.display = "none";
                }
            }
        });
    }
}

// --- Notificação Global (Sino) ---
function injectNotificationBell() {
    const header = document.querySelector('.os-header');
    if (!header) return;

    // Remove old bell if any
    const oldBell = document.getElementById('global-notification-bell');
    if (oldBell) oldBell.remove();

    const bellHTML = `
        <div id="global-notification-bell" style="position: relative; cursor: pointer; margin-right: 15px; display: flex; align-items: center;" title="Notificações">
            <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" style="color: #4a5568;"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
            <span id="global-bell-badge" style="position: absolute; top: -5px; right: -5px; background: #e53e3e; color: white; border-radius: 50%; font-size: 10px; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; font-weight: bold; display: none;">0</span>
            <div id="global-notification-dropdown" style="display: none; position: absolute; top: 35px; right: -10px; width: 300px; background: white; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 9999; flex-direction: column; max-height: 400px; text-align: left; cursor: default;">
                <div style="padding: 10px 15px; border-bottom: 1px solid #e2e8f0; font-weight: 600; font-size: 0.9rem; color: #1a202c; background: #f8fafc;">Notificações de Hoje (Calendário)</div>
                <div id="global-notification-list" style="overflow-y: auto; padding: 10px; font-size: 0.85rem; color: #4a5568; display: flex; flex-direction: column;">
                    Carregando...
                </div>
            </div>
        </div>
    `;

    // Achar a logo
    const logo = header.querySelector('.os-logo');
    
    const wrapper = document.createElement('div');
    wrapper.innerHTML = bellHTML;
    const bellEl = wrapper.firstElementChild;
    
    if (logo) {
        logo.style.marginLeft = '15px';
        logo.style.order = '4';
        
        bellEl.style.marginLeft = 'auto';
        bellEl.style.order = '3';
        
        header.insertBefore(bellEl, logo);
    } else {
        bellEl.style.marginLeft = 'auto';
        bellEl.style.order = '3';
        header.appendChild(bellEl);
    }

    bellEl.addEventListener('click', async (e) => {
        e.stopPropagation();
        const dropdown = document.getElementById('global-notification-dropdown');
        const isVisible = dropdown.style.display === 'flex';
        
        if (isVisible) {
            dropdown.style.display = 'none';
        } else {
            dropdown.style.display = 'flex';
            await loadGlobalNotifications();
        }
    });

    document.addEventListener('click', (e) => {
        const dropdown = document.getElementById('global-notification-dropdown');
        if (dropdown && dropdown.style.display === 'flex' && !dropdown.contains(e.target) && !bellEl.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });

    loadGlobalNotifications(true);
}

async function loadGlobalNotifications(countOnly = false) {
    try {
        const token = window.Auth ? window.Auth.getToken() : null;
        if (!token) return;
        
        const tzOffset = new Date().getTimezoneOffset() * 60000;
        const hojeLocal = new Date(Date.now() - tzOffset).toISOString().split('T')[0];
        
        const API_BASE = typeof window.API_BASE !== 'undefined' ? window.API_BASE : '';
        const url = `${API_BASE}/api/v1/events?start_date=${hojeLocal}&end_date=${hojeLocal}`;
        
        const resp = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
        if (!resp.ok) throw new Error("Falha");
        
        const events = await resp.json();
        const hojeEvents = events.filter(e => {
            if (e.start_time) {
                const parts = e.start_time.split('T')[0].split('-');
                if (parts.length === 3) {
                    const eDayStr = `${parts[0]}-${parts[1]}-${parts[2]}`;
                    return eDayStr === hojeLocal;
                }
            }
            return false;
        });

        const badge = document.getElementById('global-bell-badge');
        if (badge) {
            if (hojeEvents.length > 0) {
                badge.textContent = hojeEvents.length;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }

        if (!countOnly) {
            const list = document.getElementById('global-notification-list');
            if (!list) return;
            
            if (hojeEvents.length === 0) {
                list.innerHTML = "<div style='text-align: center; padding: 10px 0;'>Sem compromissos hoje.</div>";
            } else {
                list.innerHTML = hojeEvents.map(ev => {
                    const t = ev.start_time ? new Date(ev.start_time).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'}) : '';
                    return `<div style="padding: 8px 10px; border-bottom: 1px solid #edf2f7; border-radius: 4px; margin-bottom: 4px; background: #f8fafc;">
                        <strong style="color: #2b6cb0;">${t}</strong> - ${ev.title}
                    </div>`;
                }).join("");
            }
        }
    } catch (e) {
        console.error(e);
        const list = document.getElementById('global-notification-list');
        if (list && !countOnly) {
            list.innerHTML = "<div style='text-align: center; padding: 10px 0; color: red;'>Erro ao carregar notificações.</div>";
        }
    }
}

// Injetar o sino globalmente
document.addEventListener("DOMContentLoaded", () => {
    setTimeout(injectNotificationBell, 300);
});
