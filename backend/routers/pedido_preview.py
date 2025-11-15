from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from database import SessionLocal
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from services.email_service import enviar_email_notificacao
from services.pdf_service import gerar_pdf_pedido

from types import SimpleNamespace
import json
import os
import logging

router = APIRouter(prefix="/pedido", tags=["Pedido"])
TZ = ZoneInfo("America/Sao_Paulo")

# ----- Models de resposta (shape que a tela pedido_cliente já consome) -----
class ProdutoPedidoPreview(BaseModel):
    codigo: str                # mapeado a partir de codigo_tabela (você chamou de codigo_supra no SELECT)
    nome: str
    embalagem: Optional[str] = None
    peso: Optional[float] = None
    condicao_pagamento: Optional[str] = None
    valor_sem_frete: float
    valor_com_frete: float
    quantidade: int = 0

class PedidoPreviewResp(BaseModel):
    tabela_id: int
    razao_social: Optional[str] = None
    condicao_pagamento: Optional[str] = None
    validade: Optional[str] = None
    tempo_restante: Optional[str] = None
    usar_valor_com_frete: bool
    produtos: List[ProdutoPedidoPreview]

@router.get("/preview", response_model=PedidoPreviewResp)
async def pedido_preview(
    tabela_id: int = Query(..., description="ID da tabela de preço salva"),
    com_frete: bool = Query(..., description="true/false: decidir valor com ou sem frete"),
):
    with SessionLocal() as db:
        # Cabeçalho: cliente "como está no banco"
        cabecalho_sql = text("""
            SELECT cliente
            FROM tb_tabela_preco
            WHERE id_tabela = :tid
            LIMIT 1
        """)
        cliente = db.execute(cabecalho_sql, {"tid": tabela_id}).scalar() or ""

        itens_sql = text("""
            SELECT
                id_tabela,                               -- cabeçalho (retornamos como tabela_id)
                codigo_produto_supra       AS codigo_supra,
                descricao_produto          AS nome,
                embalagem                  AS embalagem,
                peso_liquido               AS peso,
                codigo_plano_pagamento     AS plano_pagamento,
                COALESCE(valor_frete, 0)   AS valor_com_frete,
                COALESCE(valor_s_frete, 0) AS valor_sem_frete
            FROM tb_tabela_preco
            WHERE id_tabela = :tid AND ativo IS TRUE
            ORDER BY descricao_produto
        """)
        try:
            rows = db.execute(itens_sql, {"tid": tabela_id}).mappings().all()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=(f"Falha ao consultar itens da tabela {tabela_id}: {str(e)}. "
                        f"Verifique se as colunas 'valor_frete' e 'valor_s_frete' já foram criadas.")
            )

        if not rows:
            raise HTTPException(status_code=404, detail="Tabela sem itens ou não encontrada")

        produtos: List[ProdutoPedidoPreview] = []
        for r in rows:
            produtos.append(ProdutoPedidoPreview(
                codigo=str(r.get("codigo_supra") or ""),
                nome=r.get("nome") or "",
                embalagem=r.get("embalagem"),
                peso=float(r.get("peso") or 0.0),
                condicao_pagamento=r.get("plano_pagamento"),
                valor_sem_frete=round(float(r.get("valor_sem_frete") or 0.0), 2),
                valor_com_frete=round(float(r.get("valor_com_frete") or 0.0), 2),
                quantidade=1,
            ))

        return PedidoPreviewResp(
            tabela_id=tabela_id,
            razao_social=cliente,
            condicao_pagamento=None,
            validade=None,
            tempo_restante=None,
            usar_valor_com_frete=com_frete,
            produtos=produtos,
        )

class ConfirmarItem(BaseModel):
    codigo: str
    descricao: str | None = None
    quantidade: int
    preco_unit: float | None = None
    preco_unit_com_frete: float | None = None
    peso_kg: float | None = None

class ConfirmarPedidoRequest(BaseModel):
    origin_code: str | None = None              # token do link /p/{code}
    usar_valor_com_frete: bool = True
    produtos: list[ConfirmarItem]
    observacao: str | None = None
    cliente: str | None = None                  # razão social mostrada
    validade_ate: str | None = None             # 'YYYY-MM-DD' (opcional)
    data_retirada: str | None = None            # 'YYYY-MM-DD' (opcional)
    validade_dias: int | None = None
    codigo_cliente: str | None = None
    link_url: str | None = None

