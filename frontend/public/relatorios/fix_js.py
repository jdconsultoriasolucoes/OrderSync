import sys

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    # Remove the invalid dataG blocks
    if 'if (dataG.vendedores && selG3Vendedor) {' in line:
        skip = True
    
    if skip:
        if '});' in line and '}' in lines[i+1] and 'if' not in lines[i+1]:
            pass # still skipping
        if line.strip() == '}' and ('if' in lines[i-1] or '});' in lines[i-1] or 'selG3Status.appendChild(opt);' in lines[i-1] or 'dataG.status_cadastro' in lines[i-5]):
            if 'selG3Status' in lines[i-1] or 'selG3Status' in lines[i-2] or 'selG3Status' in lines[i-3] or 'selG3Status' in lines[i-4] or 'selG3Status' in lines[i-5]:
                skip = False
                continue
    
    if not skip:
        new_lines.append(line)

# Now, we need to correctly insert the G3 filter population inside `if (respGerencial.ok) { const dataG = await respGerencial.json(); ... }`
# Let's find where dataG.status_cadastro is processed for Gerencial 1, and insert it after.

final_lines = []
for i, line in enumerate(new_lines):
    final_lines.append(line)
    if 'selGerencialStatus.appendChild(opt);' in line:
        # After the closing of dataG.status_cadastro block
        pass
    if 'if (dataG.status_cadastro && selGerencialStatus) {' in new_lines[i-2] and '});' in line:
        # insert G3 population
        g3_pop = """
            if (dataG.vendedores && selG3Vendedor) {
                dataG.vendedores.forEach(v => {
                    const opt = document.createElement("option");
                    opt.value = v;
                    opt.textContent = v;
                    selG3Vendedor.appendChild(opt);
                });
            }
            if (dataG.municipios && selG3Municipio) {
                dataG.municipios.forEach(m => {
                    const opt = document.createElement("option");
                    opt.value = m;
                    opt.textContent = m;
                    selG3Municipio.appendChild(opt);
                });
            }
            if (dataG.status_cadastro && selG3Status) {
                dataG.status_cadastro.forEach(s => {
                    const opt = document.createElement("option");
                    opt.value = s;
                    opt.textContent = s;
                    selG3Status.appendChild(opt);
                });
            }
"""
        final_lines.append(g3_pop)

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print("Fixed relatorios_vendas.js")
