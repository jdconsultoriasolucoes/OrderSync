from models.pedido_pdf import PedidoPdf, PedidoPdfItem
from models.tabela_preco import TabelaPreco as TabelaModel
from datetime import datetime

def carregar_tabela_como_pdf_obj(db, tabela_id: int) -> PedidoPdf:
    itens_db = db.query(TabelaModel).filter_by(id_tabela=tabela_id, ativo=True).all()
    if not itens_db:
        raise ValueError("Tabela não encontrada ou vazia")

    cab = itens_db[0]
    
    # Calculate totals assuming Qty=1 for visualization
    total_valor = 0.0
    total_peso = 0.0
    
    itens_pdf = []
    for row in itens_db:
        # Pega valor com markup se existir, ou valor final normal
        # A lógica do front prioriza valor_final_markup
        val = float(row.valor_final_markup or 0)
        if val <= 0:
             val = float(row.valor_s_frete or 0) # Fallback? Or valor_produto?
             # Na tabela temos: valor_produto, valor_frete, valor_s_frete, valor_final_markup
        
        peso = float(row.peso_liquido or 0)
        
        total_valor += val
        total_peso += peso
        
        itens_pdf.append(PedidoPdfItem(
            codigo=str(row.codigo_produto_supra),
            produto=str(row.descricao_produto),
            embalagem=str(row.embalagem),
            quantidade=1.0, # Default for Price Table
            condicao_pagamento=str(row.codigo_plano_pagamento), # Contains desc? code usually
            tabela_comissao=str(row.descricao_fator_comissao or ""),
            valor_retira=float(row.valor_s_frete_markup or row.valor_s_frete or 0),
            valor_entrega=float(row.valor_final_markup or 0) # Assumindo Com Frete
        ))

    return PedidoPdf(
        id_pedido=tabela_id, # Reusing Table ID
        codigo_cliente=str(cab.codigo_cliente or ""),
        cliente=str(cab.cliente or ""),
        nome_fantasia=str(cab.cliente or ""),
        data_pedido=cab.criado_em or datetime.now(),
        data_entrega_ou_retirada=None,
        frete_total=0.0, # Not calculated in table
        frete_kg=float(cab.frete_kg or 0),
        validade_tabela="Verificar validade", 
        total_peso_bruto=total_peso,
        total_valor=total_valor,
        observacoes="Orçamento gerado a partir da Tabela de Preço.",
        itens=itens_pdf
    )
