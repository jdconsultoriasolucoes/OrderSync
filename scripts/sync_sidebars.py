import os
import re

# Caminho raiz do frontend
FRONTEND_DIR = r"e:\OrderSync\frontend"

# Regex para encontrar a tag <li> contendo o link da Logística
# Aceita caminhos absolutos (/relatorios/relatorios.html) ou relativos (../relatorios/relatorios.html)
LI_PATTERN = re.compile(
    r'(<li><a\s+href="([^"]*?relatorios/relatorios\.html)"([^>]*)>\s*.*?</svg>\s*Logística\s*</a></li>)',
    re.DOTALL | re.IGNORECASE
)

def sync_html_files():
    print("Iniciando sincronização dos menus de navegação...")
    count = 0
    
    for root, dirs, files in os.walk(FRONTEND_DIR):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                
                # Ignorar a pasta node_modules se existir por engano
                if "node_modules" in file_path:
                    continue
                    
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # Procura a tag da Logística
                match = LI_PATTERN.search(content)
                if match:
                    original_li = match.group(1)
                    original_href = match.group(2)
                    
                    # Cria o novo link de Relatórios mantendo o mesmo tipo de caminho (absoluto ou relativo)
                    new_href = original_href.replace("relatorios.html", "relatorios_vendas.html")
                    
                    # Verifica se o link dos Relatórios já está presente no arquivo
                    if "relatorios_vendas.html" in content:
                        # Já integrado, ignora
                        continue
                        
                    # Novo item da lista HTML
                    new_li = (
                        f'\n            <li><a href="{new_href}">'
                        '\n                    <svg class="os-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                        '\n                        <line x1="18" y1="20" x2="18" y2="10"></line>'
                        '\n                        <line x1="12" y1="20" x2="12" y2="4"></line>'
                        '\n                        <line x1="6" y1="20" x2="6" y2="14"></line>'
                        '\n                    </svg> Relatórios'
                        '\n                </a></li>'
                    )
                    
                    # Insere o novo li logo após o original
                    updated_content = content.replace(original_li, original_li + new_li)
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(updated_content)
                        
                    print(f" -> Sincronizado: {os.path.relpath(file_path, FRONTEND_DIR)}")
                    count += 1
                    
    print(f"Sincronização concluída! {count} arquivos atualizados.")

if __name__ == "__main__":
    sync_html_files()
