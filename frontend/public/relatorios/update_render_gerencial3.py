import re

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'r', encoding='utf-8') as f:
    content = f.read()

# First part: renderizar headers for gerencial3
pattern1 = r'    if \(activeReport === "gerencial2"\) \{.*?    \}'

replacement1 = """    if (activeReport === "gerencial2") {
        const mesesSel = document.getElementById("filtro-gerencial2-meses");
        const qtdeMeses = mesesSel ? parseInt(mesesSel.value) : 12;
        gerencial2Meses = generateLastXMonths(qtdeMeses);
        
        let htmlHeader1 = `<tr>
            <th rowspan="2" style="width: 40px; min-width: 40px; border-right: 1px solid var(--os-border);">#</th>
            <th rowspan="2" data-sort="codigo_cliente" style="min-width: 100px; border-right: 1px solid var(--os-border);">Cód. Cliente</th>
            <th rowspan="2" data-sort="cliente" style="min-width: 250px; border-right: 1px solid var(--os-border);">Cliente</th>`;
        let htmlHeader2 = `<tr>`;
        
        gerencial2Meses.forEach((m, i) => {
            const [ano, mes] = m.split('-');
            const borderLeft = "border-left: 2px solid #cbd5e1;";
            htmlHeader1 += `<th colspan="2" style="text-align: center; border-bottom: 1px solid var(--os-border); background-color: #f8fafc; ${borderLeft}">${mes}/${ano}</th>`;
            htmlHeader2 += `<th class="tar" style="${borderLeft}">Peso (kg)</th><th class="tar col-money">Valor (R$)</th>`;
        });
        
        htmlHeader1 += `</tr>`;
        htmlHeader2 += `</tr>`;
        
        tableHeaders.innerHTML = htmlHeader1 + htmlHeader2;
    }

    if (activeReport === "gerencial3") {
        const mesesSel = document.getElementById("filtro-gerencial3-meses");
        const qtdeMeses = mesesSel ? parseInt(mesesSel.value) : 12;
        gerencial3Meses = generateLastXMonths(qtdeMeses);
        
        let htmlHeader1 = `<tr>
            <th rowspan="2" style="width: 40px; min-width: 40px; border-right: 1px solid var(--os-border);">#</th>
            <th rowspan="2" data-sort="codigo_cliente" style="min-width: 100px; border-right: 1px solid var(--os-border);">Cód. Cliente</th>
            <th rowspan="2" data-sort="cliente" style="min-width: 250px; border-right: 1px solid var(--os-border);">Cliente</th>
            <th rowspan="2" data-sort="data_ultima_compra_geral" style="min-width: 120px; border-right: 1px solid var(--os-border);">Data Última Compra</th>
            <th rowspan="2" data-sort="previsao_proxima_compra" style="min-width: 150px; border-right: 1px solid var(--os-border);">Previsão Próxima Compra</th>`;
        let htmlHeader2 = `<tr>`;
        
        gerencial3Meses.forEach((m, i) => {
            const [ano, mes] = m.split('-');
            const borderLeft = "border-left: 2px solid #cbd5e1;";
            htmlHeader1 += `<th colspan="2" style="text-align: center; border-bottom: 1px solid var(--os-border); background-color: #f8fafc; ${borderLeft}">${mes}/${ano}</th>`;
            htmlHeader2 += `<th class="tar" style="${borderLeft}">Peso (kg)</th><th class="tar col-money">Valor (R$)</th>`;
        });
        
        htmlHeader1 += `</tr>`;
        htmlHeader2 += `</tr>`;
        
        tableHeaders.innerHTML = htmlHeader1 + htmlHeader2;
    }"""

content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)


# Second part: render rows for gerencial3
pattern2 = r'        \}\);\n        tbody.innerHTML = html;\n    \}'

replacement2 = """        });
        tbody.innerHTML = html;
    }

    if (activeReport === "gerencial3") {
        listagemVendas.forEach((item, index) => {
            html += `<tr>
                <td style="border-right: 1px solid var(--os-border);">${index + 1}</td>
                <td style="border-right: 1px solid var(--os-border);">${item.codigo_cliente || "-"}</td>
                <td style="border-right: 1px solid var(--os-border);">${limparNomeCliente(item.cliente)}</td>
                <td style="border-right: 1px solid var(--os-border); text-align: center;">${fmtData(item.data_ultima_compra_geral)}</td>
                <td style="border-right: 1px solid var(--os-border); text-align: center;">${fmtData(item.previsao_proxima_compra)}</td>`;
            
            gerencial3Meses.forEach(m => {
                const borderLeft = "border-left: 2px solid #cbd5e1;";
                const p = item.meses?.[m]?.peso || 0;
                const v = item.meses?.[m]?.valor || 0;
                html += `<td class="tar" style="${borderLeft}">${fmtPeso(p).replace(' kg','')}</td><td class="tar col-money">${fmtMoney(v)}</td>`;
            });
            html += `</tr>`;
        });
        tbody.innerHTML = html;
    }"""

content = re.sub(pattern2, replacement2, content, count=1, flags=re.DOTALL)

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added gerencial3 rendering logic")
