import os
import re

file_path = r"e:\OrderSync\frontend\public\pedidos\criacao_pedido.js"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Qtde column in criarLinha
target_col = "const tdValor = document.createElement('td'); tdValor.className = 'num'; tdValor.textContent = fmtMoney(item.valor || 0);"
replacement_col = """
  const tdQtd = document.createElement('td');
  const inpQtd = document.createElement('input');
  inpQtd.type = 'number';
  inpQtd.className = 'os-input inp-qtd right';
  inpQtd.style.width = '80px';
  inpQtd.min = '1';
  inpQtd.value = item.quantidade || 1;
  item.quantidade = Number(inpQtd.value);
  inpQtd.addEventListener('input', () => {
      itens[idx].quantidade = Number(inpQtd.value) || 1;
      recalcTudo();
  });
  tdQtd.appendChild(inpQtd);

  const tdValor = document.createElement('td'); tdValor.className = 'num'; tdValor.textContent = fmtMoney(item.valor || 0);
"""
content = content.replace(target_col, replacement_col)

# 2. Add tdQtd to tr.append
target_append = "tdPeso, tdValor, tdPercent, tdDescAplic,"
replacement_append = "tdPeso, tdQtd, tdValor, tdPercent, tdDescAplic,"
content = content.replace(target_append, replacement_append)

# 3. Replace quantidade: 1 with quantidade: item.quantidade || 1
content = content.replace("quantidade: 1,", "quantidade: item.quantidade || 1,")

# 4. Modify calculate total in recalcTudo to include quantity multiplication!
# In the original, the item total is (item.valor_final_markup || item.valor_liquido || ...).
# Wait, if we use `quantidade`, it might be easier to just sum it correctly.
# Let's insert a block at the end of recalcTudo to update our HTML fields.
# We will find `if (typeof refreshToolbarEnablement === 'function') refreshToolbarEnablement();` which is near UI update.
# Actually let's just append to the bottom of the file a hook that overrides the update function.
# Wait, `recalcTudo` recalculates. I can inject a call to `atualizarResumoPedido()` at the end of `recalcTudo`.
# Let's search for the end of `recalcTudo`: 
# `function renderTabela() {` is around there, but `recalcTudo` is an async function. Let's just hook `recalcTudo`.
# I'll replace `function recalcTudo() {` with `async function originalRecalcTudo() {`, and then define a wrapper `async function recalcTudo() { await originalRecalcTudo(); atualizarResumoPedido(); }`
content = content.replace("async function recalcTudo() {", "async function originalRecalcTudo() {")

wrapper_recalc = """
async function recalcTudo() {
    await originalRecalcTudo();
    atualizarResumoPedido();
}

function atualizarResumoPedido() {
    let qtdTotal = 0;
    let pesoTotal = 0;
    let totalSF = 0;
    let totalCF = 0;

    itens.forEach(it => {
        const q = Number(it.quantidade || 1);
        qtdTotal += q;
        pesoTotal += (Number(it.peso_bruto || it.peso_liquido || 0)) * q;
        
        // As items have _totalComercial or final markup values which are PER UNIT
        const vSF = Number(it.valor_s_frete_markup || it.valor_s_frete || it.precoBase || it.valor || 0);
        const vCF = Number(it.valor_final_markup || it.valor_liquido || it.precoBase || it.valor || 0);
        
        totalSF += vSF * q;
        totalCF += vCF * q;
    });

    const elQtd = document.getElementById('resumo-qtd-itens');
    const elPeso = document.getElementById('resumo-peso');
    const elSF = document.getElementById('resumo-total-sf');
    const elCF = document.getElementById('resumo-total-cf');

    if (elQtd) elQtd.textContent = qtdTotal;
    if (elPeso) elPeso.textContent = fmt4(pesoTotal) + ' kg';
    if (elSF) elSF.textContent = fmtMoney(totalSF);
    if (elCF) elCF.textContent = fmtMoney(totalCF);
}
"""
content += "\n" + wrapper_recalc

