from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
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
from services.tabela_preco import cliente_calcula_st
from services.fiscal import calcular_linha

router = APIRouter(prefix="/pedido", tags=["Pedido"])
logger = logging.getLogger(__name__)
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
    markup: Optional[float] = 0.0
    valor_frete_unitario: Optional[float] = 0.0
    manual_freight: Optional[bool] = False

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
        # Cabeçalho: cliente e código
        cabecalho_sql = text("""
            SELECT cliente, codigo_cliente
            FROM tb_tabela_preco
            WHERE id_tabela = :tid AND ativo IS TRUE
            LIMIT 1
        """)
        cab_row = db.execute(cabecalho_sql, {"tid": tabela_id}).mappings().first()
        cliente = cab_row.get("cliente") if cab_row else ""
        codigo_cliente = cab_row.get("codigo_cliente") if cab_row else None

        # Determina se calcula ST de forma robusta e baseada no cadastro
        aplica_st = cliente_calcula_st(db, codigo_cliente)

        itens_sql = text("""
            SELECT
                t.id_tabela,
                t.codigo_produto_supra       AS codigo_supra,
                t.descricao_produto          AS nome,
                t.embalagem                  AS embalagem,
                t.peso_liquido               AS peso,
                t.codigo_plano_pagamento     AS plano_pagamento,
                t.descricao_fator_comissao   AS tabela_comissao,
                COALESCE(t.valor_frete, 0)   AS valor_com_frete_original,
                COALESCE(t.valor_s_frete, 0) AS valor_sem_frete_original,
                COALESCE(t.markup, 0)        AS markup,
                COALESCE(t.valor_final_markup, 0)   AS valor_final_markup_original,
                COALESCE(t.valor_s_frete_markup, 0) AS valor_s_frete_markup_original,
                COALESCE(t.valor_frete_aplicado, 0) AS valor_frete_unitario,
                COALESCE(t.manual_freight, FALSE)   AS manual_freight,
                t.valor_produto,
                t.comissao_aplicada,
                t.ajuste_pagamento,
                COALESCE(p.tipo, '')         AS tipo_produto,
                COALESCE(i.ipi, 0.0)         AS tax_ipi,
                COALESCE(i.icms, 0.18)       AS tax_icms,
                COALESCE(i.iva_st, 0.0)      AS tax_iva_st
            FROM tb_tabela_preco t
            LEFT JOIN t_cadastro_produto_v2 p ON p.codigo_supra = t.codigo_produto_supra AND p.status_produto = 'ATIVO'
            LEFT JOIN t_imposto_v2 i ON i.produto_id = p.id
            WHERE t.id_tabela = :tid AND t.ativo IS TRUE
            ORDER BY t.descricao_produto
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
            valor_base = float(r.get("valor_produto") or 0.0)
            comissao = float(r.get("comissao_aplicada") or 0.0)
            ajuste = float(r.get("ajuste_pagamento") or 0.0)
            frete_unit = float(r.get("valor_frete_unitario") or 0.0)
            
            # Preço fiscal unitário = (valor - comissao) + ajuste
            preco_fiscal_unit = max(0.0, valor_base - comissao) + ajuste
            
            # Alíquotas
            tipo_prod = str(r.get("tipo_produto") or "").strip().lower()
            is_pet = (tipo_prod == "pet" or tipo_prod == "insumos")
            peso_liq = float(r.get("peso") or 0.0)
            
            ipi_rate = float(r.get("tax_ipi") or 0.0) if (is_pet and peso_liq <= 10) else 0.0
            icms_rate = float(r.get("tax_icms") or 0.18)
            iva_st_rate = float(r.get("tax_iva_st") or 0.0)
            
            # Lógica fiscal em tempo de execução
            res_fiscal = calcular_linha(
                preco_unit=preco_fiscal_unit,
                quantidade=1,
                desconto_linha=0,
                frete_linha=frete_unit,
                ipi=ipi_rate,
                icms=icms_rate,
                iva_st=iva_st_rate,
                aplica_st=aplica_st
            )
            
            # Totais recalculados
            total_comercial = float(res_fiscal["total_com_st"])
            total_sem_frete = max(0.0, total_comercial - frete_unit)
            
            markup_pct = float(r.get("markup") or 0.0)
            factor = 1.0 + (markup_pct / 100.0)
            
            val_com = total_comercial
            val_sem = total_sem_frete
            val_com_mk = total_comercial * factor
            val_sem_mk = total_sem_frete * factor

            produtos.append(ProdutoPedidoPreview(
                codigo=str(r.get("codigo_supra") or ""),
                nome=r.get("nome") or "",
                embalagem=r.get("embalagem"),
                peso=peso_liq,
                condicao_pagamento=r.get("plano_pagamento"),
                tabela_comissao=r.get("tabela_comissao"),
                valor_sem_frete=round(val_sem, 2),
                valor_com_frete=round(val_com, 2),
                valor_sem_frete_markup=round(val_sem_mk, 2),
                valor_com_frete_markup=round(val_com_mk, 2),
                quantidade=0,
                markup=markup_pct,
                valor_frete_unitario=frete_unit,
                manual_freight=bool(r.get("manual_freight") or False)
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



from fastapi import Request
from models.idempotency import IdempotencyKeyModel

from core.rate_limit import limiter

@router.post("/{tabela_id}/confirmar")
@limiter.limit("5/minute")
def confirmar_pedido(
    tabela_id: int, 
    body: ConfirmarPedidoRequest, 
    background_tasks: BackgroundTasks,
    request: Request
):
    idempotency_key = request.headers.get("x-idempotency-key")
    
    with SessionLocal() as db:
        try:
            # 1. Verifica Idempotência
            if idempotency_key:
                existente = db.query(IdempotencyKeyModel).filter(IdempotencyKeyModel.chave == idempotency_key).first()
                if existente:
                    # Retorna sucesso simulado com o ID já processado
                    return {
                        "id": existente.id_pedido,
                        "status": "CRIADO",
                        "email_enviado": False, # ou buscar o real se necessário
                        "pdf_base64": None,
                        "idempotency_cached": True
                    }

            # 2. Cria o pedido
            result = criar_pedido_confirmado(db, tabela_id, body, background_tasks)
            novo_id = result.get("id")

            # 3. Salva a chave de Idempotência
            if idempotency_key and novo_id:
                nova_chave = IdempotencyKeyModel(
                    chave=idempotency_key,
                    id_pedido=novo_id
                )
                db.add(nova_chave)

            db.commit()
            return result
        except Exception as e:
             db.rollback()
             # Raise it again so our global exception_handler in main.py wraps it inside the JSON structure
             raise e
