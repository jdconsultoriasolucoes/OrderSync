# services/produtos_v2_service.py
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from datetime import date

from models.produto import ProdutoV2, ImpostoV2
from schemas.produto import ProdutoV2Create, ProdutoV2Update, ImpostoV2Create, ProdutoV2Out, ImpostoV2Out

# ----------------------------
# Helpers
# ----------------------------
def _row_to_out(db: Session, row: Dict[str, Any], include_imposto: bool = True) -> ProdutoV2Out:
    data = dict(row)
    if include_imposto and "id" in data:
        imp = db.query(ImpostoV2).filter(ImpostoV2.produto_id == data["id"]).one_or_none()
        if imp:
            data["imposto"] = ImpostoV2Out.model_validate(imp)
    return ProdutoV2Out(**data)

def _validate_business(update: Dict[str, Any]):
    # já validamos no Pydantic; aqui reforçamos regra de datas (caso PATCH parcial sem fim chegar setado)
    ini = update.get("data_desconto_inicio")
    fim = update.get("data_desconto_fim")

    if (ini and not fim) or (fim and not ini):
        raise HTTPException(422, detail="Preencha data_desconto_inicio e data_desconto_fim juntos")
    if ini and fim and ini > fim:
        raise HTTPException(422, detail="data_desconto_inicio deve ser <= data_desconto_fim")

    for campo in ("preco", "preco_tonelada", "desconto_valor_tonelada"):
        v = update.get(campo)
        if v is not None and v < 0:
            raise HTTPException(422, detail=f"{campo} não pode ser negativo")

# ----------------------------
# CRUD via ORM + leitura pela VIEW
# ----------------------------
def create_produto(db, produto_in, imposto_in=None):
    try:
        # 1) INSERT produto base
        obj = ProdutoV2(**produto_in.dict(exclude_unset=True))
        db.add(obj)
        db.flush()  # garante obj.id

        # 2) imposto (opcional)
        if imposto_in:
            imp = ImpostoV2(produto_id=obj.id, **imposto_in.dict(exclude_unset=True))
            db.add(imp)

        db.commit()
        db.refresh(obj)

    except Exception as e:
        db.rollback()
        # logue o erro para saber a raiz:
        # print(f"[create_produto] commit error: {e}")
        raise

    # 3) Tentar montar o retorno pela VIEW (se existir)
    try:
        row = db.execute(
            text("SELECT * FROM v_produto_v2_preco WHERE id = :id"),
            {"id": obj.id},
        ).mappings().first()
        if row:
            return ProdutoV2Out(**row)
    except Exception as e:
        # print(f"[create_produto] view fallback: {e}")
        pass

    # 4) Fallback: monta resposta a partir do ORM (sem view)
    #    (ajuste os campos conforme seu schema)
    imposto_out = None
    if obj.imposto:  # relacionamento 1–1
        imposto_out = ImpostoV2Out.from_orm(obj.imposto)

    return ProdutoV2Out(
        id=obj.id,
        codigo_supra=obj.codigo_supra,
        status_produto=obj.status_produto,
        nome_produto=obj.nome_produto,
        tipo_giro=obj.tipo_giro,
        estoque_disponivel=obj.estoque_disponivel,
        unidade=obj.unidade,
        peso=obj.peso,
        peso_bruto=obj.peso_bruto,
        estoque_ideal=obj.estoque_ideal,
        embalagem_venda=obj.embalagem_venda,
        unidade_embalagem=obj.unidade_embalagem,
        codigo_ean=obj.codigo_ean,
        codigo_embalagem=obj.codigo_embalagem,
        ncm=obj.ncm,
        fornecedor=obj.fornecedor,
        filhos=obj.filhos,
        familia=obj.familia,
        preco=obj.preco,
        preco_tonelada=obj.preco_tonelada,
        validade_tabela=obj.validade_tabela,
        desconto_valor_tonelada=obj.desconto_valor_tonelada,
        data_desconto_inicio=obj.data_desconto_inicio,
        data_desconto_fim=obj.data_desconto_fim,
        # calculados ficam None se não vierem da view/trigger:
        preco_final=None,
        reajuste_percentual=None,
        vigencia_ativa=None,
        # imposto:
        imposto=imposto_out,
        # snapshots anteriores (se tiver no modelo, deixe None):
        unidade_anterior=None,
        preco_anterior=None,
        preco_tonelada_anterior=None,
        validade_tabela_anterior=None,
    )

def update_produto(db: Session, produto_id: int, payload: ProdutoV2Update, imposto: Optional[ImpostoV2Create]) -> ProdutoV2Out:
    obj = db.query(ProdutoV2).filter(ProdutoV2.id == produto_id).one_or_none()
    if not obj:
        raise HTTPException(404, detail="Produto não encontrado")

    update = payload.model_dump(exclude_unset=True)
    _validate_business(update)

    for k, v in update.items():
        setattr(obj, k, v)

    if imposto is not None:
        imp = db.query(ImpostoV2).filter(ImpostoV2.produto_id == produto_id).one_or_none()
        if imp:
            for k, v in imposto.model_dump(exclude_unset=True).items():
                setattr(imp, k, v)
        else:
            db.add(ImpostoV2(produto_id=produto_id, **imposto.model_dump(exclude_unset=True)))

    db.commit()

    row = db.execute(text("SELECT * FROM v_produto_v2_preco WHERE id = :id"), {"id": produto_id}).mappings().first()
    return _row_to_out(db, row)

def get_produto(db: Session, produto_id: int) -> ProdutoV2Out:
    row = db.execute(text("SELECT * FROM v_produto_v2_preco WHERE id = :id"), {"id": produto_id}).mappings().first()
    if not row:
        raise HTTPException(404, detail="Produto não encontrado")
    return _row_to_out(db, row)

def list_produtos(
    db: Session,
    q: Optional[str],
    status: Optional[str],
    familia: Optional[int],
    vigencia_em: Optional[date],
    limit: int,
    offset: int
) -> List[ProdutoV2Out]:
    base = "SELECT * FROM v_produto_v2_preco WHERE 1=1"
    params: Dict[str, Any] = {}

    if q:
        base += " AND (nome_produto ILIKE :q OR codigo_supra ILIKE :q)"
        params["q"] = f"%{q}%"
    if status:
        base += " AND status_produto = :status"
        params["status"] = status
    if familia is not None:
        base += " AND familia = :familia"
        params["familia"] = familia
    if vigencia_em:
        base += " AND validade_tabela <= :vig"
        params["vig"] = vigencia_em

    base += " ORDER BY id DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    rows = db.execute(text(base), params).mappings().all()
    return [_row_to_out(db, r, include_imposto=False) for r in rows]

def get_anteriores(db: Session, produto_id: int) -> Dict[str, Any]:
    # lê direto da tabela base (não da view)
    row = db.execute(text("""
        SELECT preco_anterior, unidade_anterior, preco_tonelada_anterior, validade_tabela_anterior
        FROM t_cadastro_produto_v2 WHERE id = :id
    """), {"id": produto_id}).mappings().first()
    if not row:
        raise HTTPException(404, detail="Produto não encontrado")
    return dict(row)
