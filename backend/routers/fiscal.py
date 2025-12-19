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
# ... (rest of Schema)

# ... (get_db and carregar_cliente helper remains same, but we will protect usage below)

@router.post("/fiscal/preview-linha", response_model=LinhaPreviewOut)
def preview_linha(payload: LinhaPreviewIn, db: Session = Depends(get_db)):
    try:
        # 1. Tenta carregar dados do cliente SE for um ID numérico válido
        cliente = {}
        if payload.cliente_codigo:
            # Tenta converter para int de forma segura
            try:
                cod_int = int(payload.cliente_codigo)
                cliente = carregar_cliente(db, cod_int)
            except (ValueError, TypeError):
                # Se for string (ex: "Não cadastrado"), ignora e segue sem dados do DB
                pass
        
        produto = carregar_produto(db, payload.produto_id)
        
        print(f"DBG cliente: {cliente} (cod original: {payload.cliente_codigo})")
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

