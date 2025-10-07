from fastapi import APIRouter, HTTPException, Query
from services.tabela_preco import calcular_valores_dos_produtos, buscar_max_validade_ativos
from schemas.tabela_preco import TabelaPreco, TabelaPrecoCompleta, ProdutoCalculado, ParametrosCalculo, ValidadeGlobalResp, TabelaSalvar  
from typing import List, Optional
from sqlalchemy import text
from models.tabela_preco import TabelaPreco as TabelaPrecoModel
from datetime import datetime
from database import SessionLocal
from utils.calc_validade_dia import dias_restantes, classificar_status, _as_date
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging
from sqlalchemy.exc import SQLAlchemyError

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
def salvar_tabela_preco(body: TabelaSalvar):
    db: Session = SessionLocal()
    try:
        # 1) Gera id_tabela com fallback
        try:
            id_tabela = db.execute(text("SELECT nextval('seq_tabela_preco_id_tabela')")).scalar()
        except Exception:
            logger.warning("seq_tabela_preco_id_tabela ausente; usando MAX+1")
            id_tabela = db.execute(text("SELECT COALESCE(MAX(id_tabela),0)+1 FROM tb_tabela_preco")).scalar()

        insert_sql = text("""
            INSERT INTO tb_tabela_preco (
              id_tabela, nome_tabela, fornecedor, codigo_cliente, cliente,
              codigo_produto_supra, descricao_produto, embalagem, peso_liquido, valor_produto,
              comissao_aplicada, ajuste_pagamento, descricao_fator_comissao, codigo_plano_pagamento,
              valor_frete_aplicado, frete_kg, valor_frete, valor_s_frete, grupo, departamento,
              ipi, icms_st, iva_st
            ) VALUES (
              :id_tabela, :nome_tabela, :fornecedor, :codigo_cliente, :cliente,
              :codigo_produto_supra, :descricao_produto, :embalagem, :peso_liquido, :valor_produto,
              :comissao_aplicada, :ajuste_pagamento, :descricao_fator_comissao, :codigo_plano_pagamento,
              :valor_frete_aplicado, :frete_kg, :valor_frete, :valor_s_frete, :grupo, :departamento,
              :ipi, :icms_st, :iva_st
            )
            RETURNING id_linha
        """)

        logger.info("[/salvar] header id=%s nome=%s cliente=%s fornecedor=%s codigo_cliente=%s",
                    id_tabela, body.nome_tabela, body.cliente, body.fornecedor, getattr(body, "codigo_cliente", None))

        inseridos = 0
        for i, produto in enumerate(body.produtos, start=1):
            params = {
                "id_tabela": int(id_tabela),
                "nome_tabela": body.nome_tabela or "",
                "fornecedor":  (body.fornecedor or ""),
                "codigo_cliente": getattr(body, "codigo_cliente", None),
                "cliente":     body.cliente or "",

                "codigo_produto_supra": produto.codigo_produto_supra or "",
                "descricao_produto":    (produto.descricao_produto or ""),
                "embalagem":            (getattr(produto, "embalagem", "") or ""),
                "peso_liquido":         float(getattr(produto, "peso_liquido", 0) or 0),

                "valor_produto":        float(produto.valor_produto or 0),

                "comissao_aplicada":        float(getattr(produto, "comissao_aplicada", 0) or 0),
                "ajuste_pagamento":         float(getattr(produto, "ajuste_pagamento", 0) or 0),
                "descricao_fator_comissao": (getattr(produto, "descricao_fator_comissao", "") or ""),
                "codigo_plano_pagamento":   (getattr(produto, "codigo_plano_pagamento", "") or ""),

                "valor_frete_aplicado": float(getattr(produto, "valor_frete_aplicado", 0) or 0),
                "frete_kg":             float(getattr(produto, "frete_kg", 0) or 0),

                "valor_frete":   float(getattr(produto, "valor_frete", 0) or 0),
                "valor_s_frete": float(getattr(produto, "valor_s_frete", 0) or 0),

                "grupo":        (getattr(produto, "grupo", "") or ""),
                "departamento": (getattr(produto, "departamento", "") or ""),

                "ipi":     float(getattr(produto, "ipi", 0) or 0),
                "icms_st": float(getattr(produto, "icms_st", 0) or 0),
                "iva_st":  float(getattr(produto, "iva_st", 0) or 0),
            }

            logger.info("[/salvar] item %s params=%s", i, params)

            try:
                db.execute(insert_sql, params)
                inseridos += 1
            except SQLAlchemyError as e:
                logger.exception("[/salvar] ERRO no item %s. Params acima. Detalhe: %s", i, e)
                raise

        db.commit()
        return {"ok": True, "id_tabela": int(id_tabela), "itens_inseridos": inseridos}

    except Exception as e:
        db.rollback()
        logger.exception("[/salvar] Falha geral: %s", e)
        # devolve uma mensagem útil pro front enquanto debuga
        raise HTTPException(status_code=500, detail=f"Erro ao salvar tabela_preco: {e}")
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
        "codigo_produto_supra","descricao_produto","embalagem","peso_liquido","valor_produto","comissao_aplicada","codigo_plano_pagamento",
        "valor_frete_aplicado","frete_kg","grupo","departamento","ipi","iva_st","valor_frete","valor_s_frete",
        "icms_st","ajuste_pagamento","descricao_fator_comissao",
            }

    for campo, valor in list(dados.items()):
        if campo in permitidos:
            setattr(produto, campo, valor)
        # ignora silenciosamente o resto (ex.: icms_st, validade_tabela, etc.)

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
              cnpj_cpf_faturamento_formatted AS cnpj_cpf,
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
                } for p in itens
            ]
        }
    

  

@router_meta.get("/validade_global")
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