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
    
    # Regra de ID: Pega o maior ID deste TIPO e soma 10 (conforme regra de ingestão)
    max_id = db.execute(
        text("SELECT COALESCE(MAX(id), 0) FROM t_familia_produtos WHERE tipo = :t"),
        {"t": payload.tipo}
    ).scalar()
    
    # Se não tiver nenhum desse tipo, precisamos definir um "start"? 
    # Assumindo que 0 retorna se vazio, entao o primeiro será 10.
    new_id = max_id + 10
    
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
    
    # --- GATILHO DE SINCRONIZAÇÃO ---
    # Se alterou familia ou marca, replica para t_cadastro_produto_v2
    if payload.familia is not None or payload.marca is not None:
        # Usa os valores novos (do payload ou do row atualizado)
        # Se payload.marca for None, não mudou, mas precisamos do valor atual para o update?
        # Melhor pegar do 'row' que é o estado final.
        
        nova_familia = row["familia"]
        nova_marca = row["marca"] # pode ser None/Null na tabela? Se sim, cuidado. 
                                  # Mas na t_cadastro_produto_v2 usamos familia como fallback de marca.
        
        # O SQL abaixo atualiza todos os produtos vinculados a este ID de família
        sync_sql = text("""
            UPDATE t_cadastro_produto_v2
               SET familia = :fam,
                   marca   = :marc,
                   updated_at = NOW()
             WHERE id_familia = :fid
        """)
        
        # Marca fallback: Se nova_marca for null/empty, usa a propria familia (regra de negocio comum)
        marca_final = nova_marca if nova_marca else nova_familia
        
        db.execute(sync_sql, {
            "fam": nova_familia,
            "marc": marca_final,
            "fid": id
        })

    db.commit()
    return row

@router.delete("/system/familias/{id}")
def deletar_familia(id: int, db: Session = Depends(get_db)):
    row = db.execute(text("UPDATE t_familia_produtos SET ativo = FALSE, updated_at = NOW() WHERE id = :id RETURNING id"), {"id": id}).scalar()
    if not row:
        raise HTTPException(status_code=404, detail="Família não encontrada")
    db.commit()
    return {"message": "Inativado com sucesso"}

@router.get("/system/import_status_cadastro")
def import_status_cadastro(db: Session = Depends(get_db)):
    sql_create = text("""
        CREATE TABLE IF NOT EXISTS tb_status_cadastro (
            id SERIAL PRIMARY KEY,
            descricao VARCHAR UNIQUE
        )
    """)
    db.execute(sql_create)
    db.commit()

    sql_insert = text("""
        INSERT INTO tb_status_cadastro (descricao)
        SELECT DISTINCT cadastro_status_cadastro
        FROM t_cadastro_cliente_v2
        WHERE cadastro_status_cadastro IS NOT NULL
          AND trim(cadastro_status_cadastro) != ''
          AND cadastro_status_cadastro NOT IN (SELECT descricao FROM tb_status_cadastro)
        ON CONFLICT (descricao) DO NOTHING
    """)
    db.execute(sql_insert)
    db.commit()
    return {"message": "Status importados com sucesso"}

@router.get("/system/status_cadastro", response_model=List[s.StatusCadastroOut])
def listar_status_cadastro(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, descricao FROM tb_status_cadastro ORDER BY descricao")).mappings().all()
    return rows

@router.post("/system/status_cadastro", response_model=s.StatusCadastroOut)
def criar_status_cadastro(payload: s.StatusCadastroCreate, db: Session = Depends(get_db)):
    novo_id = db.execute(
        text("INSERT INTO tb_status_cadastro (descricao) VALUES (:desc) RETURNING id"),
        {"desc": payload.descricao}
    ).scalar()
    db.commit()
    return {"id": novo_id, "descricao": payload.descricao}

@router.put("/system/status_cadastro/{id}", response_model=s.StatusCadastroOut)
def atualizar_status_cadastro(id: int, payload: s.StatusCadastroUpdate, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id, descricao FROM tb_status_cadastro WHERE id = :id"), {"id": id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Status não encontrado")
    
    nova_desc = payload.descricao if payload.descricao is not None else row["descricao"]
    db.execute(text("UPDATE tb_status_cadastro SET descricao = :desc WHERE id = :id"), {"desc": nova_desc, "id": id})
    db.commit()
    return {"id": id, "descricao": nova_desc}

@router.delete("/system/status_cadastro/{id}")
def deletar_status_cadastro(id: int, db: Session = Depends(get_db)):
    row = db.execute(text("DELETE FROM tb_status_cadastro WHERE id = :id RETURNING id"), {"id": id}).scalar()
    if not row:
        raise HTTPException(status_code=404, detail="Status não encontrado")
    db.commit()
    return {"message": "Deletado com sucesso"}
