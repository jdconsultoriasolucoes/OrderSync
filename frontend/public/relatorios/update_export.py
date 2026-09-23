import re

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'r', encoding='utf-8') as f:
    content = f.read()

original_fn = """function exportarExcel() {
    if (listagemVendas.length === 0) {
        alert("Não há dados carregados para exportar.");
        return;
    }

    let aoa = [];
    let filename = "";
    
    let totalPeso = 0;
    let totalSemFrete = 0;
    let totalComFrete = 0;

    if (activeReport === "cliente") {
        aoa.push(["#", "Nº Pedido Sistema", "Pedido Supra", "Danfe", "Data Faturamento", "Código Cliente", "Cliente", "Nome Fantasia", "Município", "Peso Líquido (kg)", "Valor Sem Frete", "Valor Com Frete"]);
        filename = "relatorio_vendas_por_cliente";

        listagemVendas.forEach((item, index) => {
            const p = parseFloat(item.peso_liquido || 0);
            const vs = parseFloat(item.valor_sem_frete || 0);
            const vc = parseFloat(item.valor_com_frete || 0);

            totalPeso += p;
            totalSemFrete += vs;
            totalComFrete += vc;

            aoa.push([index + 1, item.numero_pedido || "-", item.pedido_supra || "-", item.danfe || "-", fmtData(item.data_faturamento), item.codigo_cliente || "-", limparNomeCliente(item.cliente), item.nome_fantasia || "-", item.municipio || "-", Math.round(p), vs, vc]);
        });

        aoa.push(["TOTAL ACUMULADO", "", "", "", "", "", "", "", "", Math.round(totalPeso), totalSemFrete, totalComFrete]);

    } else if (activeReport === "produto") {
        aoa.push(["#", "Código Produto", "Produto", "Embalagem", "Peso Líq. Unit. (kg)", "Quantidade", "Peso Líq. Acumulado (kg)", "Valor Sem Frete", "Valor Com Frete"]);
        filename = "relatorio_vendas_por_produto";

        listagemVendas.forEach((item, index) => {
            const pu = parseFloat(item.peso_liquido_unitario || 0);
            const q = parseFloat(item.quantidade || 0);
            const pa = parseFloat(item.peso_liquido_acumulado || 0);
            const vs = parseFloat(item.valor_sem_frete || 0);
            const vc = parseFloat(item.valor_com_frete || 0);

            totalPeso += pa;
            totalSemFrete += vs;
            totalComFrete += vc;

            aoa.push([index + 1, item.codigo_produto || "-", item.produto || "-", item.embalagem || "-", Math.round(pu), q, Math.round(pa), vs, vc]);
        });

        aoa.push(["TOTAL ACUMULADO", "", "", "", "", "", Math.round(totalPeso), totalSemFrete, totalComFrete]);

    } else if (activeReport === "gerencial") {
        aoa.push(["#", "CNPJ/CPF", "Nome Cliente", "Município", "Vendedor", "Data Última Compra", "Observação"]);
        filename = "relatorio_gerencial";

        listagemVendas.forEach((item, index) => {
            aoa.push([index + 1, fmtDoc(item.documento) || "-", limparNomeCliente(item.nome_cliente), item.municipio || "-", item.vendedor || "-", fmtData(item.data_ultima_compra), item.observacao || "-"]);
        });
    } else if (activeReport === "gerencial2") {
        let row1 = ["Cód. Cliente", "Cliente"];
        let row2 = ["", ""];
        
        gerencial2Meses.forEach(m => {
            const [ano, mes] = m.split('-');
            row1.push(`${mes}/${ano}`, "");
            row2.push("Peso (kg)", "Valor (R$)");
        });
        
        aoa.push(row1, row2);
        filename = "relatorio_gerencial2_evolucao";
        
        listagemVendas.forEach((item, index) => {
            let row = [item.codigo_cliente || "-", limparNomeCliente(item.cliente)];
            gerencial2Meses.forEach(m => {
                row.push(item.meses?.[m]?.peso || 0);
                row.push(item.meses?.[m]?.valor || 0);
            });
            aoa.push(row);
        });
    } else if (activeReport === "gerencial3") {
        let row1 = ["Cód. Cliente", "Cliente", "Data Última Compra", "Previsão Próxima Compra"];
        let row2 = ["", "", "", ""];
        
        gerencial3Meses.forEach(m => {
            const [ano, mes] = m.split('-');
            row1.push(`${mes}/${ano}`, "");
            row2.push("Peso (kg)", "Valor (R$)");
        });
        
        aoa.push(row1, row2);
        filename = "relatorio_gerencial3_evolucao";
        
        listagemVendas.forEach((item, index) => {
            let row = [item.codigo_cliente || "-", limparNomeCliente(item.cliente), fmtData(item.data_ultima_compra_geral), fmtData(item.previsao_proxima_compra)];
            gerencial3Meses.forEach(m => {
                row.push(item.meses?.[m]?.peso || 0);
                row.push(item.meses?.[m]?.valor || 0);
            });
            aoa.push(row);
        });
    }

    const ws = XLSX.utils.aoa_to_sheet(aoa);

    // Apply merges for gerencial2
    if (activeReport === "gerencial2") {
        ws['!merges'] = [
            { s: {r:0, c:0}, e: {r:1, c:0} },
            { s: {r:0, c:1}, e: {r:1, c:1} }
        ];
        
        let cIndex = 2;
        gerencial2Meses.forEach(m => {
            ws['!merges'].push({ s: {r:0, c:cIndex}, e: {r:0, c:cIndex+1} });
            cIndex += 2;
        });
        
        for (let cell in ws) {
            if (cell[0] === '!') continue;
            
            const row = parseInt(cell.replace(/\D/g, ''));
            if (!ws[cell].s) ws[cell].s = {};
            
            if (row === 1 || row === 2) {
                ws[cell].s = { alignment: { horizontal: "center", vertical: "center" }, font: { bold: true } };
            } else if (typeof ws[cell].v === 'number') {
                ws[cell].z = '#,##0.00';
            }
        }
        
        ws['!cols'] = [{ wch: 15 }, { wch: 45 }]; // Cód Cliente e Cliente
        for (let i = 0; i < gerencial2Meses.length * 2; i++) {
            ws['!cols'].push({ wch: 15 }); // Peso e Valor
        }
    } else if (activeReport === "gerencial3") {
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
        
        for (let cell in ws) {
            if (cell[0] === '!') continue;
            
            const row = parseInt(cell.replace(/\D/g, ''));
            if (!ws[cell].s) ws[cell].s = {};
            
            if (row === 1 || row === 2) {
                ws[cell].s = { alignment: { horizontal: "center", vertical: "center" }, font: { bold: true } };
            } else if (typeof ws[cell].v === 'number') {
                ws[cell].z = '#,##0.00';
            }
        }
        
        ws['!cols'] = [{ wch: 15 }, { wch: 45 }, { wch: 20 }, { wch: 20 }];
        for (let i = 0; i < gerencial3Meses.length * 2; i++) {
            ws['!cols'].push({ wch: 15 }); // Peso e Valor
        }
    }

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Relatorio");
    XLSX.writeFile(wb, `${filename}_${new Date().toISOString().slice(0, 10)}.xlsx`);
}"""

# Replace the whole exportarExcel block
content = re.sub(r'function exportarExcel\(\) \{.*?XLSX\.writeFile\(wb, `\$\{filename\}_\$\{new Date\(\)\.toISOString\(\)\.slice\(0, 10\)\}\.xlsx`\);\n\}', original_fn, content, flags=re.DOTALL)

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Restored exportarExcel")