@router.post("/{tabela_id}/confirmar")
def confirmar_pedido(tabela_id: int, body: ConfirmarPedidoRequest):
    with SessionLocal() as db:
        # 1) validação básica
        if not body.produtos:
            raise HTTPException(status_code=400, detail="Nenhum item informado")

        # 2) Validar o link do token (se veio)
        link_row = None
        if body.origin_code:
            link_row = db.execute(text("""
                SELECT code, tabela_id, com_frete, expires_at, data_prevista, uses,
                       first_access_at, last_access_at, created_at, link_url, codigo_cliente
                  FROM tb_pedido_link
                 WHERE code = :c
            """), {"c": body.origin_code}).mappings().first()

            if not link_row:
                raise HTTPException(status_code=404, detail="Link não encontrado")

            exp = link_row.get("expires_at")
            if exp is not None:
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=TZ)
                agora_sp = datetime.now(TZ)
                if agora_sp > exp:
                    raise HTTPException(status_code=410, detail="Link expirado")

            if int(link_row["tabela_id"]) != int(tabela_id):
                raise HTTPException(status_code=400, detail="Link e tabela não conferem")

            # força o com_frete do link
            body.usar_valor_com_frete = bool(link_row["com_frete"])
            pedido_created_at = link_row["created_at"]  # instante da geração do link
            link_url = link_row["link_url"]             # opcional

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
            if not s:
                return None
            return datetime.strptime(s, "%Y-%m-%d").date()

        validade_ate = _parse_date(body.validade_ate)
        validade_dias = body.validade_dias
        data_retirada = _parse_date(body.data_retirada) or (link_row["data_prevista"] if link_row else None)

        codigo_cliente = (body.codigo_cliente or "").strip() or None
        if link_row:
            link_url = link_row.get("link_url")
        else:
            link_url = None

        observacao = (body.observacao or "").strip() or None
        agora = datetime.now(TZ)
        link_expira_em = link_row["expires_at"] if link_row else None

        # 5) Insert pedido
        insert_sql = text("""
            INSERT INTO tb_pedidos (
                codigo_cliente, cliente, tabela_preco_id,
                validade_ate, validade_dias, data_retirada,
                usar_valor_com_frete, itens,
                peso_total_kg, frete_total, total_sem_frete, total_com_frete, total_pedido,
                observacoes, status, confirmado_em,
                link_token, link_url, link_enviado_em, link_expira_em, link_status,
                link_primeiro_acesso_em, link_ultimo_acesso_em, link_qtd_acessos,
                criado_em, atualizado_em, created_at
            )
            VALUES (
                :codigo_cliente, :cliente, :tabela_preco_id,
                :validade_ate, :validade_dias, :data_retirada,
                :usar_valor_com_frete, CAST(:itens AS jsonb),
                :peso_total_kg, :frete_total, :total_sem_frete, :total_com_frete, :total_pedido,
                :observacoes, 'CONFIRMADO', :confirmado_em,
                :link_token, :link_url, :link_enviado_em, :link_expira_em, 'ABERTO',
                :link_primeiro_acesso_em, :link_ultimo_acesso_em, :link_qtd_acessos,
                :agora, :agora, :pedido_created_at
            )
            RETURNING id_pedido
        """)

        params = {
            "codigo_cliente": (codigo_cliente or "Não cadastrado")[:80],
            "cliente": (body.cliente or "").strip() or "---",
            "tabela_preco_id": tabela_id,
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
            "agora": agora,
            "pedido_created_at": (link_row.get("created_at") if link_row else None),
        }

        new_id = db.execute(insert_sql, params).scalar()

        # 6) Insert itens
        insert_item_sql = text("""
            INSERT INTO tb_pedidos_itens (
                id_pedido, codigo, nome, embalagem, peso_kg,
                preco_unit, preco_unit_frt, quantidade,
                subtotal_sem_f, subtotal_com_f
            ) VALUES (
                :id_pedido, :codigo, :nome, :embalagem, :peso_kg,
                :preco_unit, :preco_unit_frt, :quantidade,
                :subtotal_sem_f, :subtotal_com_f
            )
        """)

        for it in body.produtos:
            qtd   = float(it.quantidade or 0)
            p_sem = float(it.preco_unit or 0)
            p_com = float((it.preco_unit_com_frete if it.preco_unit_com_frete is not None else it.preco_unit) or 0)

            db.execute(insert_item_sql, {
                "id_pedido": new_id,
                "codigo": (it.codigo or "")[:80],
                "nome": (getattr(it, "descricao", None) or "")[:255] or None,
                "embalagem": None,   # pode preencher depois se quiser
                "peso_kg": float(it.peso_kg or 0),
                "preco_unit": round(p_sem, 2),
                "preco_unit_frt": round(p_com, 2),
                "quantidade": qtd,
                "subtotal_sem_f": round(p_sem * qtd, 2),
                "subtotal_com_f": round(p_com * qtd, 2),
            })

        db.commit()

        # 7) Monta um "pedido" mínimo só para o serviço de e-mail
        class PedidoEmailDummy:
            """
            Objeto simples só para entregar para o email_service.
            Ele só precisa ter:
              - id
              - codigo_cliente
              - cliente_nome / nome_cliente
              - total_pedido
            """
            def __init__(self, id_pedido, codigo_cliente, cliente_nome, total_pedido):
                self.id = id_pedido
                self.codigo_cliente = codigo_cliente
                self.cliente_nome = cliente_nome
                self.total_pedido = total_pedido

        pedido_email = PedidoEmailDummy(
            id_pedido=new_id,
            codigo_cliente=codigo_cliente,
            cliente_nome=(body.cliente or "").strip() or "---",
            total_pedido=round(total_pedido, 2),
        )

        # 8) E-mail best-effort (com PDF)
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
                # Por enquanto NÃO gera PDF, manda só o e-mail
                pdf_bytes = None

                enviar_email_notificacao(
                    db=db,
                    pedido=pedido_email,
                    link_pdf=None,
                    pdf_bytes=pdf_bytes
                )

                # Se chegou até aqui sem exception, marca como ENVIADO
                db.execute(text("""
                    UPDATE public.tb_pedidos
                       SET link_enviado_em = :agora,
                           link_status     = 'ENVIADO',
                           atualizado_em   = :agora
                     WHERE id_pedido = :id
                """), {"agora": agora, "id": new_id})
                db.commit()
            except Exception as e:
                logging.exception("Falha ao enviar email (ignorada): %s", e)
                # limpa a transação antes de tentar o UPDATE
                db.rollback()
                db.execute(text("""
                    UPDATE public.tb_pedidos
                       SET link_status   = 'FALHA_ENVIO',
                           atualizado_em = :agora
                     WHERE id_pedido = :id
                """), {"agora": agora, "id": new_id})
                db.commit()

        # 9) resposta — SEM expor nada de e-mail
        return {"id": new_id, "status": "CRIADO"}