import sys
import re

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add gerencial3 variables
if 'const inG3Cod = document.getElementById("filtro-gerencial3-codigo");' not in content:
    content = content.replace('// State', '''// Elementos Filtro Gerencial 3
const inG3Cod = document.getElementById("filtro-gerencial3-codigo");
const inG3Nome = document.getElementById("filtro-gerencial3-nome");
const selG3Meses = document.getElementById("filtro-gerencial3-meses");
const selG3Filial = document.getElementById("filtro-gerencial3-filial");
const selG3Categoria = document.getElementById("filtro-gerencial3-categoria");
const selG3Vendedor = document.getElementById("filtro-gerencial3-vendedor");
const selG3Municipio = document.getElementById("filtro-gerencial3-municipio");
const inG3RotaG = document.getElementById("filtro-gerencial3-rotag");
const inG3RotaA = document.getElementById("filtro-gerencial3-rotaa");
const selG3Status = document.getElementById("filtro-gerencial3-status");
const selG3TipoEntrega = document.getElementById("filtro-gerencial3-tipo-entrega");

// State''')

# 2. Add visibility logic
if 'if (rep === "gerencial3") {' not in content:
    content = content.replace('if (rep === "gerencial2") {', '''if (rep === "gerencial3") {
                document.querySelectorAll(".filtro-gerencial3").forEach(el => el.style.display = "");
            } else if (rep === "gerencial2") {''')

# 3. Add to headers logic
if 'else if (activeReport === "gerencial3") {' not in content:
    content = content.replace('else if (activeReport === "gerencial2") {', '''else if (activeReport === "gerencial3") {
        txtTitulo.textContent = "Relatório Gerencial 3";
        tableHeaders.innerHTML = ""; // Será preenchido na renderização, igual ao gerencial2
    } else if (activeReport === "gerencial2") {''')

# 4. Add query params
if 'else if (activeReport === "gerencial3") {' not in content:
    content = content.replace('else if (activeReport === "gerencial2") {', '''else if (activeReport === "gerencial3") {
        if (inG3Cod && inG3Cod.value) queryParams.append("codigo_cliente", inG3Cod.value);
        if (inG3Nome && inG3Nome.value) queryParams.append("nome_cliente", inG3Nome.value);
        if (selG3Meses && selG3Meses.value) queryParams.append("meses", selG3Meses.value);
        if (selG3Filial && selG3Filial.value) queryParams.append("filial", selG3Filial.value);
        if (selG3Categoria && selG3Categoria.value) queryParams.append("categoria", selG3Categoria.value);
        if (selG3Vendedor && selG3Vendedor.value) queryParams.append("vendedor", selG3Vendedor.value);
        if (selG3Municipio && selG3Municipio.value) queryParams.append("municipio", selG3Municipio.value);
        if (inG3RotaG && inG3RotaG.value) queryParams.append("rota_geral", inG3RotaG.value);
        if (inG3RotaA && inG3RotaA.value) queryParams.append("rota_aproximacao", inG3RotaA.value);
        if (selG3Status && selG3Status.value) queryParams.append("status_cadastro", selG3Status.value);
        if (selG3TipoEntrega && selG3TipoEntrega.value) queryParams.append("tipo_entrega", selG3TipoEntrega.value);
    } else if (activeReport === "gerencial2") {''')

# 5. Add endpoint mapping
if 'else if (activeReport === "gerencial3") endpoint = "gerencial3";' not in content:
    content = content.replace('else if (activeReport === "gerencial2") endpoint = "gerencial2";', '''else if (activeReport === "gerencial2") endpoint = "gerencial2";
    else if (activeReport === "gerencial3") endpoint = "gerencial3";''')

# 6. Generate inverted months for Gerencial 3
if 'let gerencial3Meses = [];' not in content:
    content = content.replace('let gerencial2Meses = [];', '''let gerencial2Meses = [];
let gerencial3Meses = [];''')

