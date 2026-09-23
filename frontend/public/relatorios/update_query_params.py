import re

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace the entire if/else block inside buscarDadosRelatorio:
# From:
#     if (activeReport === "gerencial") {
# ...
#     }
#     // Seleciona endpoint conforme relatório ativo

pattern = r'    if \(activeReport === "gerencial"\) \{.*?(?=    // Seleciona endpoint conforme relatório ativo)'

replacement = """    if (activeReport === "gerencial") {
        if (inGerencialCodigo.value) queryParams.append("codigo_cliente", inGerencialCodigo.value);
        if (inGerencialDoc.value) queryParams.append("cnpj_cpf", inGerencialDoc.value);
        if (inGerencialNome.value) queryParams.append("nome_cliente", inGerencialNome.value);
        if (selGerencialMun.value) queryParams.append("municipio", selGerencialMun.value);
        if (selGerencialVend.value) queryParams.append("vendedor", selGerencialVend.value);
        if (inGerencialDataInicio.value) queryParams.append("data_compra_inicio", inGerencialDataInicio.value);
        if (inGerencialDataFim.value) queryParams.append("data_compra_fim", inGerencialDataFim.value);
        if (inGerencialObs.value) queryParams.append("observacao", inGerencialObs.value);
        if (selGerencialStatus && selGerencialStatus.value) queryParams.append("status_cadastro", selGerencialStatus.value);
    } else if (activeReport === "gerencial2") {
        const inG2Cod = document.getElementById("filtro-gerencial2-codigo");
        const inG2Nome = document.getElementById("filtro-gerencial2-nome");
        const selG2Meses = document.getElementById("filtro-gerencial2-meses");
        
        if (inG2Cod && inG2Cod.value) queryParams.append("codigo_cliente", inG2Cod.value);
        if (inG2Nome && inG2Nome.value) queryParams.append("nome_cliente", inG2Nome.value);
        if (selG2Meses && selG2Meses.value) queryParams.append("meses", selG2Meses.value);
    } else if (activeReport === "gerencial3") {
        txtTitulo.textContent = "Relatório Gerencial 3";
        tableHeaders.innerHTML = ""; // Será preenchido na renderização, igual ao gerencial2

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

        if (inG3Cod && inG3Cod.value) queryParams.append("codigo_cliente", inG3Cod.value);
        if (inG3Nome && inG3Nome.value) queryParams.append("nome_cliente", inG3Nome.value);
        if (selG3Meses && selG3Meses.value) queryParams.append("meses", selG3Meses.value);
        if (selG3Filial && selG3Filial.value) queryParams.append("filial", selG3Filial.value);
        if (selG3Categoria && selG3Categoria.value) queryParams.append("categoria", selG3Categoria.value);
        if (selG3Vendedor && selG3Vendedor.value) queryParams.append("vendedor", selG3Vendedor.value);
        if (selG3Municipio && selG3Municipio.value) queryParams.append("municipio", selG3Municipio.value);
        if (inG3RotaG && inG3RotaG.value) queryParams.append("rota_principal", inG3RotaG.value);
        if (inG3RotaA && inG3RotaA.value) queryParams.append("rota_aproximacao", inG3RotaA.value);
        if (selG3Status && selG3Status.value) queryParams.append("status_cadastro", selG3Status.value);
        if (selG3TipoEntrega && selG3TipoEntrega.value) queryParams.append("tipo_entrega", selG3TipoEntrega.value);
    } else {
        if (inDataInicio.value) queryParams.append("data_inicio", inDataInicio.value);
        if (inDataFim.value) queryParams.append("data_fim", inDataFim.value);
        if (inFaturamentoInicio.value) queryParams.append("faturamento_inicio", inFaturamentoInicio.value);
        if (inFaturamentoFim.value) queryParams.append("faturamento_fim", inFaturamentoFim.value);
        if (selFilial && selFilial.value) queryParams.append("filiais", selFilial.value);
        if (selCategoria && selCategoria.value) queryParams.append("categoria", selCategoria.value);
        if (selStatus.value) queryParams.append("status_list", selStatus.value);
        if (selMunicipio && selMunicipio.value) queryParams.append("municipios", selMunicipio.value);
        if (activeReport === "produto" && selGrupo.value) queryParams.append("grupos", selGrupo.value);
    }

"""

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated query parameters logic in JS")
