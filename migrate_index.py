import os
import re

ux_index = "E:\\OrderSync - UX\\frontend\\index.html"
dev_index = "E:\\OrderSync - Dev\\frontend\\index.html"

with open(ux_index, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace "public/" paths with "/" to match Dev Vite/Server resolution
content = content.replace('href="public/', 'href="/')
content = content.replace('src="public/', 'src="/')

# Fix auth script block 
ux_auth_block = """        // Auth check bypass for UX testing
        (function () {
            // const token = localStorage.getItem("ordersync_token");
            // if (!token) {
            //     window.location.href = "/login/login.html";
            // }
        })();

        window.addEventListener('load', function () {
            if (window.Auth) {
                window.Auth.checkAuth();
            }
        });"""

dev_auth_block = """        // Fail-safe: Check token immediately before waiting for Auth object
        (function () {
            const token = localStorage.getItem("ordersync_token");
            if (!token) {
                console.warn("No token found in index.html, redirecting to login...");
                window.location.href = "/login/login.html";
            }
        })();

        // Auth.checkAuth() will handle redirect if needed
        window.addEventListener('load', function () {
            if (window.Auth) {
                window.Auth.checkAuth();
            } else {
                console.error("Auth module failed to load!");
            }
        });"""

content = content.replace(ux_auth_block, dev_auth_block)

with open(dev_index, 'w', encoding='utf-8') as f:
    f.write(content)

print("index.html migrated successfully")
