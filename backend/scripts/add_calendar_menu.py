import os
import glob
import re

CALENDAR_LINK = """            <li><a href="/calendario/index.html">
                    <svg class="os-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="16" y1="2" x2="16" y2="6"></line>
                        <line x1="8" y1="2" x2="8" y2="6"></line>
                        <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg> Calendário
                </a></li>
"""

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
html_files = glob.glob(os.path.join(frontend_dir, '**', '*.html'), recursive=True)

modified_count = 0
for file_path in html_files:
    if 'node_modules' in file_path:
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Se já tem o calendário, pula
    if 'href="/calendario/index.html"' in content and 'Calendário' in content:
        continue

    # Acha o Dashboards no menu
    target = 'href="/dashboards.html"'
    if target in content:
        # Pega a linha inteira de fechamento do li do Dashboards
        # Vamos usar regex para encontrar o final do li do Dashboards
        pattern = re.compile(r'(<a href="/dashboards\.html".*?</a></li>)', re.DOTALL)
        match = pattern.search(content)
        if match:
            dashboards_li = match.group(1)
            # Insere logo após o li do Dashboards
            new_content = content[:match.end()] + "\n" + CALENDAR_LINK + content[match.end():]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            modified_count += 1
            print(f"Modificado: {file_path}")

print(f"Total modificado: {modified_count}")
