from typing import List, Optional, Any, Dict
from schemas.tabela_preco import ParametrosCalculo, ProdutoCalculado, TabelaSalvar
from datetime import date, datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.tabela_preco import TabelaPreco as TabelaPrecoModel
import logging
import re

logger = logging.getLogger("tabela_preco_service")

# --- Mantendo função original ---
def calcular_valores_dos_produtos(payload: ParametrosCalculo) -> List[ProdutoCalculado]:
    resultado = []

    for produto in payload.produtos:
        valor = produto.valor
        peso_liquido = produto.peso_liquido or 0.0
        # Tenta pegar peso_bruto do payload, se não tiver, usa o liquido
        peso_bruto = getattr(produto, "peso_bruto", 0.0) or 0.0
        
        peso_para_frete = peso_bruto if peso_bruto > 0 else peso_liquido

        is_pet = (str(produto.tipo or "").strip().lower() == "pet")
        ipi_item = (produto.ipi or 0.0) if (is_pet and peso_liquido <= 10) else 0.0
        
        iva_st = produto.iva_st or 0.0

        frete_kg = (payload.frete_unitario / 1000) * peso_para_frete
        ajuste_pagamento = valor * payload.acrescimo_pagamento
        comissao_aplicada = valor * payload.fator_comissao

        base = valor + frete_kg + ajuste_pagamento - comissao_aplicada 
        valor_liquido = base + ((base * ipi_item) + (base * iva_st))

        resultado.append(ProdutoCalculado(
            **produto.dict(),
            frete_kg=round(frete_kg, 4),
            ajuste_pagamento=round(ajuste_pagamento, 4),
            comissao_aplicada=round(comissao_aplicada, 4),
            valor_liquido=round(valor_liquido, 2),
            ))

    return resultado

# --- Novas Funções (Sync) ---

