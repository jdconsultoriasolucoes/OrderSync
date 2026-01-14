from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Any
from datetime import datetime

from database import SessionLocal
import schemas.system_tables as s

router = APIRouter(tags=["System Tables"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Condicoes de Pagamento ---

@router.get("/system/condicoes", response_model=List[s.CondicaoPagamentoOut])
def listar_condicoes(db: Session = Depends(get_db)):
    # Conversão: Banco armazena /100. Saida DEVE ser *100.
    res = db.execute(text("SELECT * FROM t_condicoes_pagamento WHERE ativo = TRUE ORDER BY codigo_prazo")).mappings().all()
    out = []
    for r in res:
        d = dict(r)
        if d.get("custo") is not None:
            d["custo"] = float(d["custo"]) * 100.0  # Present as percentage
        out.append(d)
    return out

@router.post("/system/condicoes", response_model=s.CondicaoPagamentoOut)
def criar_condicao(payload: s.CondicaoPagamentoCreate, db: Session = Depends(get_db)):
    # Conversão: Entrada é percentual. Gravar /100.
    custo_val = payload.custo / 100.0 if payload.custo is not None else None
    
    # Check ID conflict
    exists = db.execute(text("SELECT 1 FROM t_condicoes_pagamento WHERE codigo_prazo=:id"), {"id": payload.codigo_prazo}).scalar()
    if exists:
        raise HTTPException(status_code=400, detail="Código de prazo já existe.")

    sql = text("""
        INSERT INTO t_condicoes_pagamento (codigo_prazo, prazo, descricao, custo, ativo, created_at, updated_at, updated_by)
        VALUES (:id, :p, :d, :c, :ativo, NOW(), NOW(), 'System')
        RETURNING *
    """)
    new_row = db.execute(sql, {
        "id": payload.codigo_prazo,
        "p": payload.prazo,
        "d": payload.descricao,
        "c": custo_val,
        "ativo": True
    }).mappings().first()
    db.commit()
    
    d = dict(new_row)
    if d.get("custo") is not None:
        d["custo"] = float(d["custo"]) * 100.0
    return d

@router.put("/system/condicoes/{id}", response_model=s.CondicaoPagamentoOut)
def atualizar_condicao(id: int, payload: s.CondicaoPagamentoUpdate, db: Session = Depends(get_db)):
    custo_val = payload.custo / 100.0 if payload.custo is not None else None
    
    # Montar update dinâmico (apenas o que veio)
    sets = ["updated_at = NOW()"]
    params = {"id": id}
    
    if payload.prazo is not None:
        sets.append("prazo = :p")
        params["p"] = payload.prazo
    if payload.descricao is not None:
        sets.append("descricao = :d")
        params["d"] = payload.descricao
    if payload.custo is not None:
        sets.append("custo = :c")
        params["c"] = custo_val
    if payload.ativo is not None:
        sets.append("ativo = :atv")
        params["atv"] = payload.ativo

    sql = text(f"UPDATE t_condicoes_pagamento SET {', '.join(sets)} WHERE codigo_prazo = :id RETURNING *")
    row = db.execute(sql, params).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Condição não encontrada")
    db.commit()

    d = dict(row)
    if d.get("custo") is not None:
        d["custo"] = float(d["custo"]) * 100.0
    return d
    
@router.delete("/system/condicoes/{id}")
def deletar_condicao(id: int, db: Session = Depends(get_db)):
    # Soft delete
    row = db.execute(text("UPDATE t_condicoes_pagamento SET ativo = FALSE, updated_at = NOW() WHERE codigo_prazo = :id RETURNING codigo_prazo"), {"id": id}).scalar()
    if not row:
        raise HTTPException(status_code=404, detail="Condição não encontrada")
    db.commit()
    return {"message": "Inativado com sucesso"}


# --- Descontos ---

@router.get("/system/descontos", response_model=List[s.DescontoOut])
def listar_descontos(db: Session = Depends(get_db)):
    res = db.execute(text("SELECT * FROM t_desconto WHERE ativo = TRUE ORDER BY id_desconto")).mappings().all()
    out = []
    for r in res:
        d = dict(r)
        if d.get("fator_comissao") is not None:
            d["fator_comissao"] = float(d["fator_comissao"]) * 100.0
        out.append(d)
    return out

@router.post("/system/descontos", response_model=s.DescontoOut)
def criar_desconto(payload: s.DescontoCreate, db: Session = Depends(get_db)):
    fator = payload.fator_comissao / 100.0 if payload.fator_comissao is not None else None
    
    exists = db.execute(text("SELECT 1 FROM t_desconto WHERE id_desconto=:id"), {"id": payload.id_desconto}).scalar()
    if exists:
        raise HTTPException(status_code=400, detail="ID Desconto já existe.")

    sql = text("""
        INSERT INTO t_desconto (id_desconto, fator_comissao, ativo, created_at, updated_at, updated_by)
        VALUES (:id, :f, :ativo, NOW(), NOW(), 'System')
        RETURNING *
    """)
    new_row = db.execute(sql, {"id": payload.id_desconto, "f": fator, "ativo": True}).mappings().first()
    db.commit()
    
    d = dict(new_row)
    d["fator_comissao"] = float(d["fator_comissao"] or 0) * 100.0
    return d

@router.put("/system/descontos/{id}", response_model=s.DescontoOut)
def atualizar_desconto(id: int, payload: s.DescontoUpdate, db: Session = Depends(get_db)):
    fator = payload.fator_comissao / 100.0 if payload.fator_comissao is not None else None
    
    sets = ["updated_at = NOW()"]
    params = {"id": id}
    
    if payload.fator_comissao is not None:
        sets.append("fator_comissao = :f")
        params["f"] = fator
    if payload.ativo is not None:
        sets.append("ativo = :atv")
        params["atv"] = payload.ativo

    sql = text(f"UPDATE t_desconto SET {', '.join(sets)} WHERE id_desconto = :id RETURNING *")
    row = db.execute(sql, params).mappings().first()
    if not row:
         raise HTTPException(status_code=404, detail="Desconto não encontrado")
    db.commit()
    
    d = dict(row)
    d["fator_comissao"] = float(d["fator_comissao"] or 0) * 100.0
    return d

@router.delete("/system/descontos/{id}")
def deletar_desconto(id: int, db: Session = Depends(get_db)):
    row = db.execute(text("UPDATE t_desconto SET ativo = FALSE, updated_at = NOW() WHERE id_desconto = :id RETURNING id_desconto"), {"id": id}).scalar()
    if not row:
        raise HTTPException(status_code=404, detail="Desconto não encontrado")
    db.commit()
    return {"message": "Inativado com sucesso"}


# --- Familias ---

@router.get("/system/familias", response_model=List[s.FamiliaProdutoOut])
def listar_familias(db: Session = Depends(get_db)):
    return db.execute(text("SELECT * FROM t_familia_produtos WHERE ativo = TRUE ORDER BY id")).mappings().all()

@router.post("/system/familias", response_model=s.FamiliaProdutoOut)
def criar_familia(payload: s.FamiliaProdutoBase, db: Session = Depends(get_db)):
    # ID Auto-increment (max + 1) or Sequence? user said "Id ... não pode ser alterados". Usually DB handles creation.
    # User didn't verify if sequence exists. The table has ID column.
    # Let's verify max ID logic or assume sequence. `t_familia_produtos` usually has data.
    # Assuming standard insert logic. If auto-increment is not set, we might need manual ID.
    # I'll check if ID is serial from schema? The schema dump said "id (integer)". Doesn't confirm Serial.
    # I'll implement Max+1 logic to be safe if no sequence.
    
    max_id = db.execute(text("SELECT COALESCE(MAX(id), 0) FROM t_familia_produtos")).scalar()
    new_id = max_id + 1
    
    sql = text("""
        INSERT INTO t_familia_produtos (id, tipo, familia, marca, ativo, created_at, updated_at, updated_by)
        VALUES (:id, :t, :f, :m, :ativo, NOW(), NOW(), 'System')
        RETURNING *
    """)
    row = db.execute(sql, {
        "id": new_id,
        "t": payload.tipo,
        "f": payload.familia,
        "m": payload.marca,
        "ativo": True
    }).mappings().first()
    db.commit()
    return row

@router.put("/system/familias/{id}", response_model=s.FamiliaProdutoOut)
def atualizar_familia(id: int, payload: s.FamiliaProdutoUpdate, db: Session = Depends(get_db)):
    sets = ["updated_at = NOW()"]
    params = {"id": id}
    
    if payload.tipo is not None:
        sets.append("tipo = :t")
        params["t"] = payload.tipo
    if payload.familia is not None:
        sets.append("familia = :f")
        params["f"] = payload.familia
    if payload.marca is not None:
        sets.append("marca = :m")
        params["m"] = payload.marca
    if payload.ativo is not None:
        sets.append("ativo = :atv")
        params["atv"] = payload.ativo

    sql = text(f"UPDATE t_familia_produtos SET {', '.join(sets)} WHERE id = :id RETURNING *")
    row = db.execute(sql, params).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Família não encontrada")
    db.commit()
    return row

@router.delete("/system/familias/{id}")
def deletar_familia(id: int, db: Session = Depends(get_db)):
    row = db.execute(text("UPDATE t_familia_produtos SET ativo = FALSE, updated_at = NOW() WHERE id = :id RETURNING id"), {"id": id}).scalar()
    if not row:
        raise HTTPException(status_code=404, detail="Família não encontrada")
    db.commit()
    return {"message": "Inativado com sucesso"}
