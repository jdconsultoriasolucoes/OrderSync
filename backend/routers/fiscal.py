from __future__ import annotations
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal
from services.fiscal import decide_st, calcular_linha, D, money, _norm

router = APIRouter(tags=["Fiscal"])

# --------- I/O ---------
class LinhaPreviewIn(BaseModel):
    cliente_codigo: Optional[int] = None
    forcar_iva_st: bool = False
    produto_id: str
    preco_unit: Decimal
    quantidade: Decimal
    desconto_linha: Decimal = Decimal("0.00")
    frete_linha: Decimal = Decimal("0.00")

    # novos (opcionais) — permitem fallback quando DB não tem dados
    ramo_juridico: Optional[str] = None
    peso_kg: Optional[Decimal] = None
    tipo: Optional[str] = None

    class Config:
        extra = "ignore"

class LinhaPreviewOut(BaseModel):
    aplica_iva_st: bool
    motivos_iva_st: List[str]

    subtotal_mercadoria: float
    base_ipi: float
    ipi: float
    base_icms_proprio: float
    icms_proprio: float
    base_st: float
    icms_st_cheio: float
    icms_st_reter: float

    desconto_linha: float
    frete_linha: float

    # Por padrão mantemos a UI usando o total SEM ST (como é comum hoje),
    # mas devolvemos também o COM ST para você poder alternar facilmente.
    total_linha: float             # = total_sem_st
    total_linha_com_st: float
    total_impostos_linha: float

# --------- DB session ---------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------- Data access (mesmas fontes dos seus endpoints) ---------
# ---- em routers/fiscal.py ----
def carregar_cliente(db: Session, codigo: Optional[int]) -> dict:
    if not codigo:
        return {}
    row = db.execute(text("""
        SELECT
          codigo,
          ramo_juridico
        FROM public.t_cadastro_cliente
        WHERE codigo = :cod
        LIMIT 1
    """), {"cod": codigo}).mappings().first()
    return dict(row) if row else {}



def carregar_produto(db: Session, produto_id: str) -> dict:
    try:
        row = db.execute(text("""
            SELECT
              b.codigo_supra,
              a.tipo,
              COALESCE(b.peso,   0)    AS peso_kg,   -- alias certo
              COALESCE(b.iva_st, 0)    AS iva_st,
              COALESCE(b.ipi,    0)    AS ipi,
              COALESCE(b.icms,   0.18) AS icms
            FROM public.t_familia_produtos a
            JOIN public.t_cadastro_produto b
              ON b.familia = a.id
            WHERE status_produto = 'ATIVO' and b.codigo_supra::text = :pid
            LIMIT 1
        """), {"pid": produto_id}).mappings().first()
    except Exception as e:
        print("ERRO carregar_produto:", repr(e))
        raise HTTPException(status_code=500, detail=f"Falha ao carregar produto: {repr(e)}")

    if not row:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return dict(row)

@router.post("/fiscal/preview-linha", response_model=LinhaPreviewOut)
def preview_linha(payload: LinhaPreviewIn, db: Session = Depends(get_db)):
   
    try:
        print("DBG payload:", payload.dict())

        cliente = carregar_cliente(db, payload.cliente_codigo)
        produto = carregar_produto(db, payload.produto_id)
       
        
        
        print("DBG cliente:", cliente)
        print("DBG produto:", produto)

        ramo_db = cliente.get("ramo_juridico") if cliente else None
        ramo = ramo_db or getattr(payload, "ramo_juridico", None)

        tipo = produto.get("tipo") or getattr(payload, "tipo", None)

        peso = produto.get("peso_kg") or getattr(payload, "peso_kg", None)
        peso = D(peso)
        ipi_prod = D(produto.get("ipi", 0))
        # nova regra:
        ipi = ipi_prod if (_norm(tipo) == "pet" and peso is not None and peso <= D(10)) else D(0)

        iva_st = D(produto.get("iva_st", 0))
        icms = D(produto.get("icms", 0.18))

        aplica, motivos = decide_st(
            tipo=tipo,
            ramo_juridico=ramo,
            forcar_iva_st=payload.forcar_iva_st
        )

        comp = calcular_linha(
            preco_unit=payload.preco_unit,
            quantidade=payload.quantidade,
            desconto_linha=payload.desconto_linha,
            frete_linha=payload.frete_linha,
            ipi=ipi, icms=icms, iva_st=iva_st,
            aplica_st=aplica
        )

        return LinhaPreviewOut(
            aplica_iva_st=aplica, motivos_iva_st=motivos,
            subtotal_mercadoria=float(comp["subtotal"]),
            base_ipi=float(comp["base_ipi"]), ipi=float(comp["ipi"]),
            base_icms_proprio=float(comp["base_icms"]), icms_proprio=float(comp["icms_proprio"]),
            base_st=float(comp["base_st"]), icms_st_cheio=float(comp["icms_st_cheio"]), icms_st_reter=float(comp["icms_st_reter"]),
            desconto_linha=float(money(payload.desconto_linha)), frete_linha=float(money(payload.frete_linha)),
            total_linha=float(comp["total_sem_st"]), total_linha_com_st=float(comp["total_com_st"]),
            total_impostos_linha=float(comp["total_impostos"])
        )
    except HTTPException:
        raise
    except Exception as e:
        print("ERRO preview_linha:", repr(e))
        raise HTTPException(status_code=500, detail=f"Falha ao calcular preview fiscal: {repr(e)}")

