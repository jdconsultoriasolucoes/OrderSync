from models.pedido import PedidoModel
from services.pdf_service import gerar_pdf_pedido
from services.email_service import enviar_email_notificacao
from models.pedido_pdf import PedidoPdf, PedidoPdfItem
import base64
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
from models.produto import ProdutoV2

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
                p.peso_bruto,
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
        query = text("SELECT id_desconto, fator_comissao FROM t_desconto WHERE ativo IS TRUE ORDER BY id_desconto")
        resultado = db.execute(query).fetchall()
        return [{"codigo": row.id_desconto, "percentual": row.fator_comissao} for row in resultado]
    finally:
        db.close()

@router.get("/condicoes_pagamento")
def condicoes_pagamento():
    try:
        db = SessionLocal()
        query = text("select codigo_prazo, prazo, custo as taxa_condicao from t_condicoes_pagamento WHERE ativo IS TRUE order by codigo_prazo")
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

        # Helper: buscar status ATUAL na t_cadastro_produto_v2
        status_map = {}
        if itens:
             codigos = [i.codigo_produto_supra for i in itens if i.codigo_produto_supra]
             if codigos:
                 # Busca em lote
                rows_status = db.query(ProdutoV2.codigo_supra, ProdutoV2.status_produto).filter(
                    ProdutoV2.codigo_supra.in_(codigos),
                    ProdutoV2.fornecedor == cab.fornecedor
                ).all()
                
                # Logic to prioritized ATIVO
                # First pass: map all found statuses
                temp_status = {}
                for r in rows_status:
                    rs = (r.status_produto or "").upper()
                    if r.codigo_supra not in temp_status:
                        temp_status[r.codigo_supra] = rs
                    else:
                        # If we already have something that is NOT active, and this one IS active, overwrite.
                        # If we already have ACTIVE, keep it.
                        if temp_status[r.codigo_supra] != 'ATIVO' and rs == 'ATIVO':
                            temp_status[r.codigo_supra] = 'ATIVO'
                
                status_map = temp_status

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
                "status_atual": status_map.get(p.codigo_produto_supra, "DESCONHECIDO"), # <--- NOVO
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
    with SessionLocal() as db:
        # 1. Buscar dados da Tabela (Header + Itens)
        # ATUALIZADO: Buscar de t_cadastro_cliente_v2 para garantir dados recentes e email do comprador
        sql = text("""
            SELECT 
                t.*,
                c.cadastro_nome_fantasia as nome_fantasia,
                COALESCE(NULLIF(c.compras_email_resposavel, ''), c.faturamento_email_danfe) as cliente_email
            FROM tb_tabela_preco t
            LEFT JOIN t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa = t.codigo_cliente
            WHERE t.id_tabela = :tid AND t.ativo IS TRUE
        """)
        rows = db.execute(sql, {"tid": tabela_id}).mappings().all()
        
        if not rows:
            raise HTTPException(status_code=404, detail="Tabela de preço não encontrada ou vazia.")
        
        # Header (pega da primeira linha)
        head = rows[0]
        
        # Mapear itens da tabela por código para fácil acesso
        # (Chave: codigo_produto_supra)
        map_tbl_items = {r.get("codigo_produto_supra"): r for r in rows}
        
        # 2. Processar itens do Pedido (body.produtos tem qtd)
        itens_pdf = []
        total_valor = 0.0
        total_peso_bruto = 0.0
        total_peso_liq = 0.0
        total_frete = 0.0
        
        # Filtra apenas o que veio com quantidade > 0
        req_items = [i for i in body.produtos if i.quantidade > 0]
        
        if not req_items:
             raise HTTPException(status_code=400, detail="Nenhum item com quantidade informada.")

        for item_req in req_items:
            # Busca dados originais na tabela de preço
            original = map_tbl_items.get(item_req.codigo)
            if not original:
                continue # Item não existe na tabela, ignora
            
            qtd = item_req.quantidade
            
            # Dados básicos
            peso_liq_unit = float(original.get("peso_liquido") or 0)
            # Peso bruto não tem na tb_tabela_preco (v2)? Tem no join?
            # O select t.* pega peso_liquido. Peso bruto as vezes não está lá.
            # Vamos assumir igual ou buscar de produto se precisasse. 
            # Na view_file t_tabela_preco tinha peso_liquido.
            # O endpoint lista_preco usava 0.0. Vamos usar peso_liquido como fallback.
            peso_bruto_unit = peso_liq_unit # Fallback simplificado
            
            # Valores (usa s_frete ou com_frete?)
            # O front manda 'usar_valor_com_frete' na flag, mas o PDF geralmente mostra discriminado.
            # Vamos pegar os valores crus da tabela.
            val_s_frete = float(original.get("valor_s_frete") or 0)
            val_frete   = float(original.get("valor_frete") or 0)
            
            # Subtotais
            item_peso_bruto = peso_bruto_unit * qtd
            item_peso_liq   = peso_liq_unit * qtd
            item_total_val  = val_s_frete * qtd # Valor MERCADORIA
            item_total_frete= val_frete * qtd
            
            total_peso_bruto += item_peso_bruto
            total_peso_liq   += item_peso_liq
            total_valor      += item_total_val
            total_frete      += item_total_frete
            
            # Item PDF
            itens_pdf.append(PedidoPdfItem(
                codigo=original.get("codigo_produto_supra"),
                produto=original.get("descricao_produto"),
                embalagem=original.get("embalagem"),
                quantidade=qtd,
                condicao_pagamento=original.get("codigo_plano_pagamento"),
                tabela_comissao=original.get("descricao_fator_comissao"), # ou markup
                valor_retira=val_s_frete,
                valor_entrega=val_frete,
                markup=float(original.get("markup") or 0),
                valor_final_markup=float(original.get("valor_final_markup") or 0),
                valor_s_frete_markup=float(original.get("valor_s_frete_markup") or 0)
            ))

        # 3. Criar e Salvar Pedido no BD
        novo_pedido = PedidoModel(
            tabela_preco_id=tabela_id,
            tabela_preco_nome=head.get("nome_tabela"),
            codigo_cliente=head.get("codigo_cliente"),
            cliente=head.get("cliente"),
            # Tenta pegar email do join (cliente_email)
            # Como nao existe campo 'cliente_email' no PedidoModel, vamos por no contato_email ou ignorar
            # Mas o email_service usa pedido.cliente_email. Vamos injetar dinamicamente no objeto depois?
            # Ou salvar no campo contato_email se estiver vazio.
            contato_email=head.get("cliente_email"), 
            
            total_pedido=total_valor + total_frete, # Total Geral? Ou só mercadoria? Vamos somar frete se for CIF
            frete_total=total_frete,
            peso_total_kg=total_peso_liq, # ou bruto
            
            status="CONFIRMADO",
            confirmado_em=datetime.now(),
            created_at=datetime.now(),
            
            usar_valor_com_frete=body.usar_valor_com_frete,
            fornecedor=head.get("fornecedor")
        )
        db.add(novo_pedido)
        db.commit()
        db.refresh(novo_pedido)
        
        # 4. Gerar PDF
        # Busca validade global
        sql_val = text("SELECT MAX(CAST(validade_tabela AS DATE)) FROM t_cadastro_produto_v2 WHERE status_produto = 'ATIVO'")
        val_db = db.execute(sql_val).scalar()
        validade_fmt = val_db.strftime('%d/%m/%Y') if val_db else ""

        obj_pdf = PedidoPdf(
            id_pedido=novo_pedido.id,
            codigo_cliente=novo_pedido.codigo_cliente,
            cliente=novo_pedido.cliente,
            nome_fantasia=head.get("nome_fantasia"),
            data_pedido=novo_pedido.created_at,
            data_entrega_ou_retirada=None,
            frete_total=total_frete,
            frete_kg=float(head.get("frete_kg") or 0),
            validade_tabela=validade_fmt,
            total_peso_bruto=total_peso_bruto,
            total_peso_liquido=total_peso_liq,
            total_valor=total_valor + total_frete, # Total NFe
            observacoes=f"Pedido gerado via OrderSync a partir da tabela {tabela_id}.",
            itens=itens_pdf
        )
        
        try:
            pdf_bytes = gerar_pdf_pedido(obj_pdf, sem_validade=False)
            pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}")
            pdf_b64 = None

        # 5. Enviar Email (Background? Não, vamos tentar sync rapido ou deixar o serviço lidar)
        # Injetamos o email do cliente no objeto pedido para o serviço de email usar
        novo_pedido.cliente_email = head.get("cliente_email") 
        try:
            enviar_email_notificacao(db, novo_pedido, pdf_bytes=pdf_bytes)
        except Exception as e:
            logger.error(f"Erro ao enviar email no confirmar_pedido: {e}")

        return {
            "ok": True,
            "pedido_id": novo_pedido.id,
            "itens": len(itens_pdf),
            "pdf_base64": pdf_b64
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