def create_tabela(db: Session, body: TabelaSalvar, usuario_email: str) -> Dict[str, Any]:
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
              ipi, icms_st, iva_st, calcula_st, criacao_usuario, alteracao_usuario, markup,
              valor_final_markup, valor_s_frete_markup
            ) VALUES (
              :id_tabela, :nome_tabela, :fornecedor, :codigo_cliente, :cliente,
              :codigo_produto_supra, :descricao_produto, :embalagem, :peso_liquido, :valor_produto,
              :comissao_aplicada, :ajuste_pagamento, :descricao_fator_comissao, :codigo_plano_pagamento,
              :valor_frete_aplicado, :frete_kg, :valor_frete, :valor_s_frete, :grupo, :departamento,
              :ipi, :icms_st, :iva_st, :calcula_st, :criacao_usuario, :alteracao_usuario, :markup,
              :valor_final_markup, :valor_s_frete_markup
            )
            RETURNING id_linha
        """)

        logger.info("[create_tabela] header id=%s nome=%s cliente=%s", id_tabela, body.nome_tabela, body.cliente)

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
                "calcula_st": bool(getattr(body, "calcula_st", False)),
                "criacao_usuario": usuario_email,
                "alteracao_usuario": usuario_email,
                "markup": float(getattr(produto, "markup", 0) or 0),
                "valor_final_markup": float(getattr(produto, "valor_final_markup", 0) or 0),
                "valor_s_frete_markup": float(getattr(produto, "valor_s_frete_markup", 0) or 0),
            }

            try:
                db.execute(insert_sql, params)
                inseridos += 1
            except SQLAlchemyError as e:
                logger.exception("[create_tabela] ERRO no item %s. Params acima. Detalhe: %s", i, e)
                raise

        db.commit()
        return {"ok": True, "id_tabela": int(id_tabela), "itens_inseridos": inseridos}

    except Exception as e:
        db.rollback()
        logger.exception("[create_tabela] Falha geral: %s", e)
        raise e

def update_tabela(db: Session, id_tabela: int, body: TabelaSalvar, usuario_email: str) -> Dict[str, Any]:
    try:
        now = datetime.utcnow()
        existentes = db.query(TabelaPrecoModel).filter(
            TabelaPrecoModel.id_tabela == id_tabela
        ).all()
        
        if not existentes:
            # Retorna None para indicar 404 (caller deve tratar)
            return None

        por_id = {r.id_linha: r for r in existentes}
        por_codigo = { (r.codigo_produto_supra or "").strip(): r for r in existentes if (r.codigo_produto_supra or "").strip() }

        # Update Cabeçalho (em todas as linhas)
        for r in existentes:
            r.nome_tabela    = body.nome_tabela
            r.cliente        = body.cliente
            # Proteção: só atualiza codigo_cliente se vier preenchido
            if body.codigo_cliente:
                r.codigo_cliente = body.codigo_cliente
            elif not r.codigo_cliente:
                # Se não tem nada no banco, define padrão
                r.codigo_cliente = "Não cadastrado"
            
            r.fornecedor     = body.fornecedor or ""
            r.calcula_st     = bool(getattr(body, "calcula_st", False))
            r.editado_em     = now

        # Filtra itens válidos
        produtos_validos = []
        for p in (body.produtos or []):
            cod = (getattr(p, "codigo_produto_supra", "") or "").strip()
            if not cod: continue
            if cod.lower() == "string": continue
            
            desc = (getattr(p, "descricao_produto", "") or "").strip()
            if not desc or desc.lower() == "string": continue
            
            p.codigo_produto_supra = cod
            p.codigo_plano_pagamento = (getattr(p, "codigo_plano_pagamento", "") or "").strip()
            produtos_validos.append(p)

        enviados_codigos = set()
        novos = atualizados = reativados = 0

        for p in produtos_validos:
            cod = p.codigo_produto_supra
            enviados_codigos.add(cod)

            target = None
            p_id_linha = getattr(p, "id_linha", None)
            if p_id_linha is not None:
                target = por_id.get(p_id_linha)
            if target is None:
                target = por_codigo.get(cod)

            if target is not None:
                # UPDATE
                target.descricao_produto        = p.descricao_produto
                target.embalagem                = (p.embalagem or "")
                target.peso_liquido             = (p.peso_liquido or 0)
                target.valor_produto            = (p.valor_produto or 0)
                target.comissao_aplicada        = (p.comissao_aplicada or 0)
                target.ajuste_pagamento         = (p.ajuste_pagamento or 0)
                target.descricao_fator_comissao = (p.descricao_fator_comissao or "")
                target.codigo_plano_pagamento   = p.codigo_plano_pagamento
                target.valor_frete_aplicado     = (p.valor_frete_aplicado or 0)
                
                # Logic for frete_kg fallback
                if getattr(p, "frete_kg", None) is not None:
                    target.frete_kg = p.frete_kg
                else:
                     target.frete_kg = getattr(body, "frete_kg", None) or 0

                target.valor_frete              = (getattr(p, "valor_frete", None) or 0)
                target.valor_s_frete            = (p.valor_s_frete or 0)
                target.grupo                    = getattr(p, "grupo", None)
                target.departamento             = getattr(p, "departamento", None)
                target.ipi                      = (p.ipi or 0)
                target.icms_st                  = (p.icms_st or 0)
                target.iva_st                   = (p.iva_st or 0)
                target.calcula_st               = bool(getattr(body, "calcula_st", False))
                target.markup                   = (p.markup or 0)
                target.valor_final_markup       = (p.valor_final_markup or 0)
                target.valor_s_frete_markup     = (p.valor_s_frete_markup or 0)
                
                if not target.ativo:
                    target.ativo = True
                    target.deletado_em = None
                    reativados += 1
                else:
                    atualizados += 1
                target.editado_em = now
                target.alteracao_usuario = usuario_email
            else:
                # INSERT
                db.add(TabelaPrecoModel(
                    id_tabela            = id_tabela,
                    nome_tabela          = body.nome_tabela,
                    cliente              = body.cliente,
                    codigo_cliente       = body.codigo_cliente or "Não cadastrado",
                    fornecedor           = body.fornecedor or "",
                    codigo_produto_supra = cod,
                    descricao_produto    = p.descricao_produto,
                    embalagem            = (p.embalagem or ""),
                    peso_liquido         = (p.peso_liquido or 0),
                    valor_produto        = (p.valor_produto or 0),
                    comissao_aplicada    = (p.comissao_aplicada or 0),
                    ajuste_pagamento     = (p.ajuste_pagamento or 0),
                    descricao_fator_comissao = (p.descricao_fator_comissao or ""),
                    codigo_plano_pagamento   = p.codigo_plano_pagamento,
                    valor_frete_aplicado = (p.valor_frete_aplicado or 0),
                    frete_kg             = (getattr(p, "frete_kg", None) if getattr(p, "frete_kg", None) is not None else getattr(body, "frete_kg", None) or 0),
                    valor_frete          = (getattr(p, "valor_frete", None) or 0),
                    valor_s_frete        = (p.valor_s_frete or 0),
                    grupo                = getattr(p, "grupo", None),
                    departamento         = getattr(p, "departamento", None),
                    ipi                  = (p.ipi or 0),
                    icms_st              = (p.icms_st or 0),
                    iva_st               = (p.iva_st or 0),
                    calcula_st           = bool(getattr(body, "calcula_st", False)),
                    markup               = (p.markup or 0),
                    valor_final_markup   = (p.valor_final_markup or 0),
                    valor_s_frete_markup = (p.valor_s_frete_markup or 0),
                    ativo                = True,
                    deletado_em          = None,
                    editado_em           = now,
                    criacao_usuario      = usuario_email,
                    alteracao_usuario    = usuario_email,
                ))
                novos += 1

        # Soft Delete
        removidos = 0
        for r in existentes:
            cod_exist = (r.codigo_produto_supra or "").strip()
            if r.ativo and cod_exist and cod_exist not in enviados_codigos:
                r.ativo = False
                r.deletado_em = now
                r.editado_em  = now
                removidos += 1

        db.commit()
        return {
            "ok": True,
            "tabela_id": id_tabela,
            "novos": novos,
            "reativados": reativados,
            "atualizados": atualizados,
            "removidos": removidos
        }
    except Exception as e:
        db.rollback()
        raise e