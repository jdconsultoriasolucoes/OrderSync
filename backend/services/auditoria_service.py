import json
import logging
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.auditoria import LogisticaAuditoriaModel

logger = logging.getLogger("ordersync.errors")

def json_serializer(x):
    if isinstance(x, (datetime, date)):
        return x.isoformat()
    if isinstance(x, Decimal):
        return float(x)
    if isinstance(x, uuid.UUID):
        return str(x)
    if isinstance(x, bytes):
        return x.decode('utf-8', errors='ignore')
    return str(x)

def _garantir_tabela_auditoria(db: Session):
    try:
        with db.begin_nested():
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS public.tb_logistica_auditoria (
                    id SERIAL PRIMARY KEY,
                    tipo_operacao VARCHAR(50) NOT NULL,
                    id_original INTEGER NOT NULL,
                    numero_identificador VARCHAR(100),
                    data_criacao_original TIMESTAMP,
                    data_finalizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_responsavel VARCHAR(255),
                    snapshot_dados TEXT
                );
                CREATE INDEX IF NOT EXISTS ix_tb_logistica_auditoria_id ON public.tb_logistica_auditoria (id);
                CREATE INDEX IF NOT EXISTS ix_tb_logistica_auditoria_id_original ON public.tb_logistica_auditoria (id_original);
            """))
    except Exception:
        pass

def gerar_snapshot_carga(db: Session, carga_id: int, carga_model, carga_pedidos, usuario_email: str):
    try:
        _garantir_tabela_auditoria(db)
        
        # Pega detalhes da carga
        snapshot = {
            "carga": {
                "id": carga_model.id,
                "nome_carga": getattr(carga_model, "nome_carga", None),
                "numero_carga": getattr(carga_model, "numero_carga", None),
                "id_transporte": getattr(carga_model, "id_transporte", None),
                "data_carregamento": carga_model.data_carregamento.isoformat() if getattr(carga_model, "data_carregamento", None) else None,
                "is_retirada": getattr(carga_model, "is_retirada", None),
                "tipo_retirada": getattr(carga_model, "tipo_retirada", None)
            },
            "pedidos": []
        }
        
        for cp in carga_pedidos:
            num_ped = str(cp.numero_pedido).strip() if cp.numero_pedido is not None else ""
            if not num_ped.isdigit():
                continue
                
            ped_id = int(num_ped)
            # Buscar dados do pedido
            ped = db.execute(text("""
                SELECT 
                    id_pedido, 
                    status, 
                    codigo_cliente, 
                    cliente,
                    COALESCE(total_pedido, total_com_frete, total_sem_frete, 0) AS total,
                    total_pedido,
                    total_com_frete,
                    total_sem_frete,
                    peso_total_kg,
                    COALESCE(confirmado_em, created_at) AS data_emissao,
                    confirmado_em,
                    created_at
                FROM tb_pedidos 
                WHERE id_pedido = :id
            """), {"id": ped_id}).mappings().first()
            
            # Buscar itens do pedido
            itens = db.execute(text("""
                SELECT 
                    id_item, 
                    id_pedido, 
                    codigo, 
                    COALESCE(nome, '') AS descricao,
                    nome,
                    quantidade, 
                    COALESCE(preco_unit_frt, preco_unit, 0) AS valor_unitario,
                    preco_unit,
                    preco_unit_frt,
                    COALESCE(subtotal_com_f, subtotal_sem_f, 0) AS valor_total,
                    subtotal_com_f,
                    subtotal_sem_f
                FROM tb_pedidos_itens 
                WHERE id_pedido = :id
            """), {"id": ped_id}).mappings().all()
            
            if ped:
                ped_dict = dict(ped)
                ped_dict["itens"] = [dict(i) for i in itens]
                snapshot["pedidos"].append(ped_dict)
                
        snapshot_json = json.dumps(snapshot, default=json_serializer)
        
        auditoria = LogisticaAuditoriaModel(
            tipo_operacao="CARGA",
            id_original=carga_model.id,
            numero_identificador=getattr(carga_model, "numero_carga", None) or str(carga_model.id),
            data_criacao_original=getattr(carga_model, "data_criacao", None),
            usuario_responsavel=usuario_email,
            snapshot_dados=snapshot_json
        )
        db.add(auditoria)
    except Exception as e:
        logger.error(f"[AUDITORIA] Erro ao gerar snapshot da carga {carga_id}: {e}", exc_info=True)

def gerar_snapshot_retirada(db: Session, retirada_id: int, retirada_model, retirada_pedidos, usuario_email: str):
    try:
        _garantir_tabela_auditoria(db)
        
        snapshot = {
            "retirada": {
                "id": retirada_model.id,
                "nome_retirada": getattr(retirada_model, "nome_retirada", None),
                "numero_retirada": getattr(retirada_model, "numero_retirada", None),
                "data_retirada": retirada_model.data_retirada.isoformat() if getattr(retirada_model, "data_retirada", None) else None,
            },
            "pedidos": []
        }
        
        for rp in retirada_pedidos:
            num_ped = str(rp.numero_pedido).strip() if rp.numero_pedido is not None else ""
            if not num_ped.isdigit():
                continue
                
            ped_id = int(num_ped)
            ped = db.execute(text("""
                SELECT 
                    id_pedido, 
                    status, 
                    codigo_cliente, 
                    cliente,
                    COALESCE(total_pedido, total_com_frete, total_sem_frete, 0) AS total,
                    total_pedido,
                    total_com_frete,
                    total_sem_frete,
                    peso_total_kg,
                    COALESCE(confirmado_em, created_at) AS data_emissao,
                    confirmado_em,
                    created_at
                FROM tb_pedidos 
                WHERE id_pedido = :id
            """), {"id": ped_id}).mappings().first()
            
            itens = db.execute(text("""
                SELECT 
                    id_item, 
                    id_pedido, 
                    codigo, 
                    COALESCE(nome, '') AS descricao,
                    nome,
                    quantidade, 
                    COALESCE(preco_unit_frt, preco_unit, 0) AS valor_unitario,
                    preco_unit,
                    preco_unit_frt,
                    COALESCE(subtotal_com_f, subtotal_sem_f, 0) AS valor_total,
                    subtotal_com_f,
                    subtotal_sem_f
                FROM tb_pedidos_itens 
                WHERE id_pedido = :id
            """), {"id": ped_id}).mappings().all()
            
            if ped:
                ped_dict = dict(ped)
                ped_dict["itens"] = [dict(i) for i in itens]
                snapshot["pedidos"].append(ped_dict)
                
        snapshot_json = json.dumps(snapshot, default=json_serializer)
        
        auditoria = LogisticaAuditoriaModel(
            tipo_operacao="RETIRADA",
            id_original=retirada_model.id,
            numero_identificador=getattr(retirada_model, "numero_retirada", None) or str(retirada_model.id),
            data_criacao_original=getattr(retirada_model, "data_criacao", None),
            usuario_responsavel=usuario_email,
            snapshot_dados=snapshot_json
        )
        db.add(auditoria)
    except Exception as e:
        logger.error(f"[AUDITORIA] Erro ao gerar snapshot da retirada {retirada_id}: {e}", exc_info=True)

