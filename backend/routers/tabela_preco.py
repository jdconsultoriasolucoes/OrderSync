from fastapi import APIRouter, HTTPException, Query
from services.tabela_preco import calcular_valores_dos_produtos
from schemas.tabela_preco import TabelaPreco, TabelaPrecoCompleta, ProdutoCalculado, ParametrosCalculo 
from typing import List, Optional
from sqlalchemy import text
from models.tabela_preco import TabelaPreco as TabelaPrecoModel
from datetime import datetime
from database import SessionLocal

router = APIRouter()

# Simula um banco de dados em memória
tabelas_de_preco_db: List[TabelaPreco] = []


@router.post("/TabelaPreco", response_model=TabelaPreco)
def criar_tabela_preco(tabela: TabelaPreco):
    tabela.id = len(tabelas_de_preco_db) + 1
    tabelas_de_preco_db.append(tabela)
    return tabela


@router.get("/TabelaPreco", response_model=List[TabelaPreco])
def listar_tabelas_preco():
    return tabelas_de_preco_db


@router.get("/TabelaPreco/{tabela_id}", response_model=TabelaPreco)
def obter_tabela_preco(tabela_id: Optional [int]):
    for tabela in tabelas_de_preco_db:
        if tabela.id == tabela_id:
            return tabela
    raise HTTPException(status_code=404, detail="Tabela de preço não encontrada")


@router.put("/TabelaPreco/{tabela_id}", response_model=TabelaPreco)
def atualizar_tabela_preco(tabela_id: Optional [int], tabela_atualizada: TabelaPreco):
    for idx, tabela in enumerate(tabelas_de_preco_db):
        if tabela.id == tabela_id:
            tabela_atualizada.id = tabela_id
            tabelas_de_preco_db[idx] = tabela_atualizada
            return tabela_atualizada
    raise HTTPException(status_code=404, detail="Tabela de preço não encontrada")


@router.delete("/TabelaPreco/{tabela_id}")
def deletar_tabela_preco(tabela_id: Optional [int]):
    for idx, tabela in enumerate(tabelas_de_preco_db):
        if tabela.id == tabela_id:
            del tabelas_de_preco_db[idx]
            return {"message": "Tabela de preço deletada com sucesso"}
    raise HTTPException(status_code=404, detail="Tabela de preço não encontrada")

@router.get("/produtos_filtro")
def filtrar_produtos_para_tabela_preco(
    grupo: Optional[str] = Query(None),
    fornecedor: Optional[str] = Query(None),   # se não for usar, remova do signature
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    try:
        print(f"grupo={grupo}, fornecedor={fornecedor}, page={page}, page_size={page_size}")

        base_sql = """
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
                p.ipi AS ipi,
                p.iva_st AS icms_st,
                p.marca AS grupo,
                f.familia AS departamento
            FROM t_cadastro_produto p
            LEFT JOIN t_familia_produtos f 
                ON CAST(p.familia AS INT) = CAST(f.id AS INT)
            WHERE (:grupo IS NULL OR p.marca = :grupo)
              -- AND (:fornecedor IS NULL OR p.fornecedor = :fornecedor)  -- descomente se existir essa coluna
        """

        # mesmos params para count e paginação
        params = {
            "grupo": grupo or None,
            "fornecedor": fornecedor or None,
        }

        with SessionLocal() as db:
            # total
            count_sql = f"SELECT COUNT(*) AS total FROM ({base_sql}) sub"
            total = db.execute(text(count_sql), params).scalar() or 0

            # paginação + ordenação determinística
            offset = (page - 1) * page_size
            paginated_sql = f"""
                {base_sql}
                ORDER BY p.nome_produto ASC
                LIMIT :limit OFFSET :offset
            """
            params_lim = {**params, "limit": int(page_size), "offset": int(offset)}

            rows = db.execute(text(paginated_sql), params_lim).mappings().all()

        return {
            "items": rows,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

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

@router.get("/condicoes_pagamento")
def condicoes_pagamento():
    try:
        db = SessionLocal()
        query = text("select codigo_prazo, prazo, custo as taxa_condicao from t_condicoes_pagamento order by codigo_prazo")
        resultado = db.execute(query).fetchall()
        return [{"codigo": row.codigo_prazo, "descricao": row.prazo, "taxa_condicao": row.taxa_condicao} for row in resultado]
    finally:
        db.close()

@router.get("/filtro_grupo_produto")
def filtro_grupo_produto():
    try:
        db = SessionLocal()
        query = text("select distinct marca as grupo from  t_cadastro_produto order by marca")
        resultado = db.execute(query).fetchall()
        return [{"grupo": row.grupo} for row in resultado]
    finally:
        db.close()

@router.post("/salvar")
def salvar_tabela_preco(payload: TabelaPrecoCompleta):
    db = SessionLocal()
    try:
        for produto in payload.produtos:
            registro = TabelaPrecoModel(
                nome_tabela=payload.nome_tabela,
                validade_inicio=payload.validade_inicio,
                validade_fim=payload.validade_fim,
                cliente=payload.cliente,
                fornecedor=payload.fornecedor,
                **produto.dict()
            )
            db.add(registro)

        db.commit()
        return {"mensagem": "Tabela salva com sucesso", "qtd_produtos": len(payload.produtos)}
    finally:
        db.close()


@router.put("/{id}")
def editar_produto(id: int, novo_produto: TabelaPreco):
    db = SessionLocal()
    produto = db.query(TabelaPrecoModel).get(id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    for campo, valor in novo_produto.dict().items():
        setattr(produto, campo, valor)

    db.commit()
    return {"mensagem": "Produto atualizado com sucesso"}


@router.delete("/{id}")
def desativar_produto(id: int):
    db = SessionLocal()
    produto = db.query(TabelaPrecoModel).get(id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    produto.ativo = False
    produto.deletado_em = datetime.utcnow()

    db.commit()
    return {"mensagem": "Produto desativado com sucesso"}


@router.post("/calcular_valores", response_model=List[ProdutoCalculado])
def calcular_valores(payload: ParametrosCalculo):
    return calcular_valores_dos_produtos(payload)