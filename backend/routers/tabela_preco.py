from fastapi import APIRouter, HTTPException, Query
from services.tabela_preco import calcular_valores_dos_produtos, buscar_max_validade_ativos
from schemas.tabela_preco import TabelaPreco, TabelaPrecoCompleta, ProdutoCalculado, ParametrosCalculo, ValidadeGlobalResp 
from typing import List, Optional
from sqlalchemy import text
from models.tabela_preco import TabelaPreco as TabelaPrecoModel
from datetime import datetime
from database import SessionLocal
from utils.calc_validade_dia import dias_restantes, classificar_status, _as_date

router_meta = APIRouter(prefix="/tabela_preco/meta", tags=["tabela_preco"])
router      = APIRouter(prefix="/tabela_preco",       tags=["tabela_preco"])

# Simula um banco de dados em memória
tabelas_de_preco_db: List[TabelaPreco] = []



@router.get("/produtos_filtro")
def filtrar_produtos_para_tabela_preco(
    grupo: Optional[str] = Query(None),
    fornecedor: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Busca em código, descrição, grupo/marca, unidade/tipo"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    try:
        base_sql = """
            SELECT 
                p.codigo_supra AS codigo_tabela,
                p.nome_produto AS descricao,
                CASE 
                    WHEN p.unidade IN ('SC','SACO') THEN 'SACO'
                    WHEN p.unidade IN ('FD')       THEN 'FARDO'
                    WHEN p.unidade IN ('CX')       THEN 'CAIXA'
                    ELSE p.unidade
                END AS embalagem,
                p.peso AS peso_liquido,
                p.preco_lista_supra AS valor,
                p.ipi AS ipi,
                p.iva_st AS iva_st,
                p.marca AS grupo,
                f.familia AS departamento,
                p.fornecedor,
                f.tipo,
                p.icms,
                p.validade_tabela
            FROM t_cadastro_produto p
            LEFT JOIN t_familia_produtos f 
              ON CAST(p.familia AS INT) = CAST(f.id AS INT)
            WHERE p.status_produto = 'ATIVO'
              AND (:grupo IS NULL OR p.marca = :grupo)
              AND (:fornecedor IS NULL OR p.fornecedor = :fornecedor)
              AND (
                    :q IS NULL
                 OR  p.codigo_supra::text ILIKE :like
                 OR  p.nome_produto       ILIKE :like
                 OR  COALESCE(p.marca,'') ILIKE :like
                 OR  COALESCE(p.unidade,'') ILIKE :like
                 OR  COALESCE(f.tipo,'')  ILIKE :like
              )
        """

        params = {
            "grupo": grupo or None,
            "fornecedor": fornecedor or None,
            "q": q or None,
            "like": f"%{q}%" if q else None,
        }

        with SessionLocal() as db:
            count_sql = f"SELECT COUNT(*) AS total FROM ({base_sql}) sub"
            total = db.execute(text(count_sql), params).scalar() or 0

            offset = (page - 1) * page_size
            paginated_sql = f"""
                {base_sql}
                ORDER BY p.nome_produto ASC
                LIMIT :limit OFFSET :offset
            """
            params_lim = {**params, "limit": int(page_size), "offset": int(offset)}
            rows = db.execute(text(paginated_sql), params_lim).mappings().all()

        return {"items": rows, "total": total, "page": page, "page_size": page_size}
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
        max_tid = db.execute(text("SELECT COALESCE(MAX(id_tabela), 0) FROM tb_tabela_preco")).scalar() or 0
        id_tabela = int(max_tid) + 1
        for produto in payload.produtos:
           registro = TabelaPrecoModel(
                 # Cabeçalho
                 id_tabela=id_tabela,
                 nome_tabela=payload.nome_tabela,
                 cliente=payload.cliente,
                 fornecedor=payload.fornecedor or (getattr(produto, "fornecedor", None) or ""),
                
                 # Produto
                 codigo_tabela=produto.codigo_tabela,
                 descricao=produto.descricao,
                 embalagem=produto.embalagem,
                 peso_liquido=produto.peso_liquido,
                 peso_bruto=produto.peso_bruto,
                 valor=produto.valor,  # mantém apenas ESTE
                # NÃO setar: valor=produto.valor_liquido  (removido)

                 # Mapping existente
                 comissao_aplicada=(produto.desconto or 0.0),
                 ajuste_pagamento=(produto.acrescimo or 0.0),

                 fator_comissao=produto.fator_comissao,
                 plano_pagamento=produto.plano_pagamento,
                 frete_percentual=produto.frete_percentual,
                 frete_kg=produto.frete_kg,
                 grupo=produto.grupo,
                 departamento=produto.departamento,
                 ipi=produto.ipi,
                 iva_st=produto.iva_st,

                  # Colunas que existem no modelo (ok persistir)
                  valor_frete=produto.valor_frete,
                  valor_s_frete=produto.valor_s_frete,
                         )
        db.add(registro)

        db.commit()
        return {"mensagem": "Tabela salva com sucesso", "qtd_produtos": len(payload.produtos)}
    finally:
        db.close()


@router.put("/{id_linha}")
def editar_produto(id_linha: int, novo_produto: TabelaPreco):
 with SessionLocal() as db:
    produto = db.query(TabelaPrecoModel).get(id_linha)
    if not produto:
     raise HTTPException(status_code=404, detail="Produto não encontrado")

    dados = novo_produto.dict()

    # Bloqueia identificadores
    dados.pop("id_linha", None)
    dados.pop("id_tabela", None)

    # Mapeia descontos/acréscimos
    if "desconto" in dados:
        produto.comissao_aplicada = dados.pop("desconto") or 0.0
    if "acrescimo" in dados:
        produto.ajuste_pagamento = dados.pop("acrescimo") or 0.0

    # Campos do modelo que podem ser atualizados
    permitidos = {
        "nome_tabela","fornecedor","cliente",
        "codigo_tabela","descricao","embalagem","peso_liquido","peso_bruto","valor",
        "fator_comissao","plano_pagamento","frete_percentual","frete_kg",
        "grupo","departamento","ipi","iva_st",
        "valor_frete","valor_s_frete",
            }

    for campo, valor in list(dados.items()):
        if campo in permitidos:
            setattr(produto, campo, valor)
        # ignora silenciosamente o resto (ex.: icms_st, valor_liquido, validade_tabela, etc.)

    db.commit()
    return {"mensagem": "Produto atualizado com sucesso"}


@router.delete("/{id_tabela}")
def desativar_tabela(id_tabela: int):
    with SessionLocal() as db:
        linhas = db.query(TabelaPrecoModel).filter_by(id_tabela=id_tabela, ativo=True).all()
        if not linhas:
            raise HTTPException(status_code=404, detail="Tabela não encontrada")

        for r in linhas:
            r.ativo = False
            r.deletado_em = datetime.utcnow()

        db.commit()
        return {"mensagem": "Tabela desativada com sucesso", "linhas_afetadas": len(linhas)}

@router.post("/calcular_valores", response_model=List[ProdutoCalculado])
def calcular_valores(payload: ParametrosCalculo):
    return calcular_valores_dos_produtos(payload)

@router.get("/")
def listar_tabelas():
    with SessionLocal() as db:
        rows = db.execute(text("""
            SELECT
              id_tabela,
              MIN(id_linha) AS any_row_id,
              nome_tabela,
              cliente,
              fornecedor,
              MAX(criado_em) AS criado_em
            FROM tb_tabela_preco
            WHERE ativo is TRUE
            GROUP BY id_tabela, nome_tabela, cliente, fornecedor
            ORDER BY criado_em DESC
        """)).mappings().all()

        # O front usa "tabela.id" para abrir/editar; devolvemos id = id_tabela
        return [
            {
                "id": int(r["id_tabela"]),
                "nome_tabela": r["nome_tabela"],
                "cliente": r["cliente"],
                "fornecedor": r["fornecedor"],
            }
            for r in rows
        ]



@router.get("/busca_cliente")
def busca_cliente(
    q: str = Query("", description="Trecho do nome ou CNPJ"),
    ramo: str | None = Query(None, description="Filtra pelo ramo_juridico ex.: 'Revenda'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        db = SessionLocal()
        base_sql = """
            SELECT
              codigo,
              cnpj_cpf_faturamento AS cnpj_cpf,
              nome_empresarial     AS nome_cliente,
              ramo_juridico
            FROM public.t_cadastro_cliente
            WHERE
              (:q = '' OR nome_empresarial ILIKE :like OR cnpj_cpf_faturamento ILIKE :like)
        """
        params = {
            "q": q,
            "like": f"%{q}%",
            "offset": (page - 1) * page_size,
            "limit": page_size,
        }
        if ramo:
            base_sql += " AND ramo_juridico = :ramo"
            params["ramo"] = ramo

        base_sql += " ORDER BY nome_empresarial OFFSET :offset LIMIT :limit"

        rows = db.execute(text(base_sql), params).mappings().all()
        return [dict(r) for r in rows]
    finally:
        db.close()


@router.get("/{id_tabela}")
def obter_tabela(id_tabela: int):
    with SessionLocal() as db:
        cab = db.query(TabelaPrecoModel).filter_by(id_tabela=id_tabela, ativo=True).first()
        if not cab:
            raise HTTPException(status_code=404, detail="Tabela não encontrada")

        itens = db.query(TabelaPrecoModel).filter_by(id_tabela=id_tabela, ativo=True).all()

        return {
            "id": id_tabela,
            "nome_tabela": cab.nome_tabela,
            "cliente": cab.cliente,
            "fornecedor": cab.fornecedor,
            "produtos": [
                {
                    "codigo_tabela": p.codigo_tabela,
                    "descricao": p.descricao,
                    "embalagem": p.embalagem,
                    "peso_liquido": p.peso_liquido,
                    "valor": p.valor,
                    "desconto": p.comissao_aplicada,
                    "acrescimo": p.ajuste_pagamento,
                    "fator_comissao": p.fator_comissao,
                    "plano_pagamento": p.plano_pagamento,
                    "frete_percentual": p.frete_percentual,
                    "frete_kg": p.frete_kg,
                    "grupo": p.grupo,
                    "departamento": p.departamento,
                    "ipi": p.ipi,
                    "iva_st": p.iva_st,
                } for p in itens
            ]
        }
    

  

@router_meta.get("/validade_global", response_model=ValidadeGlobalResp)
def validade_global():
    try:
        with SessionLocal() as db:
            v = db.execute(text("""
                SELECT MAX(CAST(p.validade_tabela AS DATE)) AS max_validade
                FROM t_cadastro_produto p
                WHERE p.status_produto = 'ATIVO'
            """)).scalar()

        v_date = _as_date(v)
        if not v_date:
            return ValidadeGlobalResp()

        d = dias_restantes(v_date)
        s = classificar_status(d)
        v_br = v_date.strftime("%d/%m/%Y")

        return ValidadeGlobalResp(
            validade_tabela=v_date,
            validade_tabela_br=v_br,
            dias_restantes=d,
            status_validade=s,
            origem="max_ativos",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular validade_global: {e}")
    

def _as_frac(x: float | None) -> float:
    if not x: 
        return 0.0
    # aceita 0–1 (fração) ou 0–100 (percentual)
    return x/100.0 if x > 1.0 else x

def calcular_valores_dos_produtos(payload: ParametrosCalculo) -> List[ProdutoCalculado]:
    resultado = []
    for produto in payload.produtos:
        valor = produto.valor
        peso  = produto.peso_liquido or 0.0
        is_pet = (str(produto.tipo or "").strip().lower() == "pet")

        ipi_pct  = _as_frac(produto.ipi)
        iva_pct  = _as_frac(produto.iva_st)
        # se os parâmetros do payload forem percentuais, normalize também
        fator_comissao     = _as_frac(payload.fator_comissao)
        acrescimo_pagamento = _as_frac(payload.acrescimo_pagamento)

        ipi_item = ipi_pct if (is_pet and peso <= 10) else 0.0

        frete_kg = (payload.frete_unitario / 1000) * peso
        ajuste_pagamento = valor * acrescimo_pagamento
        comissao_aplicada = valor * fator_comissao

        base = valor + frete_kg + ajuste_pagamento - comissao_aplicada
        valor_liquido = base + (base * ipi_item) + (base * iva_pct)

        resultado.append(ProdutoCalculado(
            **produto.dict(),
            frete_kg=round(frete_kg, 4),
            ajuste_pagamento=round(ajuste_pagamento, 4),
            comissao_aplicada=round(comissao_aplicada, 4),
            valor_liquido=round(valor_liquido, 2),
        ))
    return resultado
