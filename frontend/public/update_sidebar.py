import os
import re

frontend_dir = r"e:\OrderSync\frontend\public"

# We want to replace the block of 2 LIs (config_email and usuarios) with 1 LI (configuracoes)
# in the 'Sistema' section of the sidebar.
# The structure usually looks like:
'''
            <li><a href="/config_email/config_email.html">
                    <svg ...>...</svg> Configuração E-mail
                </a></li>
            <li><a href="/profile/profile.html">
                    <svg ...>...</svg> Profile
                </a></li>
            <li><a href="/usuarios.html">
                    <svg ...>...</svg> Usuários
                </a></li>
'''
# It's better to just regex replace the specific config_email and usuarios blocks with empty string,
# and insert the configuracoes block right before profile.

config_email_pattern = re.compile(r'<li>\s*<a href="/config_email/config_email\.html">[\s\S]*?</a>\s*</li>', re.IGNORECASE)
usuarios_pattern = re.compile(r'<li>\s*<a href="/usuarios\.html">[\s\S]*?</a>\s*</li>', re.IGNORECASE)

configuracoes_html = '''<li><a href="/configuracoes.html">
                    <svg class="os-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                    </svg> Configurações
                </a></li>'''

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    
    # Remove old items
    content = config_email_pattern.sub('', content)
    content = usuarios_pattern.sub('', content)
    
    # Insert new item before profile
    # look for profile item: <li><a href="/profile/profile.html">
    profile_idx = content.find('<li><a href="/profile/profile.html">')
    if profile_idx != -1 and 'configuracoes.html' not in content:
        content = content[:profile_idx] + configuracoes_html + "\n            " + content[profile_idx:]
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, dirs, files in os.walk(frontend_dir):
    for file in files:
        if file.endswith('.html'):
            update_file(os.path.join(root, file))
