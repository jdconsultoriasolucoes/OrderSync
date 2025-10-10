# routers/pedido_preview.py
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Request, Depends
from pydantic import BaseModel, constr, conlist
from typing import Optional, List
from sqlalchemy import text
from database import SessionLocal  
from datetime import datetime
from sqlalchemy.orm import Session
import json

router = APIRouter(prefix="/pedido", tags=["Pedido"])

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
                SELECT code, tabela_id, com_frete, expires_at, data_prevista
                  FROM tb_pedido_link
                 WHERE code = :c
            """), {"c": body.origin_code}).mappings().first()

            if not link_row:
                raise HTTPException(status_code=404, detail="Link não encontrado")
            if link_row["expires_at"] and datetime.utcnow() > link_row["expires_at"]:
                raise HTTPException(status_code=410, detail="Link expirado")
            if int(link_row["tabela_id"]) != int(tabela_id):
                raise HTTPException(status_code=400, detail="Link e tabela não conferem")

            # força o com_frete do link
            body.usar_valor_com_frete = bool(link_row["com_frete"])

        # 3) Somar totais no servidor
        peso_total_kg = 0.0
        total_sem_frete = 0.0
        total_com_frete = 0.0
        for it in body.produtos:
            qtd = float(it.quantidade or 0)
            peso_total_kg += float(it.peso_kg or 0) * qtd
            total_sem_frete += float(it.preco_unit or 0) * qtd
            total_com_frete += float((it.preco_unit_com_frete if it.preco_unit_com_frete is not None else it.preco_unit) or 0) * qtd

        frete_total = max(0.0, total_com_frete - total_sem_frete)
        total_pedido = total_com_frete if body.usar_valor_com_frete else total_sem_frete

        # 4) Datas e campos
        def _parse_date(s: str | None):
            if not s:
                return None
            return datetime.strptime(s, "%Y-%m-%d").date()

        validade_ate = _parse_date(body.validade_ate)
        data_retirada = _parse_date(body.data_retirada) or (link_row["data_prevista"] if link_row else None)

        cliente_str = (body.cliente or "").strip() or "---"
        codigo_cliente = (f"LINK:{body.origin_code}" if body.origin_code else f"TABELA:{tabela_id}")[:80]
        observacao = (body.observacao or "").strip() or None
        agora = datetime.utcnow()

        link_expira_em = link_row["expires_at"] if link_row else None
        link_token = body.origin_code

        # 5) Insert
        insert_sql = text("""
            INSERT INTO tb_pedidos (
              codigo_cliente, cliente, tabela_preco_id,
              validade_ate, validade_dias, data_retirada,
              usar_valor_com_frete, itens,
              peso_total_kg, frete_total, total_sem_frete, total_com_frete, total_pedido,
              observacoes, status, confirmado_em,
              link_token, link_url, link_enviado_em, link_expira_em, link_status,
              criado_em, atualizado_em
            )
            VALUES (
              :codigo_cliente, :cliente, :tabela_preco_id,
              :validade_ate, NULL, :data_retirada,
              :usar_valor_com_frete, CAST(:itens AS jsonb),
              :peso_total_kg, :frete_total, :total_sem_frete, :total_com_frete, :total_pedido,
              :observacoes, 'CONFIRMADO', :confirmado_em,
              :link_token, NULL, :link_enviado_em, :link_expira_em, 'ABERTO',
              :agora, :agora
            )
            RETURNING id_pedido
        """)

        new_id = db.execute(insert_sql, {
            "codigo_cliente": codigo_cliente,
            "cliente": cliente_str,
            "tabela_preco_id": tabela_id,
            "validade_ate": validade_ate,
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
            "link_token": link_token,
            "link_enviado_em": agora,
            "link_expira_em": link_expira_em,
            "agora": agora
        }).scalar()

        db.commit()
        return {"id": new_id, "status": "CRIADO"}