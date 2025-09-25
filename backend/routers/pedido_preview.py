# routers/pedido_preview.py
from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import text
from database import SessionLocal  

router = APIRouter(prefix="/pedido", tags=["Pedido"])

# ----- Models de resposta (shape que a tela pedido_cliente já consome) -----
class ProdutoPedidoPreview(BaseModel):
    codigo: str                # mapeado a partir de codigo_tabela (você chamou de codigo_supra no SELECT)
    nome: str
    embalagem: Optional[str] = None
    peso: Optional[float] = None
    valor_sem_frete: float
    valor_com_frete: float
    quantidade: int = 0

class PedidoPreviewResp(BaseModel):
    tabela_id: int
    cnpj: Optional[str] = None
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
    cnpj: Optional[str] = Query(None),
    razao_social: Optional[str] = Query(None),
    condicao_pagamento: Optional[str] = Query(None),
):
    """
    Monta o payload de preview do pedido para a tela pedido_cliente:
    - Validade: vem do endpoint validade_global
    - Condição de pagamento: vem da própria tabela (plano_pagamento)
    - Valores: usa valor_frete / valor_s_frete (novas colunas)
    """
    with SessionLocal() as db:
        # 1) Itens (somente colunas necessárias), conforme sua especificação:
        itens_sql = text("""
            SELECT
                id_tabela,                               -- cabeçalho (retornamos como tabela_id)
                codigo_tabela      AS codigo_supra,      -- você pediu esse alias; vamos mapear para 'codigo' na resposta
                descricao          AS nome,
                embalagem          AS embalagem,
                peso_liquido       AS peso,
                valor_frete        AS valor_com_frete,   -- NOVA coluna (precisa existir no banco)
                valor_s_frete      AS valor_sem_frete,   -- NOVA coluna (precisa existir no banco)
                plano_pagamento    AS plano_pagamento    -- vem da própria tabela
            FROM tb_tabela_preco
            WHERE id_tabela = :tid AND ativo IS TRUE
            ORDER BY descricao
        """)
        try:
            rows = db.execute(itens_sql, {"tid": tabela_id}).mappings().all()
        except Exception as e:
            # Tipicamente vai cair aqui se as colunas novas ainda não existem.
            raise HTTPException(
                status_code=500,
                detail=f"Falha ao consultar itens da tabela {tabela_id}: {str(e)}. "
                       f"Verifique se as colunas 'valor_frete' e 'valor_s_frete' já foram criadas."
            )
        if not rows:
            raise HTTPException(status_code=404, detail="Tabela sem itens ou não encontrada")

        # 2) Condição de pagamento
        #    Se vier no link, usa a do link. Caso contrário, usa a do primeiro item (todas devem estar consistentes).
        cond_pg = condicao_pagamento or rows[0].get("plano_pagamento")

        # 3) Validade: via endpoint validade_global
        validade, tempo_restante = await _get_validade_global(tabela_id)

        # 4) Montar lista de produtos no shape do front
        produtos: List[ProdutoPedidoPreview] = []
        for r in rows:
            # Mapeia codigo_supra -> codigo (mantém compatibilidade com a tela)
            codigo = str(r.get("codigo_supra") or "")
            nome = r.get("nome") or ""
            embalagem = r.get("embalagem")
            peso = float(r.get("peso") or 0.0)
            v_sem = float(r.get("valor_sem_frete") or 0.0)
            v_com = float(r.get("valor_com_frete") or 0.0)

            produtos.append(ProdutoPedidoPreview(
                codigo=codigo,
                nome=nome,
                embalagem=embalagem,
                peso=peso,
                valor_sem_frete=round(v_sem, 2),
                valor_com_frete=round(v_com, 2),
                quantidade=0
            ))

        return PedidoPreviewResp(
               tabela_id=tabela_id,
               cnpj=cnpj,
               razao_social=razao_social,
               condicao_pagamento=cond_pg,
               validade=None,         # front chama /tabela_preco/meta/validade_global
               tempo_restante=None,
               usar_valor_com_frete=com_frete,
               produtos=produtos
            )
