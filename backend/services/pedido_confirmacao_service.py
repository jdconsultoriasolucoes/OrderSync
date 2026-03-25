from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
import logging

from services.pdf_service import gerar_pdf_pedido
from services.email_service import enviar_email_notificacao
from services.pedido_pdf_data import carregar_pedido_pdf
from schemas.pedido_confirmacao import ConfirmarPedidoRequest
from fastapi import BackgroundTasks
from core.exceptions import BusinessRuleException, ValidationException

# Config Logger
logger = logging.getLogger("pedido_confirmacao_service")
TZ = ZoneInfo("America/Sao_Paulo")

def criar_pedido_confirmado(db: Session, tabela_id: int, body: ConfirmarPedidoRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    print(f"DEBUG: ConfirmarPedido - OriginCode: '{body.origin_code}' | Cliente: '{body.cliente}'")
    
    # 1) validação básica
    if not body.produtos:
        raise BusinessRuleException("Nenhum item informado no pedido")

    # ---  buscar fornecedor e nome da tabela de preço ---
    res_tabela = db.execute(text("""
        SELECT fornecedor, nome_tabela
        FROM public.tb_tabela_preco
        WHERE id_tabela = :tid
    """), {"tid": tabela_id}).mappings().first()

    if res_tabela:
        fornecedor = str(res_tabela["fornecedor"])[:255] if res_tabela["fornecedor"] else None
        tabela_nome_snapshot = str(res_tabela["nome_tabela"])[:255] if res_tabela["nome_tabela"] else None
    else:
        fornecedor = None
        tabela_nome_snapshot = None

    # ... (rest of logic) ...

    # 2) Get Link info
    link_row = None
    if body.origin_code:
        link_row = db.execute(text("""
            SELECT code, tabela_id, com_frete, expires_at, data_prevista, uses,
                   first_access_at, last_access_at, created_at, link_url, codigo_cliente
              FROM tb_pedido_link
             WHERE code = :c
        """), {"c": body.origin_code}).mappings().first()

        if not link_row:
            raise ValidationException("Link compartilhado não encontrado ou expirado", code="LINK_001")

        exp = link_row.get("expires_at")
        if exp is not None:
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=TZ)
            agora_sp = datetime.now(TZ)
            if agora_sp > exp:
                pass 

        if int(link_row["tabela_id"]) != int(tabela_id):
            raise BusinessRuleException("O Link fornecido não pertence a esta tabela de preço", code="LINK_002")

        # força o com_frete do link
        body.usar_valor_com_frete = bool(link_row["com_frete"])
        pedido_created_at = link_row["created_at"]
        link_url = link_row["link_url"]
    else:
        pedido_created_at = None
        link_url = None

    # 3) Somar totais no servidor
    peso_total_kg = 0.0
    total_sem_frete = 0.0
    total_com_frete = 0.0
    for it in body.produtos:
        qtd = float(it.quantidade or 0)
        peso_total_kg += float(it.peso_kg or 0) * qtd
        total_sem_frete += float(it.preco_unit or 0) * qtd
        total_com_frete += float(
            (it.preco_unit_com_frete if it.preco_unit_com_frete is not None else it.preco_unit) or 0
        ) * qtd

    frete_total = max(0.0, total_com_frete - total_sem_frete)
    total_pedido = total_com_frete if body.usar_valor_com_frete else total_sem_frete

    # 4) Datas e campos
    def _parse_date(s: str | None):
        if not s: return None
        try:
             return datetime.strptime(s, "%Y-%m-%d").date()
        except:
             return None

    validade_ate = _parse_date(body.validade_ate)
    validade_dias = body.validade_dias
    data_retirada = _parse_date(body.data_retirada) or (link_row["data_prevista"] if link_row else None)

    # 4.1) Validação de Data Retirada
    if data_retirada:
        hoje = datetime.now(TZ).date()
        if data_retirada < hoje:
            raise BusinessRuleException("A Data de Retirada não pode ser no passado (Data informada: " + data_retirada.strftime("%d/%m/%Y") + ")")

    codigo_cliente = (body.codigo_cliente or "").strip() or None
    if not codigo_cliente and link_row:
        c_link = link_row.get("codigo_cliente")
        if c_link and c_link.strip() and c_link != "Não cadastrado":
            codigo_cliente = c_link.strip()

    if not codigo_cliente or codigo_cliente == "Não cadastrado":
        try:
             row_tab = db.execute(text("SELECT codigo_cliente FROM tb_tabela_preco WHERE id_tabela = :tid"), {"tid": tabela_id}).mappings().first()
             if row_tab and row_tab["codigo_cliente"]:
                 codigo_cliente = str(row_tab["codigo_cliente"]).strip()
        except Exception as e:
             logger.error(f"Erro ao buscar codigo na tabela: {e}")

    observacao = (body.observacao or "").strip() or None
    agora = datetime.now(TZ)
    link_expira_em = link_row["expires_at"] if link_row else None

    # 5) Insert pedido
    insert_sql = text("""
        INSERT INTO tb_pedidos (
            codigo_cliente, cliente, tabela_preco_id, tabela_preco_nome,
            validade_ate, validade_dias, data_retirada,
            usar_valor_com_frete, itens,
            peso_total_kg, frete_total, total_sem_frete, total_com_frete, total_pedido,
            observacoes, status, confirmado_em,
            link_token, link_url, link_enviado_em, link_expira_em, link_status,
            link_primeiro_acesso_em, link_ultimo_acesso_em, link_qtd_acessos,
            fornecedor,          
            criado_em, atualizado_em, created_at
        )
        VALUES (
            :codigo_cliente, :cliente, :tabela_preco_id, :tabela_preco_nome,
            :validade_ate, :validade_dias, :data_retirada,
            :usar_valor_com_frete, CAST(:itens AS jsonb),
            :peso_total_kg, :frete_total, :total_sem_frete, :total_com_frete, :total_pedido,
            :observacoes, 'Orçamento', :confirmado_em,
            :link_token, :link_url, :link_enviado_em, :link_expira_em, 'ABERTO',
            :link_primeiro_acesso_em, :link_ultimo_acesso_em, :link_qtd_acessos,
            :fornecedor,         
            :agora, :agora, :pedido_created_at
        )
        RETURNING id_pedido
    """)

    params = {
        "codigo_cliente": (codigo_cliente or "Não cadastrado")[:80],
        "cliente": (body.cliente or "").strip() or "---",
        "tabela_preco_id": tabela_id,
        "tabela_preco_nome": tabela_nome_snapshot,
        "validade_ate": validade_ate,
        "validade_dias": validade_dias,
        "data_retirada": data_retirada,
        "usar_valor_com_frete": bool(body.usar_valor_com_frete),
        "itens": json.dumps([i.dict() for i in body.produtos]),
        "peso_total_kg": round(peso_total_kg, 3),
        "frete_total": round(frete_total, 2),
        "total_sem_frete": round(total_sem_frete, 2),
        "total_com_frete": round(total_com_frete, 2),
        "total_pedido": round(total_pedido, 2),
        "observacoes": observacao,
        "confirmado_em": agora,
        "link_token": body.origin_code,
        "link_url": link_url,
        "link_enviado_em": agora,
        "link_expira_em": link_expira_em,
        "link_primeiro_acesso_em": link_row.get("first_access_at") if link_row else None,
        "link_ultimo_acesso_em": link_row.get("last_access_at") if link_row else None,
        "link_qtd_acessos": link_row.get("uses") if link_row else None,
        "fornecedor": fornecedor,
        "agora": agora,
        "pedido_created_at": (pedido_created_at),
    }

    new_id = db.execute(insert_sql, params).scalar()

    # 6) Insert itens
    insert_item_sql = text("""
        INSERT INTO tb_pedidos_itens (
            id_pedido, codigo, nome, embalagem, peso_kg,
            condicao_pagamento, tabela_comissao,
            preco_unit, preco_unit_frt, quantidade,
            subtotal_sem_f, subtotal_com_f
        ) VALUES (
            :id_pedido, :codigo, :nome, :embalagem, :peso_kg,
            :condicao_pagamento, :tabela_comissao,
            :preco_unit, :preco_unit_frt, :quantidade,
            :subtotal_sem_f, :subtotal_com_f
        )
    """)

    for it in body.produtos:
        qtd   = float(it.quantidade or 0)
        p_sem = float(it.preco_unit or 0)
        p_com = float((it.preco_unit_com_frete 
                        if it.preco_unit_com_frete is not None 
                        else it.preco_unit) or 0)

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
            "quantidade": qtd,
            "subtotal_sem_f": round(p_sem * qtd, 2),
            "subtotal_com_f": round(p_com * qtd, 2),
        })

    db.commit()

    # 7) Monta um "pedido" mínimo só para o serviço de e-mail
    # Fetch customer email for the "Client Copy" feature
    from services.email_service import get_email_cliente_responsavel_compras
    print(f"DEBUG: CriarPedido - Buscando email inicial para codigo: '{codigo_cliente}'")
    client_email_addr = get_email_cliente_responsavel_compras(db, codigo_cliente)

    class PedidoEmailDummy:
        def __init__(self, id_pedido, codigo_cliente, cliente_nome, total_pedido, cliente_email):
            self.id = id_pedido
            self.codigo_cliente = codigo_cliente
            self.cliente_nome = cliente_nome
            self.total_pedido = total_pedido
            self.cliente_email = cliente_email

    pedido_email = PedidoEmailDummy(
        id_pedido=new_id,
        codigo_cliente=codigo_cliente,
        cliente_nome=(body.cliente or "").strip() or "---",
        total_pedido=round(total_pedido, 2),
        cliente_email=client_email_addr
    )

    email_agendado = False  # será True se a tarefa foi enfileirada com sucesso
    pdf_bytes_cliente = None
    EMAIL_MODE = os.getenv("ORDERSYNC_EMAIL_MODE", "best-effort").lower()
    
    if EMAIL_MODE == "off":
        # Apenas marca o pedido como "link desabilitado" e segue a vida
        db.execute(text("""
            UPDATE public.tb_pedidos
               SET link_status = 'DESABILITADO',
                   atualizado_em = :agora
             WHERE id_pedido = :id
        """), {"agora": agora, "id": new_id})
        db.commit()
    else:
        try:
            # Em vez de bloquear o request ou usar fila em memória, 
            # delegamos para a nossa tabela worker fazer tudo (Gerar PDF e SMTP)
            from models.background_task import BackgroundTaskModel
            
            nova_tarefa = BackgroundTaskModel(
                tipo_tarefa="ENVIO_EMAIL_CONFIRMACAO",
                referencia_id=new_id,
                status="PENDENTE",
                tentativas=0
            )
            db.add(nova_tarefa)
            db.commit()
            
            # Sinaliza que o e-mail foi agendado com sucesso
            # O worker irá enviá-lo em segundo plano
            email_agendado = True
            
        except Exception as queue_err:
            logging.exception("Falha ao colocar pedido %s na fila de email: %s", new_id, queue_err)

    # 9) resposta — com flag de email e PDF Base64
    # Usamos email_agendado (tarefa enfileirada) pois o e-mail é enviado de forma assíncrona
    # pelo worker. Na hora desta resposta, link_status ainda é 'ABERTO', então checar
    # link_status == 'ENVIADO' sempre retornaria False.
    email_enviado_cliente = email_agendado
    
    # Encode PDF to Base64 for immediate frontend download
    # USA O PDF DO CLIENTE (não do vendedor)
    pdf_b64 = None
    if pdf_bytes_cliente:
        import base64
        pdf_b64 = base64.b64encode(pdf_bytes_cliente).decode('utf-8')

    return {
        "id": new_id, 
        "status": "CRIADO", 
        "email_enviado": email_enviado_cliente,
        "pdf_base64": pdf_b64
    }
