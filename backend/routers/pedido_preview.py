# routers/pedido_preview.py
from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, constr
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
                codigo_supra      AS codigo_supra,      -- você pediu esse alias; vamos mapear para 'codigo' na resposta
                descricao_produto          AS nome,
                embalagem          AS embalagem,
                peso_liquido       AS peso,
                codigo_plano_pagamento    AS plano_pagamento,    -- vem da própria tabela
                COALESCE(valor_frete, 0)   AS valor_com_frete,
                COALESCE(valor_s_frete, 0) AS valor_sem_frete
                
            FROM tb_tabela_preco
            WHERE id_tabela = :tid AND ativo IS TRUE
            ORDER BY descricao_produto
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

        cond_pg = rows[0].get("codigo_plano_pagamento")  # (se quiser manter algo no cabeçalho, mas não vamos usá-lo)

        # 3) Validade: vem de /tabela_preco/meta/validade_global (chamado pelo front)
        

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
                condicao_pagamento=r.get("plano_pagamento"),
                valor_sem_frete=round(v_sem, 2),
                valor_com_frete=round(v_com, 2),
                quantidade=1
            ))

        return PedidoPreviewResp(
               tabela_id=tabela_id,
               razao_social=cliente,       # mesmo texto, como você pediu
               condicao_pagamento=None,    # agora a condição é exibida por item
               validade=None,         # front chama /tabela_preco/meta/validade_global
               tempo_restante=None,
               usar_valor_com_frete=com_frete,
               produtos=produtos
            )


class ConfirmarItem(BaseModel):
    codigo: str
    quantidade: int
    # adicione outros campos se necessários

class ConfirmarPedidoRequest(BaseModel):
    usar_valor_com_frete: Optional[bool] = None  # pode vir quando a origem é por tabela
    produtos: List[ConfirmarItem]
    observacao: Optional[constr(max_length=244)] = None

@router.post("/{tabela_id}/confirmar")
def confirmar_pedido(tabela_id: int, body: ConfirmarPedidoRequest):
    if not body.produtos:
        raise HTTPException(400, "Nenhum item informado")

    observacao = (body.observacao or "").strip()

    # TODO: criar cabeçalho em tb_pedido (id_cliente, tabela_id, usar_valor_com_frete, observacao, etc.)
    # TODO: inserir itens em tb_pedido_item
    # id_pedido = ...

    return {
      "ok": True,
      "tabela_id": tabela_id,
      "itens": len(body.produtos),
      "observacao": observacao
    }