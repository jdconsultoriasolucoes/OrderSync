from fastapi import APIRouter, HTTPException, Query
from schemas.tabela_preco import TabelaPreco
from typing import List, Optional
from sqlalchemy import text
from database import SessionLocal

router = APIRouter()

# Simula um banco de dados em memória
#tabelas_de_preco_db: List[TabelaPreco] = []


@router.post("/", response_model=TabelaPreco)
def criar_tabela_preco(tabela: TabelaPreco):
    tabela.id = len(tabelas_de_preco_db) + 1
    tabelas_de_preco_db.append(tabela)
    return tabela


@router.get("/", response_model=List[TabelaPreco])
def listar_tabelas_preco():
    return tabelas_de_preco_db


@router.get("/{tabela_id}", response_model=TabelaPreco)
def obter_tabela_preco(tabela_id: Optional [int]):
    for tabela in tabelas_de_preco_db:
        if tabela.id == tabela_id:
            return tabela
    raise HTTPException(status_code=404, detail="Tabela de preço não encontrada")


@router.put("/{tabela_id}", response_model=TabelaPreco)
def atualizar_tabela_preco(tabela_id: Optional [int], tabela_atualizada: TabelaPreco):
    for idx, tabela in enumerate(tabelas_de_preco_db):
        if tabela.id == tabela_id:
            tabela_atualizada.id = tabela_id
            tabelas_de_preco_db[idx] = tabela_atualizada
            return tabela_atualizada
    raise HTTPException(status_code=404, detail="Tabela de preço não encontrada")


@router.delete("/{tabela_id}")
def deletar_tabela_preco(tabela_id: Optional [int]):
    for idx, tabela in enumerate(tabelas_de_preco_db):
        if tabela.id == tabela_id:
            del tabelas_de_preco_db[idx]
            return {"message": "Tabela de preço deletada com sucesso"}
    raise HTTPException(status_code=404, detail="Tabela de preço não encontrada")

@router.get("/produtos_filtro")
def filtrar_produtos_para_tabela_preco(
    grupo: Optional[str] = Query(None),
    plano_pagamento: Optional[str] = Query(None),
    frete_kg: Optional[float] = Query(0.0),
    fornecedor: Optional[str] = Query(None),
    fator_comissao: Optional[float] = Query(0.0)

):
    try:
        print(f"grupo={grupo}, plano_pagamento={plano_pagamento}, frete_kg={frete_kg}, fator_comissao={fator_comissao}")

        db = SessionLocal()

        query = text("""
                      
            SELECT 
                p.codigo_supra AS codigo_tabela,
                p.nome_produto AS descricao,
                CASE 
                    WHEN p.unidade IN ('SC','SACO') THEN 'SACO'
                    WHEN p.unidade IN ('FD') THEN 'FARDO'
                    WHEN p.unidade IN ('CX') THEN 'CAIXA'
                    ELSE p.unidade
                END AS embalagem,
                p.peso AS peso_liquido,
                p.peso AS peso_bruto,
                p.preco_lista_supra AS valor,
                :fator_comissao AS fator_comissao,
                cp.custo AS custo_condicao_pagamento,
                :frete_kg AS frete_kg,
                p.ipi,
                p.iva_st AS icms_st,
                ROUND(p.preco_lista_supra * (1 + cp.custo), 2) AS valor_base,  -- sem desconto
                p.marca AS grupo,
                f.familia AS departamento,
                :fornecedor AS fornecedor
            FROM t_cadastro_produto p
            LEFT JOIN t_familia_produtos f ON CAST(p.familia AS INT) = CAST(f.id AS INT)
            LEFT JOIN t_condicoes_pagamento cp ON cp.codigo_prazo = :plano_pagamento
            WHERE (:grupo IS NULL OR p.marca = :grupo)
        """)

        params = {
            "grupo": grupo or None,
            "plano_pagamento": plano_pagamento or 0,
            "frete_kg": frete_kg or 0.0,
            "fator_comissao": fator_comissao or 0.0,
            "fornecedor": fornecedor or ""
        }


        result = db.execute(query, params)
        rows = [dict(row) for row in result]
        db.close()
        return rows

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar produtos: {str(e)}")
    
@router.get("/descontos")
def listar_descontos():
    try:
        db = SessionLocal()
        query = text("SELECT id_desconto, fator_comissao FROM t_desconto ORDER BY id_desconto")
        resultado = db.execute(query).fetchall()
        return [{"codigo": row.id_desconto, "percentual": row.fator_comissao} for row in resultado]
    finally:
        db.close()