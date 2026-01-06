from fastapi import APIRouter, HTTPException, Query
from services.tabela_preco import calcular_valores_dos_produtos, create_tabela, update_tabela
from schemas.tabela_preco import TabelaPreco, TabelaPrecoCompleta, ProdutoCalculado, ParametrosCalculo, ValidadeGlobalResp, TabelaSalvar  
from typing import List, Optional
from sqlalchemy import text , bindparam
from models.tabela_preco import TabelaPreco as TabelaPrecoModel
from datetime import datetime
from database import SessionLocal
from utils.calc_validade_dia import dias_restantes, classificar_status, _as_date
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
import re
from fastapi import Depends
from core.deps import get_current_user, get_db
from models.usuario import UsuarioModel

logger = logging.getLogger("tabela_preco")

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
    page_size: int = Query(25, ge=1, le=1000),
):
    try:
        base_sql = """
            SELECT 
                p.codigo_supra AS codigo_tabela,
                p.nome_produto AS descricao,
                CASE 
                    WHEN UPPER(p.embalagem_venda) IN ('SC', 'SACO') THEN 'SACO'
                    WHEN UPPER(p.embalagem_venda) IN ('CX', 'CAIXA') THEN 'CAIXA'
                    WHEN UPPER(p.embalagem_venda) IN ('FD', 'FARDO') THEN 'FARDO'
                    WHEN UPPER(p.embalagem_venda) IN ('PC', 'PACOTE') THEN 'PACOTE'
                    WHEN UPPER(p.embalagem_venda) IN ('UN', 'UNIDADE', 'UNI') THEN 'UNIDADE'
                    ELSE COALESCE(p.embalagem_venda, 'UN')
                END AS embalagem,
                p.peso AS peso_liquido,
                p.preco AS valor,
                p.ipi,
                p.iva_st,
                p.marca AS grupo,
                p.familia AS departamento,
                p.marca,
                p.id_familia,
                p.fornecedor,
                p.tipo,
                p.icms,
                p.validade_tabela
            FROM v_produto_v2_preco p
            WHERE p.status_produto = 'ATIVO'
              AND (:grupo IS NULL OR p.marca = :grupo)
              AND (:fornecedor IS NULL OR p.fornecedor = :fornecedor)
              AND (
                    :q IS NULL
                 OR  p.codigo_supra::text ILIKE :like
                 OR  p.nome_produto       ILIKE :like
                 OR  COALESCE(p.marca,'')   ILIKE :like
                 OR  COALESCE(p.unidade,'') ILIKE :like
                 OR  COALESCE(p.tipo,'')  ILIKE :like
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
        query = text("select distinct marca as grupo from t_cadastro_produto_v2 WHERE marca IS NOT NULL AND marca != '' order by marca")
        resultado = db.execute(query).fetchall()
        return [{"grupo": row.grupo} for row in resultado]
    finally:
        db.close()

@router.post("/salvar")
def salvar_tabela_preco(
    body: TabelaSalvar, 
    current_user: UsuarioModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return create_tabela(db, body, current_user.email)
    except Exception as e:
        logger.exception("[/salvar] Falha geral: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao salvar tabela_preco: {e}")






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
def listar_tabelas(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: Optional[str] = Query(None)
):
    try:
        db = SessionLocal()
        
        # Filtro de busca
        q_raw = (q or "").strip()
        like_pattern = f"%{q_raw}%"
        
        # 1. Query BASE (com filtros)
        #    Obs: nome_tabela e cliente estão no GROUP BY, então podemos filtrar no WHERE tranquilamente.
        #    Se quisesse filtrar pelo resultado de agregação, seria HAVING ou subquery.
        where_clause = "WHERE ativo is TRUE"
        params = {
            "limit": page_size,
            "offset": (page - 1) * page_size
        }
        
        if q_raw:
            where_clause += " AND (nome_tabela ILIKE :like OR cliente ILIKE :like)"
            params["like"] = like_pattern

        # 2. Contagem TOTAL (para paginação)
        #    Precisamos contar quantos GRUPOS existem. 
        #    Count(Distinct id_tabela) funciona bem já que id_tabela é chave do grupo.
        count_sql = f"""
            SELECT COUNT(DISTINCT id_tabela)
            FROM tb_tabela_preco
            {where_clause}
        """
        total = db.execute(text(count_sql), params).scalar() or 0

        # 3. Busca de dados paginados
        data_sql = f"""
            SELECT
              id_tabela,
              MIN(id_linha) AS any_row_id,
              nome_tabela,
              cliente,
              fornecedor,
              MAX(frete_kg) AS frete_kg,
              BOOL_OR(calcula_st) AS calcula_st,
              MAX(criado_em) AS criado_em
            FROM tb_tabela_preco
            {where_clause}
            GROUP BY id_tabela, nome_tabela, cliente, fornecedor
            ORDER BY MAX(criado_em) DESC
            LIMIT :limit OFFSET :offset
        """
        
        rows = db.execute(text(data_sql), params).mappings().all()

        items = [
            {
                "id": int(r["id_tabela"]),
                "nome_tabela": r["nome_tabela"],
                "cliente": r["cliente"],
                "fornecedor": r["fornecedor"],
                "frete_kg": float(r["frete_kg"] or 0),
                "calcula_st": bool(r["calcula_st"]),
            }
            for r in rows
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    except Exception as e:
        logger.error(f"Erro ao listar tabelas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao listar tabelas.")
    finally:
        db.close()



@router.get("/busca_cliente")
def busca_cliente(
    q: str = Query("", description="Trecho do nome ou CNPJ"),
    ramo: str | None = Query(None, description="Filtra pelo ramo_juridico ex.: 'Revenda'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        db = SessionLocal()

        # texto original digitado/colado
        q_raw = (q or "").strip()
        like = f"%{q_raw}%"

        # só dígitos (para CNPJ/CPF), mesmo se vier "7769327000171 - DISPET ..."
        cnpj_digits = re.sub(r"\D", "", q_raw)
        cnpj_like = f"%{cnpj_digits}%" if cnpj_digits else None

        base_sql = """
            SELECT
              cadastro_codigo_da_empresa AS codigo,
              COALESCE(cadastro_cnpj, cadastro_cpf) AS cnpj_cpf,
              cadastro_nome_cliente AS nome_cliente,
              cadastro_tipo_cliente AS ramo_juridico,
              cadastro_markup
            FROM public.t_cadastro_cliente_v2
            WHERE
              (
                :q = ''
                OR cadastro_nome_cliente ILIKE :like
                OR (
                    :cnpj_like IS NOT NULL
                    AND (cadastro_cnpj ILIKE :cnpj_like OR cadastro_cpf ILIKE :cnpj_like)
                  )
              )
        """

        params = {
            "q": q_raw,
            "like": like,
            "cnpj_like": cnpj_like,
            "offset": (page - 1) * page_size,
            "limit": page_size,
        }

        if ramo:
            base_sql += " AND cadastro_tipo_cliente = :ramo"
            params["ramo"] = ramo

        base_sql += " ORDER BY cadastro_nome_cliente OFFSET :offset LIMIT :limit"

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

         # se por algum motivo tiver divergência entre linhas, faz um OR
        calcula_st = any(bool(getattr(p, "calcula_st", False)) for p in itens) or bool(
            getattr(cab, "calcula_st", False)
        )

        return {
            "id": id_tabela,
            "nome_tabela": cab.nome_tabela,
            "cliente": cab.cliente,
            "codigo_cliente": getattr(cab, "codigo_cliente", None) or getattr(cab, "cliente_codigo", None),
            "fornecedor": cab.fornecedor,
            "calcula_st": calcula_st,
            "produtos": [
                {
                "codigo_produto_supra": p.codigo_produto_supra,     
                "descricao_produto": p.descricao_produto,           
                "embalagem": p.embalagem,
                "peso_liquido": p.peso_liquido,
                "valor_produto": p.valor_produto,                   
                "comissao_aplicada": p.comissao_aplicada,           
                "ajuste_pagamento": p.ajuste_pagamento,             
                "descricao_fator_comissao": p.descricao_fator_comissao, 
                "codigo_plano_pagamento": p.codigo_plano_pagamento, 
                "valor_frete_aplicado": p.valor_frete_aplicado,     
                "frete_kg": p.frete_kg,
                "grupo": p.grupo,
                "departamento": p.departamento,
                "ipi": p.ipi,
                "iva_st": p.iva_st,
                "icms_st": p.icms_st,
                "valor_frete": p.valor_frete,
                "valor_s_frete": p.valor_s_frete,
                "markup": p.markup,
                "valor_final_markup": p.valor_final_markup,
                "valor_s_frete_markup": p.valor_s_frete_markup,
                } for p in itens
            ]
        }
    

  

@router_meta.get("/validade_global")
def validade_global():
    try:
        with SessionLocal() as db:
            v = db.execute(text("""
                SELECT MAX(CAST(p.validade_tabela AS DATE)) AS max_validade
                FROM t_cadastro_produto_v2 p
                WHERE p.status_produto = 'ATIVO'
            """)).scalar()

        v_date = _as_date(v)
        if not v_date:
            return ValidadeGlobalResp()

        d = dias_restantes(v_date)
        s = classificar_status(d)
        v_br = v_date.strftime("%d/%m/%Y")

        return {
       # chaves que o front já usa:
       "validade": v_br,
       "tempo_restante": f"{d} dias",
       # mantém também o formato “rico”, se você quiser reaproveitar noutros pontos:
       "validade_tabela": v_date.isoformat(),
       "validade_tabela_br": v_br,
       "dias_restantes": d,
       "status_validade": s,
       "origem": "max_ativos",
         }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular validade_global: {e}")
    

class ItemReq(BaseModel):
    codigo: str
    quantidade: int

class ConfirmarPedidoReq(BaseModel):
    usar_valor_com_frete: bool
    produtos: List[ItemReq]

@router.post("/{tabela_id}/confirmar_pedido")
def confirmar_pedido(tabela_id: int, body: ConfirmarPedidoReq):
    # TODO: criar o pedido no BD e disparar e-mail silencioso
    if not body.produtos:
        raise HTTPException(status_code=400, detail="Nenhum item informado")

    # EXEMPLO de retorno mínimo esperado pelo front (ele só checa resp.ok):
    return {
        "ok": True,
        "tabela_id": tabela_id,
        "usar_valor_com_frete": body.usar_valor_com_frete,
        "itens": len(body.produtos)
    }

def only_code(v):
    # "1200 - 28/56/84 DIAS" -> "1200"
    if v is None: return ""
    return str(v).strip().split(" - ", 1)[0]

@router.put("/{id_tabela}")
def atualizar_tabela(
    id_tabela: int, 
    body: TabelaSalvar, 
    current_user: UsuarioModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        res = update_tabela(db, id_tabela, body, current_user.email)
        if res is None:
            raise HTTPException(404, "Tabela não encontrada")
        return res
    except Exception as e:
        logger.error(f"Erro ao atualizar tabela: {e}")
        # Re-raise apenas se for HTTPException
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")