# 5. Salvar Pedido button logic
salvar_pedido_logic = """
document.addEventListener('DOMContentLoaded', () => {
    const btnSalvar = document.getElementById('btn-salvar-pedido');
    if(btnSalvar) {
        btnSalvar.addEventListener('click', salvarPedido);
    }
    
    const btnCarregar = document.getElementById('btn-carregar-tabela');
    if(btnCarregar) {
        btnCarregar.addEventListener('click', carregarTabelaBase);
    }
});

async function carregarTabelaBase() {
    const id = document.getElementById('tabela_base_id')?.value;
    if(!id) return;
    
    try {
        document.body.style.cursor = 'wait';
        const r = await fetch(`${API_BASE}/tabela_preco/${id}`);
        if(!r.ok) throw new Error('Tabela não encontrada');
        const data = await r.json();
        
        // Copiar produtos
        if(data.produtos && data.produtos.length > 0) {
            itens = data.produtos.map(p => {
                const mapItem = mapBackendItemToFrontend(p, data.tabela || {});
                mapItem.quantidade = 1; // Default
                return mapItem;
            });
            renderTabela();
            await recalcTudo();
        }
        
        alert('Produtos da tabela carregados com sucesso!');
    } catch(err) {
        alert(err.message);
    } finally {
        document.body.style.cursor = 'default';
    }
}

async function salvarPedido() {
    if (!itens || itens.length === 0) {
        alert("Adicione produtos ao pedido.");
        return;
    }
    
    const cliente_nome = document.getElementById('cliente_nome')?.value || '';
    const codigo_cliente = document.getElementById('codigo_cliente')?.value || '';
    
    if (!codigo_cliente || codigo_cliente === "Não cadastrado") {
        alert("Atenção: É necessário selecionar um cliente válido para o envio da confirmação do pedido.");
        return;
    }

    const mkGlobal = Number(document.getElementById('markup_global')?.value || 0);
    const tblId = document.getElementById('tabela_base_id')?.value || null;
    const observacao = document.getElementById('observacao')?.value || '';

    const payload = {
        cliente: cliente_nome,
        codigo_cliente: codigo_cliente,
        tabela_preco_id: tblId, // Opcional
        observacao: observacao,
        usar_valor_com_frete: true,
        produtos: itens.map(it => {
            const q = Number(it.quantidade || 1);
            const vSF = Number(it.valor_s_frete_markup || it.valor_s_frete || it.precoBase || it.valor || 0);
            const vCF = Number(it.valor_final_markup || it.valor_liquido || it.precoBase || it.valor || 0);
            
            return {
                codigo: it.codigo_tabela,
                descricao: it.descricao,
                embalagem: it.embalagem,
                peso_kg: Number(it.peso_bruto || it.peso_liquido || 0),
                quantidade: q,
                preco_unit: vSF,
                preco_unit_com_frete: vCF,
                condicao_pagamento: it.plano_pagamento || null,
                tabela_comissao: it.__descricao_fator_label || null,
                markup: it.markup || mkGlobal || 0,
                valor_frete_unitario: Number(it.valor_frete_aplicado || 0)
            };
        })
    };

    try {
        btnSalvar = document.getElementById('btn-salvar-pedido');
        btnSalvar.disabled = true;
        btnSalvar.textContent = "Gerando...";

        const r = await fetch(`${API_BASE}/pedidos/admin_criar`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        if (!r.ok) {
            const err = await r.json();
            throw new Error(err.detail || 'Erro ao gerar pedido');
        }

        const res = await r.json();
        alert(`Pedido #${res.id_pedido} gerado com sucesso! Um e-mail com o PDF será enviado ao cliente.`);
        
        // Limpar tela
        itens = [];
        document.getElementById('cliente_nome').value = '';
        document.getElementById('codigo_cliente').value = '';
        renderTabela();
        atualizarResumoPedido();
        
    } catch(err) {
        alert(err.message);
    } finally {
        if(btnSalvar) {
            btnSalvar.disabled = false;
            btnSalvar.textContent = "Salvar e Gerar Pedido";
        }
    }
}
"""

content += "\n" + salvar_pedido_logic

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Modificações no JS concluídas com sucesso!")
