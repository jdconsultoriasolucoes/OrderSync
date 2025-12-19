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
from typing import Optional, List, Union

# ... (imports remain)

# --------- I/O ---------
class LinhaPreviewIn(BaseModel):
    # ACEITA INT OU STR agora, para evitar crash com "Não cadastrado"
    cliente_codigo: Optional[Union[int, str]] = None
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
              b.tipo,
              b.peso    AS peso_kg,
              b.iva_st,
              b.ipi,
              b.icms
            FROM public.v_produto_v2_preco b
            WHERE b.status_produto = 'ATIVO' and b.codigo_supra::text = :pid
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
        print(f"--- PREVIEW LINHA DEBUG ---")
        print(f"Payload input: cliente_codigo={payload.cliente_codigo!r} (type {type(payload.cliente_codigo)}), forcar={payload.forcar_iva_st}, produto={payload.produto_id}")

        # 1. Tenta carregar dados do cliente SE for um ID numérico válido
        cliente = {}
        if payload.cliente_codigo:
            try:
                # remove espaços se for string e converte
                val_str = str(payload.cliente_codigo).strip()
                if val_str.isdigit():
                    cod_int = int(val_str)
                    cliente = carregar_cliente(db, cod_int)
                else:
                    print(f"cliente_codigo '{val_str}' nao é numérico, ignorando DB lookup.")
            except Exception as ex:
                print(f"Erro ao converter cliente_codigo: {ex}")
                pass
        
        produto = carregar_produto(db, payload.produto_id)
        
        print(f"Cliente DB: {cliente}")
        print(f"Produto DB: {produto.get('codigo_supra')} - {produto.get('tipo')} - IVA: {produto.get('iva_st')}")

        ramo_db = cliente.get("ramo_juridico") if cliente else None
        ramo = ramo_db or getattr(payload, "ramo_juridico", None)
        print(f"Ramo Final: {ramo!r} (DB: {ramo_db!r}, Payload: {getattr(payload, 'ramo_juridico', None)!r})")

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
        print(f"DECIDE ST: Aplica={aplica}, Motivos={motivos}")

        comp = calcular_linha(
            preco_unit=payload.preco_unit,
            quantidade=payload.quantidade,
            desconto_linha=payload.desconto_linha,
            frete_linha=payload.frete_linha,
            ipi=ipi, icms=icms, iva_st=iva_st,
            aplica_st=aplica
        )
        
        print(f"TOTAL COM ST: {comp['total_com_st']}")
        print(f"---------------------------")

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

