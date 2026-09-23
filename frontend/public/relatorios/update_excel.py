import sys

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Excel Export for Gerencial 3
export_g3 = '''
    } else if (activeReport === "gerencial3") {
        let row1 = ["Cód. Cliente", "Cliente", "Última Compra", "Próxima Compra"];
        let row2 = ["", "", "", ""];
        
        gerencial3Meses.forEach(m => {
            const [ano, mes] = m.split('-');
            row1.push(`${mes}/${ano}`, "");
            row2.push("Peso", "Valor");
        });
        
        aoa.push(row1);
        aoa.push(row2);
        
        filename = "relatorio_gerencial3";
        
        listagemVendas.forEach((item, index) => {
            let row = [
                item.codigo_cliente,
                item.cliente || "",
                fmtData(item.data_ultima_compra_geral),
                fmtData(item.previsao_proxima_compra)
            ];
            
            gerencial3Meses.forEach(m => {
                row.push(item.meses?.[m]?.peso || 0);
                row.push(item.meses?.[m]?.valor || 0);
            });
            aoa.push(row);
        });
'''

if '} else if (activeReport === "gerencial3") {' not in content.split('function exportarExcel()')[1]:
    content = content.replace('} else if (activeReport === "gerencial2") {', export_g3 + '\n    } else if (activeReport === "gerencial2") {')

# Merge configuration for Gerencial 3
merge_g3 = '''
    if (activeReport === "gerencial3") {
        ws['!merges'] = [
            { s: {r:0, c:0}, e: {r:1, c:0} },
            { s: {r:0, c:1}, e: {r:1, c:1} },
            { s: {r:0, c:2}, e: {r:1, c:2} },
            { s: {r:0, c:3}, e: {r:1, c:3} }
        ];
        let cIndex = 4;
        gerencial3Meses.forEach(m => {
            ws['!merges'].push({ s: {r:0, c:cIndex}, e: {r:0, c:cIndex+1} });
            cIndex += 2;
        });
    }
'''

if 'if (activeReport === "gerencial3") {' not in content.split('// Apply merges')[1]:
    content = content.replace('if (activeReport === "gerencial2") {', merge_g3 + '\n    if (activeReport === "gerencial2") {')


# Columns width configuration for Gerencial 3
cols_g3 = '''
    if (activeReport === "gerencial3") {
        ws['!cols'] = [
            { wch: 15 },
            { wch: 40 },
            { wch: 15 },
            { wch: 15 }
        ];
        for (let i = 0; i < gerencial3Meses.length * 2; i++) {
            ws['!cols'].push({ wch: 15 }); // Peso e Valor
        }
    }
'''

if 'if (activeReport === "gerencial3") {' not in content.split('// Configura largura das colunas')[1]:
    content = content.replace('if (activeReport === "gerencial2") {', cols_g3 + '\n    if (activeReport === "gerencial2") {')


with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done Excel")
