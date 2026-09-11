import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.auditoria import LogisticaAuditoriaModel
from datetime import datetime

def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

def gerar_snapshot_carga(db: Session, carga_id: int, carga_model, carga_pedidos, usuario_email: str):
    # Pega detalhes da carga
    snapshot = {
        "carga": {
            "id": carga_model.id,
            "nome_carga": carga_model.nome_carga,
            "numero_carga": carga_model.numero_carga,
            "id_transporte": carga_model.id_transporte,
            "data_carregamento": carga_model.data_carregamento.isoformat() if carga_model.data_carregamento else None,
            "is_retirada": carga_model.is_retirada,
            "tipo_retirada": carga_model.tipo_retirada
        },
        "pedidos": []
    }
    
    for cp in carga_pedidos:
        if not cp.numero_pedido.isdigit():
            continue
            
        ped_id = int(cp.numero_pedido)
        # Buscar dados do pedido
        ped = db.execute(text("SELECT id_pedido, status, codigo_cliente, total, data_emissao FROM tb_pedidos WHERE id_pedido = :id"), {"id": ped_id}).mappings().first()
        
        # Buscar itens do pedido
        itens = db.execute(text("SELECT id_item, id_pedido, codigo, descricao, quantidade, valor_unitario, valor_total FROM tb_pedidos_itens WHERE id_pedido = :id"), {"id": ped_id}).mappings().all()
        
        if ped:
            ped_dict = dict(ped)
            ped_dict["itens"] = [dict(i) for i in itens]
            snapshot["pedidos"].append(ped_dict)
            
    snapshot_json = json.dumps(snapshot, default=datetime_handler)
    
    auditoria = LogisticaAuditoriaModel(
        tipo_operacao="CARGA",
        id_original=carga_model.id,
        numero_identificador=carga_model.numero_carga or str(carga_model.id),
        data_criacao_original=carga_model.data_criacao,
        usuario_responsavel=usuario_email,
        snapshot_dados=snapshot_json
    )
    db.add(auditoria)

def gerar_snapshot_retirada(db: Session, retirada_id: int, retirada_model, retirada_pedidos, usuario_email: str):
    snapshot = {
        "retirada": {
            "id": retirada_model.id,
            "nome_retirada": retirada_model.nome_retirada,
            "numero_retirada": retirada_model.numero_retirada,
            "data_retirada": retirada_model.data_retirada.isoformat() if retirada_model.data_retirada else None,
        },
        "pedidos": []
    }
    
    for rp in retirada_pedidos:
        if not rp.numero_pedido or not rp.numero_pedido.isdigit():
            continue
            
        ped_id = int(rp.numero_pedido)
        ped = db.execute(text("SELECT id_pedido, status, codigo_cliente, total, data_emissao FROM tb_pedidos WHERE id_pedido = :id"), {"id": ped_id}).mappings().first()
        itens = db.execute(text("SELECT id_item, id_pedido, codigo, descricao, quantidade, valor_unitario, valor_total FROM tb_pedidos_itens WHERE id_pedido = :id"), {"id": ped_id}).mappings().all()
        
        if ped:
            ped_dict = dict(ped)
            ped_dict["itens"] = [dict(i) for i in itens]
            snapshot["pedidos"].append(ped_dict)
            
    snapshot_json = json.dumps(snapshot, default=datetime_handler)
    
    auditoria = LogisticaAuditoriaModel(
        tipo_operacao="RETIRADA",
        id_original=retirada_model.id,
        numero_identificador=retirada_model.numero_retirada or str(retirada_model.id),
        data_criacao_original=retirada_model.data_criacao,
        usuario_responsavel=usuario_email,
        snapshot_dados=snapshot_json
    )
    db.add(auditoria)
