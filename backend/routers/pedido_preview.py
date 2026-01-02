from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from database import SessionLocal
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from services.email_service import enviar_email_notificacao
from services.pdf_service import gerar_pdf_pedido
from services.pedido_pdf_data import carregar_pedido_pdf
from types import SimpleNamespace
import json
import os
import logging
from schemas.pedido_confirmacao import ConfirmarPedidoRequest
from services.pedido_confirmacao_service import criar_pedido_confirmado

router = APIRouter(prefix="/pedido", tags=["Pedido"])
TZ = ZoneInfo("America/Sao_Paulo")

# ----- Models de resposta (shape que a tela pedido_cliente já consome) -----
class ProdutoPedidoPreview(BaseModel):
    codigo: str                # mapeado a partir de codigo_tabela (você chamou de codigo_supra no SELECT)
    nome: str
    embalagem: Optional[str] = None
    peso: Optional[float] = None
    condicao_pagamento: Optional[str] = None
    tabela_comissao: Optional[str] = None
    valor_sem_frete: float
    valor_com_frete: float
    valor_sem_frete_markup: Optional[float] = 0.0
    valor_com_frete_markup: Optional[float] = 0.0
    quantidade: int = 0
    markup: Optional[float] = 0.0 # NOVO

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
                codigo_plano_pagamento     AS plano_pagamento,
                descricao_fator_comissao   AS tabela_comissao,
                COALESCE(valor_frete, 0)   AS valor_com_frete,
                COALESCE(valor_s_frete, 0) AS valor_sem_frete,
                COALESCE(markup, 0)        AS markup,
                COALESCE(valor_final_markup, 0)   AS valor_final_markup,
                COALESCE(valor_s_frete_markup, 0) AS valor_s_frete_markup
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
            # ORIGINAL values (no overwrite)
            v_com = float(r.get("valor_com_frete") or 0.0)
            v_sem = float(r.get("valor_sem_frete") or 0.0)
            
            mk_pct = float(r.get("markup") or 0.0)
            
            # Markup values
            v_com_mk = float(r.get("valor_final_markup") or 0.0)
            v_sem_mk = float(r.get("valor_s_frete_markup") or 0.0)

            # If markup is 0 in DB, ensure we pass 0 or the normal price? 
            # Ideally passthrough 0 if not applied, let frontend handle fallback.
            # But user said "aparecer colunas preco normal + colunas markup".
            # If markup is 0, markup price == normal price.
            # providing specific markup fields allows frontend to decide.

            produtos.append(ProdutoPedidoPreview(
                codigo=str(r.get("codigo_supra") or ""),
                nome=r.get("nome") or "",
                embalagem=r.get("embalagem"),
                peso=float(r.get("peso") or 0.0),
                condicao_pagamento=r.get("plano_pagamento"),
                tabela_comissao=r.get("tabela_comissao"),
                valor_sem_frete=round(v_sem, 2),
                valor_com_frete=round(v_com, 2),
                valor_sem_frete_markup=round(v_sem_mk, 2),
                valor_com_frete_markup=round(v_com_mk, 2),
                quantidade=0,
                markup=mk_pct
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



@router.post("/{tabela_id}/confirmar")
def confirmar_pedido(tabela_id: int, body: ConfirmarPedidoRequest):
    with SessionLocal() as db:
        try:
            return criar_pedido_confirmado(db, tabela_id, body)
        except ValueError as ve:
             raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
             logger.exception(f"Erro confirmar_pedido: {e}")
             raise HTTPException(status_code=500, detail="Erro interno ao confirmar pedido")