# 7. Render Table Headers
render_header_g3 = '''
    if (activeReport === "gerencial3") {
        const mesesSel = document.getElementById("filtro-gerencial3-meses");
        const qtdeMeses = mesesSel ? parseInt(mesesSel.value) : 12;
        gerencial3Meses = generateLastXMonths(qtdeMeses).reverse(); // INVERTIDO!
        
        let htmlHeader1 = `<tr>
            <th rowspan="2" style="width: 40px; min-width: 40px; border-right: 1px solid var(--os-border);">#</th>
            <th rowspan="2" data-sort="codigo_cliente" style="min-width: 100px; border-right: 1px solid var(--os-border);">Cód. Cliente</th>
            <th rowspan="2" data-sort="cliente" style="min-width: 250px; border-right: 1px solid var(--os-border);">Cliente</th>
            <th rowspan="2" data-sort="data_ultima_compra_geral" style="min-width: 130px; border-right: 1px solid var(--os-border);">Última Compra</th>
            <th rowspan="2" data-sort="previsao_proxima_compra" style="min-width: 130px; border-right: 1px solid var(--os-border);">Próxima Compra</th>`;
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
    }
'''
if 'if (activeReport === "gerencial3") {' not in content.split('function renderizarTabela()')[1]:
    content = content.replace('if (activeReport === "gerencial2") {', render_header_g3 + '\n    if (activeReport === "gerencial2") {')

# 8. Render Table Rows
render_row_g3 = '''
    } else if (activeReport === "gerencial3") {
        listagemVendas.forEach((item, index) => {
            html += `<tr>
                <td style="text-align: center; border-right: 1px solid var(--os-border);">${index + 1}</td>
                <td style="border-right: 1px solid var(--os-border);">${item.codigo_cliente}</td>
                <td style="border-right: 1px solid var(--os-border);">${item.cliente || "-"}</td>
                <td style="border-right: 1px solid var(--os-border);">${fmtData(item.data_ultima_compra_geral)}</td>
                <td style="border-right: 1px solid var(--os-border);">${fmtData(item.previsao_proxima_compra)}</td>
            `;
            gerencial3Meses.forEach(m => {
                const borderLeft = "border-left: 2px solid #cbd5e1;";
                const p = item.meses?.[m]?.peso || 0;
                const v = item.meses?.[m]?.valor || 0;
                totalPeso += p;
                totalComFrete += v; // Total geral
                html += `<td class="tar" style="${borderLeft}">${fmtPeso(p)}</td><td class="tar col-money">${fmtMoney(v)}</td>`;
            });
            html += `</tr>`;
        });
'''
if '} else if (activeReport === "gerencial3") {' not in content.split('let totalComFrete = 0;')[1]:
    content = content.replace('} else if (activeReport === "gerencial2") {', render_row_g3 + '} else if (activeReport === "gerencial2") {')

# 9. Clear filters
if 'if (inG3Cod) inG3Cod.value = "";' not in content:
    clear_g3 = '''
    if (inG3Cod) inG3Cod.value = "";
    if (inG3Nome) inG3Nome.value = "";
    if (selG3Filial) selG3Filial.value = "";
    if (selG3Categoria) selG3Categoria.value = "";
    if (selG3Vendedor) selG3Vendedor.value = "";
    if (selG3Municipio) selG3Municipio.value = "";
    if (inG3RotaG) inG3RotaG.value = "";
    if (inG3RotaA) inG3RotaA.value = "";
    if (selG3Status) selG3Status.value = "";
    if (selG3TipoEntrega) selG3TipoEntrega.value = "";
'''
    content = content.replace('await buscarDadosRelatorio();', clear_g3 + '\n    await buscarDadosRelatorio();')

# 10. Populate filters in init
pop_g3 = '''
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
'''
if 'if (dataG.vendedores && selG3Vendedor) {' not in content:
    content = content.replace('} catch (err) {', pop_g3 + '\n        } catch (err) {')
    
# 11. Populate filial and categoria logic is global, but selG3Filial must receive the same data as selFilial
pop_filial_g3 = '''
                    if (selG3Filial) {
                        const opt3 = document.createElement("option");
                        opt3.value = f;
                        opt3.textContent = f;
                        selG3Filial.appendChild(opt3);
                    }
'''
if 'if (selG3Filial) {' not in content:
    content = content.replace('selFilial.appendChild(opt);', 'selFilial.appendChild(opt);' + pop_filial_g3)


with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
