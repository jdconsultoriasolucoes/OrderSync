import os

file_path = r"e:\OrderSync\backend\routers\pedidos.py"

endpoint_code = """
# ---------- Criação de Pedido Manual (Admin/Vendedor) ----------
from pydantic import BaseModel, Field

class AdminCriarPedidoItem(BaseModel):
    codigo: str
    descricao: Optional[str] = None
    embalagem: Optional[str] = None
    condicao_pagamento: Optional[str] = None
    tabela_comissao: Optional[str] = None
    quantidade: float
    preco_unit: float
    preco_unit_com_frete: Optional[float] = None
    peso_kg: float
    markup: Optional[float] = 0.0
    valor_frete_unitario: Optional[float] = 0.0

class AdminCriarPedidoRequest(BaseModel):
    cliente: str
    codigo_cliente: str
    tabela_preco_id: Optional[str] = None
    observacao: Optional[str] = None
    usar_valor_com_frete: bool = True
    produtos: List[AdminCriarPedidoItem]

@router.post("/admin_criar")
def admin_criar_pedido(body: AdminCriarPedidoRequest, db: Session = Depends(get_db)):
    from models.pedido import PedidoModel
    from models.background_task import BackgroundTaskModel
    import json
    
    if not body.produtos:
        raise HTTPException(status_code=400, detail="Nenhum item informado no pedido")
        
    peso_total_kg = 0.0
    total_sem_frete = 0.0
    total_com_frete = 0.0

    for it in body.produtos:
        qtd = float(it.quantidade or 0)
        peso_total_kg += float(it.peso_kg or 0) * qtd
        total_sem_frete += float(it.preco_unit or 0) * qtd
        p_com = float((it.preco_unit_com_frete if it.preco_unit_com_frete is not None else it.preco_unit) or 0)
        total_com_frete += p_com * qtd

    frete_total = max(0.0, total_com_frete - total_sem_frete)
    total_pedido = total_com_frete if body.usar_valor_com_frete else total_sem_frete
    
    # Insert pedido
    agora = datetime.now()
    
    insert_sql = text(\"""
        INSERT INTO tb_pedidos (
            codigo_cliente, cliente, tabela_preco_id, tabela_preco_nome,
            usar_valor_com_frete, itens,
            peso_total_kg, frete_total, frete_kg, total_sem_frete, total_com_frete, total_pedido,
            observacoes, status, confirmado_em,
            link_status, link_enviado_em,
            criado_em, atualizado_em, created_at
        )
        VALUES (
            :codigo_cliente, :cliente, :tabela_preco_id, NULL,
            :usar_valor_com_frete, CAST(:itens AS jsonb),
            :peso_total_kg, :frete_total, 0, :total_sem_frete, :total_com_frete, :total_pedido,
            :observacoes, 'Orçamento', :confirmado_em,
            'ABERTO', :agora,
            :agora, :agora, :agora
        )
        RETURNING id_pedido
    \""")
    
    tid = body.tabela_preco_id if body.tabela_preco_id and str(body.tabela_preco_id).strip() else None
    
    params = {
        "codigo_cliente": body.codigo_cliente[:80],
        "cliente": body.cliente.strip(),
        "tabela_preco_id": int(tid) if tid and tid.isdigit() else None,
        "usar_valor_com_frete": body.usar_valor_com_frete,
        "itens": json.dumps([i.dict() for i in body.produtos]),
        "peso_total_kg": round(peso_total_kg, 3),
        "frete_total": round(frete_total, 2),
        "total_sem_frete": round(total_sem_frete, 2),
        "total_com_frete": round(total_com_frete, 2),
        "total_pedido": round(total_pedido, 2),
        "observacoes": body.observacao,
        "confirmado_em": agora,
        "agora": agora
    }
    
    new_id = db.execute(insert_sql, params).scalar()
    
    # Insert itens
    insert_item_sql = text(\"""
        INSERT INTO tb_pedidos_itens (
            id_pedido, codigo, nome, embalagem, peso_kg,
            condicao_pagamento, tabela_comissao,
            preco_unit, preco_unit_frt, valor_frete_unitario, quantidade,
            subtotal_sem_f, subtotal_com_f,
            markup
        ) VALUES (
            :id_pedido, :codigo, :nome, :embalagem, :peso_kg,
            :condicao_pagamento, :tabela_comissao,
            :preco_unit, :preco_unit_frt, :valor_frete_unitario, :quantidade,
            :subtotal_sem_f, :subtotal_com_f,
            :markup
        )
    \""")
    
    for it in body.produtos:
        qtd = float(it.quantidade or 0)
        p_sem = float(it.preco_unit or 0)
        p_com = float((it.preco_unit_com_frete if it.preco_unit_com_frete is not None else it.preco_unit) or 0)
        v_frete = float(it.valor_frete_unitario or round(p_com - p_sem, 2))
        
        db.execute(insert_item_sql, {
            "id_pedido": new_id,
            "codigo": (it.codigo or "")[:80],
            "nome": (it.descricao or "")[:255] or None,
            "embalagem": getattr(it, "embalagem", None),
            "peso_kg": float(it.peso_kg or 0),
            "condicao_pagamento": it.condicao_pagamento,
            "tabela_comissao": it.tabela_comissao,
            "preco_unit": round(p_sem, 2),
            "preco_unit_frt": round(p_com, 2),
            "valor_frete_unitario": v_frete,
            "quantidade": qtd,
            "subtotal_sem_f": round(p_sem * qtd, 2),
            "subtotal_com_f": round(p_com * qtd, 2),
            "markup": float(it.markup or 0.0)
        })
        
    db.commit()
    
    # Agendar envio do E-mail
    nova_tarefa = BackgroundTaskModel(
        tipo_tarefa="ENVIO_EMAIL_CONFIRMACAO",
        referencia_id=new_id,
        status="PENDENTE",
        tentativas=0
    )
    db.add(nova_tarefa)
    db.commit()
    
    return {
        "id_pedido": new_id,
        "status": "CRIADO"
    }
"""

with open(file_path, "a", encoding="utf-8") as f:
    f.write("\n" + endpoint_code)

print("Endpoint adicionado com sucesso.")
