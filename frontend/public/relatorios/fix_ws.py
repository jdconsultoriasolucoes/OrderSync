import sys
import re

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to remove the blocks from alternarRelatorioUI and renderizarTabela
# They look like:
"""
    if (activeReport === "gerencial3") {
        ws['!merges'] = [ ... ]
        ...
    }
"""

def remove_spurious_ws(text):
    # find all ws configurations and only keep them if they are in the exportarExcel function
    parts = text.split('function exportarExcel() {')
    if len(parts) == 2:
        part1 = parts[0]
        part2 = parts[1]
        
        # Clean part1 from any "if (activeReport === "gerencial3") { \n ws..."
        part1 = re.sub(r'if \(activeReport === "gerencial3"\) \{\s*ws\[\'!merges\'\].*?\}\s*', '', part1, flags=re.DOTALL)
        part1 = re.sub(r'if \(activeReport === "gerencial3"\) \{\s*ws\[\'!cols\'\].*?\}\s*', '', part1, flags=re.DOTALL)
        
        return part1 + 'function exportarExcel() {' + part2
    return text

new_content = remove_spurious_ws(content)

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Fixed ws error")
