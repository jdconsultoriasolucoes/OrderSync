from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta,date
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import SessionLocal  # usa seu database.py
from services.pedidos import (
    LISTAGEM_SQL, COUNT_SQL, RESUMO_SQL, ITENS_JSON_SQL,
    STATUS_SQL, STATUS_UPDATE_SQL, STATUS_EVENT_INSERT_SQL
)

import re

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])

from utils.string_utils import clean_client_name


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def normalizar_pedido_supra(pedido_supra_str: str, data_referencia=None) -> str:
    """
    Garante que o pedido_supra seja gravado no banco sempre com 10 dígitos (YYYY + 6 dígitos com zero padding).
    Ex: '2111' -> '2026002111' (usando o ano da data_referencia ou o ano atual do sistema).
    Ex: '2026002111' -> '2026002111' (mantém intacto).
    """
    if not pedido_supra_str:
        return ""
    
    # Remove qualquer caractere não numérico
    digits = "".join(filter(str.isdigit, str(pedido_supra_str)))
    if not digits:
        return ""
    
    # Se já tem 10 dígitos, retorna direto
    if len(digits) == 10:
        return digits
        
    # Se tiver menos que 10 dígitos (ex: 2111), completa com o ano
    # Determina o ano a partir da data de referência ou do ano atual do sistema local (2026)
    ano = "2026"
    if data_referencia:
        try:
            if hasattr(data_referencia, 'year'):
                ano = str(data_referencia.year)
            else:
                match = str(data_referencia).strip()[:4]
                if match.isdigit() and len(match) == 4:
                    ano = match
        except:
            pass
            
    # Limpa zeros à esquerda do sufixo para fazer o lpad correto de 6 dígitos
    sufixo = digits.lstrip('0')
    if not sufixo:
        sufixo = "0"
    
    # Trunca se passar de 6 dígitos
    if len(sufixo) > 6:
        sufixo = sufixo[-6:]
        
    return f"{ano}{sufixo.zfill(6)}"

# ---------- Schemas ----------
class PedidoListItem(BaseModel):
    numero_pedido: int
    data_pedido: datetime
    cliente_nome: str
    cliente_codigo: Optional[str] = None
    modalidade: str
    valor_total: float
    status_codigo: str
    tabela_preco_nome: Optional[str] = None
    fornecedor: Optional[str] = None
    link_url: Optional[str] = None
    link_status: Optional[str] = None
    link_enviado: bool
    peso_total: Optional[float] = 0.0
    municipio: Optional[str] = None
    rota_principal: Optional[str] = None
    pedido_supra: Optional[str] = None
    nota_fiscal: Optional[str] = None
    data_faturamento: Optional[datetime] = None

class ListagemResponse(BaseModel):
    data: List[PedidoListItem]
    page: int
    pageSize: int
    total: int

class PedidoItemResumo(BaseModel):
    codigo: str
    nome: Optional[str] = None
    embalagem: Optional[str] = None
    quantidade: float
    preco_unit: float
    preco_unit_frt: Optional[float] = None
    subtotal_sem_f: Optional[float] = None
    subtotal_com_f: Optional[float] = None
    manual_freight: Optional[bool] = False
    valor_frete_unitario: Optional[float] = 0.0
    markup: Optional[float] = 0.0
    valor_final_markup: Optional[float] = 0.0
    valor_s_frete_markup: Optional[float] = 0.0
    condicao_pagamento: Optional[str] = None
    tabela_comissao: Optional[str] = None
    peso_liquido_unit: Optional[float] = 0.0
    peso_liquido_total: Optional[float] = 0.0

class PedidoResumo(BaseModel):
    id_pedido: int
    codigo_cliente: Optional[str] = None
    cliente: str
    nome_fantasia: Optional[str] = None
    contato_nome: Optional[str] = None
    contato_email: Optional[str] = None
    contato_fone: Optional[str] = None
    cliente_telefone: Optional[str] = None
    cliente_celular: Optional[str] = None
    tabela_preco_nome: Optional[str] = None
    fornecedor: Optional[str] = None
    validade_ate: Optional[str] = None
    validade_dias: Optional[int] = None
    usar_valor_com_frete: bool
    calcula_st: Optional[bool] = False
    frete_kg: Optional[float] = 0.0
    peso_total_kg: float
    frete_total: float
    total_pedido: float
    valor_ajuste: Optional[float] = 0.0
    peso_liquido_calculado: Optional[float] = None
    peso_bruto_calculado: Optional[float] = None
    observacoes: Optional[str] = None
    status: str
    confirmado_em: Optional[datetime] = None
    cancelado_em: Optional[datetime] = None
    cancelado_motivo: Optional[str] = None
    link_url: Optional[str] = None
    link_primeiro_acesso_em: Optional[datetime] = None
    link_status: Optional[str] = None
    numero_carga: Optional[int] = None
    pedido_supra: Optional[str] = None
    nota_fiscal: Optional[str] = None
    created_at: datetime
    itens: List[PedidoItemResumo] = Field(default_factory=list)

class StatusEntry(BaseModel):
    codigo: str
    rotulo: str
    cor_hex: Optional[str] = None
    ordem: Optional[int] = None
    ativo: Optional[bool] = True

class StatusListResponse(BaseModel):
    data: List[StatusEntry]

class StatusChangeBody(BaseModel):
    para: str
    motivo: Optional[str] = None
    user_id: Optional[str] = None

class PedidoCamposFaturamento(BaseModel):
    pedido_supra: Optional[str] = None
    nota_fiscal: Optional[str] = None

class PedidoUpdateItem(BaseModel):
    codigo: str
    descricao: Optional[str] = None
    embalagem: Optional[str] = None
    condicao_pagamento: Optional[str] = None
    tabela_comissao: Optional[str] = None
    quantidade: float
    preco_unit: Optional[float] = None
    preco_unit_com_frete: Optional[float] = None
    peso_kg: Optional[float] = None
    manual_freight: Optional[bool] = False
    valor_frete_unitario: Optional[float] = 0.0
    frete_base_ton: Optional[float] = 0.0
    markup: Optional[float] = 0.0
    valor_final_markup: Optional[float] = 0.0
    valor_s_frete_markup: Optional[float] = 0.0

class PedidoUpdateRequest(BaseModel):
    usar_valor_com_frete: bool = True
    produtos: List[PedidoUpdateItem]
    observacoes: Optional[str] = None
    frete_kg: Optional[float] = 0.0
    pedido_supra: Optional[str] = None
    nota_fiscal: Optional[str] = None
    contato_nome: Optional[str] = None
    contato_email: Optional[str] = None
    contato_fone: Optional[str] = None
    calcula_st: Optional[bool] = False

# ---------- Routes ----------
def to_iso_or_none(v):
    if v is None:
        return None
    if isinstance(v, (date, datetime)):
        try:
            return v.isoformat()
        except Exception:
            return str(v)
    return str(v)

@router.get("", response_model=ListagemResponse)
def listar_pedidos(
    from_: Optional[str] = Query(None, alias="from"),  # "YYYY-MM-DD"
    to_:   Optional[str] = Query(None, alias="to"),    # "YYYY-MM-DD"
    status: Optional[str] = None,
    exclude_status: Optional[str] = None,
    tabela_nome: Optional[str] = None,
    cliente: Optional[str] = Query(None, description="busca em nome ou código"),
    fornecedor: Optional[str] = None,
    id_pedido: Optional[int] = Query(None, description="Filtrar por número exato do pedido"),
    pedido_supra: Optional[str] = None,
    nota_fiscal: Optional[str] = None,
    page: int = 1,
    pageSize: int = 25,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # 1. Paginação
    limit = pageSize
    offset = (page - 1) * pageSize
    if offset < 0:
        offset = 0

    # 2. Montar dinamicamente os filtros
    # quebra status em lista (se veio)
    status_list = [s.strip() for s in status.split(",") if s.strip()] if status else None
    
    filtros_sql = []
    params = {}

    # Só aplica filtro de data se fornecido OU se não houver filtros específicos de busca direta
    # Se id_pedido, pedido_supra ou nota_fiscal estiverem presentes, ignoramos as datas padrão
    tem_busca_direta = bool(id_pedido or pedido_supra or nota_fiscal)
    
    # Decisão: Só aplicamos datas se:
    # 1. Não há busca direta (ID, Supra, NF)
    # 2. OU se o usuário alterou as datas manualmente (comparar com o que seria o padrão no front?)
    # Na verdade, o mais seguro é: Se tem busca direta, ignoramos datas A MENOS que tenham sido passadas.
    # Mas como o front sempre passa, vamos ver se o front passou datas que NÃO são o padrão de 30 dias?
    # Melhor: Se tem busca direta, ignoramos datas por padrão.
    
    if (from_ or to_) and not tem_busca_direta:
        # Se não veio nada e não tem busca direta, aplica o padrão de 30 dias
        if not from_ or not to_:
            hoje = datetime.now()
            inicio = hoje - timedelta(days=30)
            from_str = inicio.strftime("%Y-%m-%d")
            to_str   = hoje.strftime("%Y-%m-%d")
        else:
            from_str = from_
            to_str = to_

        try:
            from_dt = datetime.strptime(from_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            limite_to = datetime.strptime(to_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0) + timedelta(days=1)
            
            filtros_sql.append("a.created_at >= :from")
            filtros_sql.append("a.created_at <  :to")
            params["from"] = from_dt
            params["to"] = limite_to
        except ValueError:
            pass # Ignora erro de formato de data
    elif (from_ and to_) and tem_busca_direta:
        # Se tem busca direta E o usuário passou datas, talvez ele queira filtrar por data TAMBÉM?
        # Por enquanto, se tem busca direta, vamos priorizar a busca global. 
        # Se quisermos ser super precisos, teríamos que saber se as datas são "padrão".
        pass

    if status_list:
        placeholders = ", ".join([f":st_{i}" for i in range(len(status_list))])
        filtros_sql.append(f"a.status IN ({placeholders})")
        for i, status_val in enumerate(status_list):
            params[f"st_{i}"] = status_val

    if exclude_status:
        ex_status_list = [s.strip() for s in exclude_status.split(",") if s.strip()]
        placeholders_ex = ", ".join([f":ex_st_{i}" for i in range(len(ex_status_list))])
        filtros_sql.append(f"a.status NOT IN ({placeholders_ex})")
        for i, status_val in enumerate(ex_status_list):
            params[f"ex_st_{i}"] = status_val

    if tabela_nome:
        filtros_sql.append("a.tabela_preco_nome ILIKE :tabela_nome")
        params["tabela_nome"] = f"%{tabela_nome}%"

    if cliente:
        filtros_sql.append("(a.cliente ILIKE :cliente_busca OR a.codigo_cliente ILIKE :cliente_busca)")
        params["cliente_busca"] = f"%{cliente}%"

    if fornecedor:
        filtros_sql.append("a.fornecedor ILIKE :fornecedor_busca")
        params["fornecedor_busca"] = f"%{fornecedor}%"

    if id_pedido:
        filtros_sql.append("a.id_pedido = :id_pedido_filtro")
        params["id_pedido_filtro"] = id_pedido

    if pedido_supra:
        filtros_sql.append("a.pedido_supra ILIKE :pedido_supra_busca")
        params["pedido_supra_busca"] = f"%{pedido_supra}%"

    if nota_fiscal:
        filtros_sql.append("a.nota_fiscal ILIKE :nota_fiscal_busca")
        params["nota_fiscal_busca"] = f"%{nota_fiscal}%"

    where_clause = " AND ".join(filtros_sql)

    # 6. montar SQL COUNT e LISTAGEM de forma segura
    count_sql = text(f"""
        SELECT COUNT(*) AS total
        FROM public.tb_pedidos a
        WHERE {where_clause}
    """)

    listagem_sql = text(f"""
        SELECT
          a.id_pedido                               AS numero_pedido,
          a.created_at                              AS data_pedido,
          COALESCE(c.cadastro_nome_cliente, a.cliente) AS cliente_nome,
          a.codigo_cliente                          AS cliente_codigo,
          CASE WHEN a.usar_valor_com_frete THEN 'ENTREGA' ELSE 'RETIRADA' END AS modalidade,
          a.total_pedido                            AS valor_total,
          a.status                                  AS status_codigo,
          a.status                                  AS status_codigo,
          a.tabela_preco_nome                       AS tabela_preco_nome,
          a.fornecedor                              AS fornecedor,
          a.link_url,
          a.link_status,
          (a.link_enviado_em IS NOT NULL)           AS link_enviado,
          COALESCE(a.peso_total_kg, 0)              AS peso_total,
          c.entrega_municipio                       AS municipio,
          c.entrega_rota_principal                 AS rota_principal,
          a.pedido_supra,
          a.nota_fiscal,
          a.data_faturamento
        FROM public.tb_pedidos a
        LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = a.codigo_cliente
        WHERE {where_clause}
        ORDER BY a.id_pedido DESC
        LIMIT :limit OFFSET :offset
    """)

    # adiciona paginação nos params da listagem
    params_listagem = {
        **params,
        "limit": limit,
        "offset": offset,
    }

    # 7. executa
    total_row = db.execute(count_sql, params).mappings().first()
    total = total_row["total"] if total_row and "total" in total_row else 0

    rows_raw = db.execute(listagem_sql, params_listagem).mappings().all()

    # 8. monta resposta
    rows = [
        PedidoListItem(
            numero_pedido      = r["numero_pedido"],
            data_pedido        = r["data_pedido"],
            cliente_nome       = clean_client_name(r["cliente_nome"]),
            cliente_codigo     = r["cliente_codigo"],
            modalidade         = r["modalidade"],
            valor_total        = r["valor_total"],
            status_codigo      = r["status_codigo"],
            tabela_preco_nome  = r["tabela_preco_nome"],
            fornecedor         = r["fornecedor"],
            link_url           = r["link_url"],
            link_status        = r["link_status"],
            link_enviado       = r["link_enviado"],
            peso_total         = float(r["peso_total"] or 0),
            municipio          = r.get("municipio"),
            rota_principal     = r.get("rota_principal"),
            pedido_supra       = r.get("pedido_supra"),
            nota_fiscal        = r.get("nota_fiscal"),
            data_faturamento   = r.get("data_faturamento")
        )
        for r in rows_raw
    ]

    return {
        "data": rows,
        "page": page,
        "pageSize": pageSize,
        "total": total,
    }

@router.get("/{id_pedido}/resumo", response_model=PedidoResumo)
def resumo_pedido(id_pedido: int, db: Session = Depends(get_db)):
    head = db.execute(RESUMO_SQL, {"id_pedido": id_pedido}).mappings().first()
    if not head:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    head_dict = dict(head)
    head_dict["cliente"] = clean_client_name(head_dict.get("cliente"))
    for k in ("validade_ate", "created_at", "atualizado_em", "data_prevista", "confirmado_em"):
        if k in head_dict:
            head_dict[k] = to_iso_or_none(head_dict[k])

    itens = db.execute(ITENS_JSON_SQL, {"id_pedido": id_pedido}).scalar() or []
    head_dict["itens"] = itens
    
    # Extract native PDF weight flow dynamically to keep single source of truth
    from services.pedido_pdf_data import carregar_pedido_pdf
    pdf_data = carregar_pedido_pdf(db, id_pedido)
    head_dict["peso_liquido_calculado"] = pdf_data.total_peso_liquido
    head_dict["peso_bruto_calculado"] = pdf_data.total_peso_bruto

    return PedidoResumo(**head_dict)

@router.put("/{id_pedido:int}")
def atualizar_pedido(
    id_pedido: int,
    body: PedidoUpdateRequest,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None)
):
    from models.pedido import PedidoModel
    import json
    
    # 1. Busca pedido e trava a linha (lock)
    pedido = db.query(PedidoModel).filter(PedidoModel.id == id_pedido).with_for_update().first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # 2. Verifica se o status permite edição (Aceita 'ORCAMENTO' ou 'ORÇAMENTO')
    status_atual = str(pedido.status).strip().upper()
    if status_atual not in ["ORCAMENTO", "ORÇAMENTO"]:
        raise HTTPException(status_code=400, detail="Apenas pedidos com status 'Orçamento' podem ser editados.")

    # 3. Recalcular os totais
    peso_total_kg = 0.0
    total_sem_frete = 0.0
    total_com_frete = 0.0

    for it in body.produtos:
        qtd = float(it.quantidade or 0)
        peso_total_kg += float(it.peso_kg or 0) * qtd
        total_sem_frete += float(it.preco_unit or 0) * qtd
        total_com_frete += float((it.preco_unit_com_frete if it.preco_unit_com_frete is not None else it.preco_unit) or 0) * qtd

    frete_total = max(0.0, total_com_frete - total_sem_frete)
    total_pedido = total_com_frete if body.usar_valor_com_frete else total_sem_frete

    # 4. Atualizar o cabeçalho do pedido
    pedido.usar_valor_com_frete = body.usar_valor_com_frete
    if body.calcula_st is not None:
        pedido.calcula_st = body.calcula_st
    pedido.observacoes = body.observacoes
    pedido.frete_kg = round(body.frete_kg or 0, 4)
    if body.pedido_supra is not None:
        dt_ref = pedido.confirmado_em or pedido.created_at or datetime.now()
        pedido.pedido_supra = normalizar_pedido_supra(body.pedido_supra, dt_ref)
    pedido.nota_fiscal = body.nota_fiscal
    if body.contato_nome is not None: pedido.contato_nome = body.contato_nome
    if body.contato_email is not None: pedido.contato_email = body.contato_email
    if body.contato_fone is not None: pedido.contato_fone = body.contato_fone
    pedido.peso_total_kg = round(peso_total_kg, 3)
    pedido.frete_total = round(frete_total, 2)
    pedido.total_sem_frete = round(total_sem_frete, 2)
    pedido.total_com_frete = round(total_com_frete, 2)
    pedido.total_pedido = round(total_pedido, 2)
    pedido.atualizado_em = datetime.now()
    
    db.add(pedido)
    print(f"[DEBUG] Atualizando pedido {id_pedido}: Peso={pedido.peso_total_kg}, Frete={pedido.frete_total}, Total={pedido.total_pedido}")

    # 5. Deletar os itens antigos da tabela tb_pedidos_itens
    db.execute(text("DELETE FROM public.tb_pedidos_itens WHERE id_pedido = :id_pedido"), {"id_pedido": id_pedido})

    # 6. Inserir os novos itens
    insert_item_sql = text("""
        INSERT INTO tb_pedidos_itens (
            id_pedido, codigo, nome, embalagem, peso_kg,
            condicao_pagamento, tabela_comissao,
            preco_unit, preco_unit_frt, valor_frete_unitario, frete_base_ton, quantidade,
            subtotal_sem_f, subtotal_com_f, manual_freight,
            markup, valor_final_markup, valor_s_frete_markup
        ) VALUES (
            :id_pedido, :codigo, :nome, :embalagem, :peso_kg,
            :condicao_pagamento, :tabela_comissao,
            :preco_unit, :preco_unit_frt, :valor_frete_unitario, :frete_base_ton, :quantidade,
            :subtotal_sem_f, :subtotal_com_f, :manual_freight,
            :markup, :valor_final_markup, :valor_s_frete_markup
        )
    """)

    for it in body.produtos:
        qtd = float(it.quantidade or 0)
        p_sem = float(it.preco_unit or 0)
        p_com = float((it.preco_unit_com_frete if it.preco_unit_com_frete is not None else it.preco_unit) or 0)
        
        # Se manual_freight for verdadeiro, usa frete_base_ton para calcular o frete unitário
        if bool(getattr(it, "manual_freight", False)):
            base_ton = float(it.frete_base_ton or 0)
            v_frete = round((base_ton / 1000.0) * float(it.peso_kg or 0), 2)
            v_frete_unitario_final = v_frete # No item, guardamos o resultado unitário
        else:
            v_frete = round(p_com - p_sem, 2)
            v_frete_unitario_final = v_frete

        db.execute(insert_item_sql, {
            "id_pedido": id_pedido,
            "codigo": (it.codigo or "")[:80],
            "nome": (it.descricao or "")[:255] or None,
            "embalagem": getattr(it, "embalagem", None),
            "peso_kg": float(it.peso_kg or 0),
            "condicao_pagamento": it.condicao_pagamento,
            "tabela_comissao": it.tabela_comissao,
            "preco_unit": round(p_sem, 2),
            "preco_unit_frt": round(p_sem + v_frete, 2),
            "valor_frete_unitario": v_frete_unitario_final,
            "frete_base_ton": float(it.frete_base_ton or 0),
            "quantidade": qtd,
            "subtotal_sem_f": round(p_sem * qtd, 2),
            "subtotal_com_f": round(p_com * qtd, 2),
            "manual_freight": bool(getattr(it, "manual_freight", False)),
            "markup": float(getattr(it, "markup", 0.0) or 0.0),
            "valor_final_markup": float(getattr(it, "valor_final_markup", 0.0) or 0.0),
            "valor_s_frete_markup": float(getattr(it, "valor_s_frete_markup", 0.0) or 0.0),
        })

    # 7. Logar evento de edição (usando a tabela de status_event como log geral)
    try:
        with db.begin_nested():
            db.execute(STATUS_EVENT_INSERT_SQL, {
                "pedido_id": id_pedido,
                "de_status": "ORCAMENTO",
                "para_status": "ORCAMENTO",
                "user_id": user_id or "sistema",
                "motivo": "Edição de itens do orçamento",
                "metadata": "{}"
            })
    except Exception:
        pass

    db.commit()

    # Retorna o PDF base64 do cliente para download imediato, igual na criação
    from services.pedido_pdf_data import carregar_pedido_pdf
    from services.pdf_service import gerar_pdf_pedido
    import base64
    
    try:
        obj_pdf_cliente = carregar_pedido_pdf(db, id_pedido)
        # Por padrão a criação envia "sem_validade=False"
        pdf_bytes_cliente = gerar_pdf_pedido(obj_pdf_cliente, sem_validade=False)
        pdf_b64 = base64.b64encode(pdf_bytes_cliente).decode('utf-8')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Erro ao gerar PDF atualizado: {e}")
        pdf_b64 = None

    return {
        "ok": True,
        "id": id_pedido,
        "pdf_base64": pdf_b64
    }

def verificar_e_historico_carga(db: Session, id_pedido: int, user_id: Optional[str]):
    try:
        # Garante que qualquer alteração ORM (como o pedido.status = 'CANCELADO') seja persistida
        # no banco de dados para que o SELECT abaixo consiga enxergá-la.
        db.flush()

        # Encontra as cargas onde esse pedido está
        cargas = db.execute(text("""
            SELECT DISTINCT c.id, c.is_historico 
            FROM tb_cargas c
            JOIN tb_cargas_pedidos cp ON cp.id_carga = c.id
            WHERE TRIM(cp.numero_pedido) = :id_pedido AND (c.is_historico IS NULL OR c.is_historico = FALSE)
        """), {"id_pedido": str(id_pedido).strip()}).fetchall()

        for carga_row in cargas:
            carga_id = carga_row[0]
            # Verifica se TODOS os pedidos dessa carga estão faturados ou cancelados
            # Usa TRIM() para evitar falso negativos com espaços adicionais
            todos_faturados = db.execute(text("""
                SELECT COUNT(*) as total_pendente
                FROM tb_cargas_pedidos cp
                JOIN tb_pedidos p ON TRIM(p.id_pedido::text) = TRIM(cp.numero_pedido)
                WHERE cp.id_carga = :carga_id
                  AND LOWER(TRIM(p.status)) NOT IN ('faturado supra', 'faturado dispet', 'cancelado')
            """), {"carga_id": carga_id}).scalar()

            if todos_faturados == 0:
                # Todos os pedidos da carga estão no status desejado, mover para histórico
                user_id_int = None
                if user_id and str(user_id).isdigit():
                    user_id_int = int(user_id)
                db.execute(text("""
                    UPDATE tb_cargas
                    SET is_historico = TRUE,
                        data_faturamento = now(),
                        faturado_por_id = :user_id
                    WHERE id = :carga_id
                """), {"carga_id": carga_id, "user_id": user_id_int})
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger("ordersync.errors")
        logger.error(f"Erro ao verificar histórico de carga {id_pedido}: {e}\n{traceback.format_exc()}")

@router.get("/status", response_model=StatusListResponse)

def listar_status(db: Session = Depends(get_db)):
    rows = db.execute(STATUS_SQL).mappings().all()
    data = [StatusEntry(**dict(r)) for r in rows]
    return StatusListResponse(data=data)

@router.post("/{id_pedido}/status")
def mudar_status(id_pedido: int, body: StatusChangeBody, db: Session = Depends(get_db)):
    # LOCK PESSIMISTA: Evita race condition se 2 pessoas alterarem status do mesmo pedido c/ milissegundos d diferença
    cur = db.execute(text("SELECT status FROM public.tb_pedidos WHERE id_pedido=:id FOR UPDATE"), {"id": id_pedido}).first()
    if not cur:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    de_status = cur[0]

    # VALIDAÇÃO DE FATURAMENTO: Bloqueia se o cliente não tem código da empresa
    status_faturamento = {"faturado supra", "faturado dispet"}
    if body.para and body.para.lower() in status_faturamento:
        resultado = db.execute(
            text("""
                SELECT c.cadastro_codigo_da_empresa
                FROM public.tb_pedidos p
                LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
                WHERE p.id_pedido = :id
            """),
            {"id": id_pedido}
        ).first()
        codigo_empresa = resultado[0] if resultado else None
        if not codigo_empresa or not str(codigo_empresa).strip():
            raise HTTPException(
                status_code=400,
                detail="O código da empresa não está preenchido. Por favor, complete o cadastro antes de faturar."
            )

    # Determinar atualizações adicionais de data dependendo do status manual
    extra_set = ""
    para_lower = str(body.para or "").lower().strip()
    if para_lower in ("faturado supra", "faturado dispet"):
        extra_set = ", data_faturamento = now()"
    elif para_lower == "cancelado":
        extra_set = ", cancelado_em = now()"
    elif para_lower in ("pedido", "confirmado"):
        extra_set = ", confirmado_em = now()"

    dynamic_status_update = text(f"""
        UPDATE public.tb_pedidos
        SET status = :para_status,
            atualizado_em = now(),
            atualizado_por = :user_id
            {extra_set}
        WHERE id_pedido = :id_pedido
        RETURNING id_pedido
    """)

    upd = db.execute(dynamic_status_update, {
        "para_status": body.para, 
        "id_pedido": id_pedido,
        "user_id": body.user_id
    }).first()
    if upd is None:
        raise HTTPException(status_code=400, detail="Falha ao atualizar status")

    # log (silencioso no MVP se tabela não existir)
    try:
        with db.begin_nested():
            db.execute(STATUS_EVENT_INSERT_SQL, {
                "pedido_id": id_pedido,
                "de_status": de_status,
                "para_status": body.para,
                "user_id": body.user_id,
                "motivo": body.motivo,
                "metadata": "{}"
            })
    except Exception:
        pass

    if body.para and body.para.lower() in ("faturado supra", "faturado dispet", "cancelado"):
        verificar_e_historico_carga(db, id_pedido, body.user_id)

    db.commit()
    return {"ok": True}

@router.patch("/{id_pedido}/campos_faturamento")
def atualizar_campos_faturamento(id_pedido: int, body: PedidoCamposFaturamento, db: Session = Depends(get_db)):
    from models.pedido import PedidoModel
    pedido = db.query(PedidoModel).filter(PedidoModel.id == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    if body.pedido_supra is not None:
        dt_ref = pedido.confirmado_em or pedido.created_at or datetime.now()
        pedido.pedido_supra = normalizar_pedido_supra(body.pedido_supra, dt_ref)
    if body.nota_fiscal is not None:
        pedido.nota_fiscal = body.nota_fiscal
        
    db.add(pedido)
    db.commit()
    return {"ok": True, "pedido_supra": pedido.pedido_supra, "nota_fiscal": pedido.nota_fiscal}

# ---------- Ações Extras (Cancelamento / Reenvio) ----------

from models.pedido import PedidoModel
from services.email_service import enviar_email_notificacao

@router.post("/{id_pedido}/cancelar")
def cancelar_pedido(id_pedido: int, db: Session = Depends(get_db), user_id: Optional[str] = Query(None)):
    """
    Cancela o pedido e registra no histórico (se possível).
    """
    # LOCK PESSIMISTA via ORM: .with_for_update() garante exclusão mutua para cancelar
    pedido = db.query(PedidoModel).filter(PedidoModel.id == id_pedido).with_for_update().first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if pedido.status == "CANCELADO":
        return {"message": "Pedido já estava cancelado", "status": "CANCELADO"}
    
    pedido.status = "CANCELADO"
    pedido.cancelado_em = datetime.now()
    
    # Tenta logar evento (opcional, igual ao mudar_status)
    # Tenta logar evento (opcional)
    try:
        with db.begin_nested():
            db.execute(STATUS_EVENT_INSERT_SQL, {
                "pedido_id": id_pedido,
                "de_status": "ANY",
                "para_status": "CANCELADO",
                "user_id": user_id or "sistema",
                "motivo": "Cancelado via Tela de Pedidos",
                "metadata": "{}"
            })
    except Exception:
        pass

    verificar_e_historico_carga(db, id_pedido, user_id or "sistema")
    
    db.commit()
    return {"message": "Pedido cancelado com sucesso", "status": "CANCELADO"}

from core.rate_limit import limiter
from models.background_task import BackgroundTaskModel

@router.post("/{id_pedido}/reenviar_email")
@limiter.limit("5/minute")
def reenviar_email_pedido(
    id_pedido: int, 
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Reenvia o e-mail de confirmação para o cliente em thread paralela via Worker Persistente.
    """
    pedido = db.query(PedidoModel).filter(PedidoModel.id == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Em vez do antigo BackgroundTasks que travava CPU, mandamos pro db queue
    nova_tarefa = BackgroundTaskModel(
        tipo_tarefa="ENVIO_EMAIL_CONFIRMACAO",
        referencia_id=id_pedido,
        status="PENDENTE",
        tentativas=0
    )
    db.add(nova_tarefa)
    db.commit()

    return {"message": "E-mail agendado para reenvio com sucesso (via fila)."}

@router.get("/debug_historico/{carga_id}")
def debug_historico_carga(carga_id: int, db: Session = Depends(get_db)):
    """ Endpoint temporário para debug de histórico """
    detalhes = db.execute(text("""
        SELECT cp.numero_pedido, p.status
        FROM tb_cargas_pedidos cp
        LEFT JOIN tb_pedidos p ON p.id_pedido::text = cp.numero_pedido
        WHERE cp.id_carga = :carga_id
    """), {"carga_id": carga_id}).mappings().all()
    
    pendentes = [
        dict(d) for d in detalhes 
        if (d["status"] or "").lower() not in ('faturado supra', 'faturado dispet', 'cancelado')
    ]
    
    return {
        "carga_id": carga_id,
        "todos_pedidos": [dict(d) for d in detalhes],
        "qdt_pendentes_python": len(pendentes),
        "pendentes_detalhes": pendentes
    }




# ---------- Criação de Pedido Manual (Admin/Vendedor) ----------
from pydantic import BaseModel, Field

class AdminCriarPedidoItem(BaseModel):
    codigo: str
    descricao: Optional[str] = None
    embalagem: Optional[str] = None
    condicao_pagamento: Optional[str] = None
    tabela_comissao: Optional[str] = None
    quantidade: float
    preco_unit: float
    preco_unit_com_frete: Optional[float] = None
    peso_kg: float
    markup: Optional[float] = 0.0
    valor_frete_unitario: Optional[float] = 0.0

class AdminCriarPedidoRequest(BaseModel):
    cliente: str
    codigo_cliente: str
    tabela_preco_id: Optional[str] = None
    observacao: Optional[str] = None
    usar_valor_com_frete: bool = True
    produtos: List[AdminCriarPedidoItem]

@router.post("/admin_criar")
def admin_criar_pedido(body: AdminCriarPedidoRequest, db: Session = Depends(get_db)):
    from models.pedido import PedidoModel
    from models.background_task import BackgroundTaskModel
    import json
    
    if not body.produtos:
        raise HTTPException(status_code=400, detail="Nenhum item informado no pedido")
        
    peso_total_kg = 0.0
    total_sem_frete = 0.0
    total_com_frete = 0.0

    for it in body.produtos:
        qtd = float(it.quantidade or 0)
        peso_total_kg += float(it.peso_kg or 0) * qtd
        total_sem_frete += float(it.preco_unit or 0) * qtd
        p_com = float((it.preco_unit_com_frete if it.preco_unit_com_frete is not None else it.preco_unit) or 0)
        total_com_frete += p_com * qtd

    frete_total = max(0.0, total_com_frete - total_sem_frete)
    total_pedido = total_com_frete if body.usar_valor_com_frete else total_sem_frete
    
    # Insert pedido
    agora = datetime.now()
    
    insert_sql = text("""
        INSERT INTO tb_pedidos (
            codigo_cliente, cliente, tabela_preco_id, tabela_preco_nome,
            usar_valor_com_frete, itens,
            peso_total_kg, frete_total, frete_kg, total_sem_frete, total_com_frete, total_pedido,
            observacoes, status, confirmado_em,
            link_status, link_enviado_em,
            criado_em, atualizado_em, created_at
        )
        VALUES (
            :codigo_cliente, :cliente, :tabela_preco_id, :tabela_preco_nome,
            :usar_valor_com_frete, CAST(:itens AS jsonb),
            :peso_total_kg, :frete_total, 0, :total_sem_frete, :total_com_frete, :total_pedido,
            :observacoes, 'Orçamento', :confirmado_em,
            'ABERTO', :agora,
            :agora, :agora, :agora
        )
        RETURNING id_pedido
    """)
    
    tid = body.tabela_preco_id if body.tabela_preco_id and str(body.tabela_preco_id).strip() else None
    
    tabela_id_final = int(tid) if tid and tid.isdigit() else 0
    tabela_nome_final = "Criação manual"
    
    if tabela_id_final > 0:
        nome_db = db.execute(text("SELECT nome_tabela FROM tb_tabela_preco WHERE id_tabela = :tid LIMIT 1"), {"tid": tabela_id_final}).scalar()
        if nome_db:
            tabela_nome_final = nome_db
            
    params = {
        "codigo_cliente": body.codigo_cliente[:80],
        "cliente": body.cliente.strip(),
        "tabela_preco_id": tabela_id_final,
        "tabela_preco_nome": tabela_nome_final,
        "usar_valor_com_frete": body.usar_valor_com_frete,
        "itens": json.dumps([i.dict() for i in body.produtos]),
        "peso_total_kg": round(peso_total_kg, 3),
        "frete_total": round(frete_total, 2),
        "total_sem_frete": round(total_sem_frete, 2),
        "total_com_frete": round(total_com_frete, 2),
        "total_pedido": round(total_pedido, 2),
        "observacoes": body.observacao,
        "confirmado_em": agora,
        "agora": agora
    }
    
    new_id = db.execute(insert_sql, params).scalar()
    
    # Insert itens
    insert_item_sql = text("""
        INSERT INTO tb_pedidos_itens (
            id_pedido, codigo, nome, embalagem, peso_kg,
            condicao_pagamento, tabela_comissao,
            preco_unit, preco_unit_frt, valor_frete_unitario, quantidade,
            subtotal_sem_f, subtotal_com_f,
            markup
        ) VALUES (
            :id_pedido, :codigo, :nome, :embalagem, :peso_kg,
            :condicao_pagamento, :tabela_comissao,
            :preco_unit, :preco_unit_frt, :valor_frete_unitario, :quantidade,
            :subtotal_sem_f, :subtotal_com_f,
            :markup
        )
    """)
    
    for it in body.produtos:
        qtd = float(it.quantidade or 0)
        p_sem = float(it.preco_unit or 0)
        p_com = float((it.preco_unit_com_frete if it.preco_unit_com_frete is not None else it.preco_unit) or 0)
        v_frete = float(it.valor_frete_unitario or round(p_com - p_sem, 2))
        
        db.execute(insert_item_sql, {
            "id_pedido": new_id,
            "codigo": (it.codigo or "")[:80],
            "nome": (it.descricao or "")[:255] or None,
            "embalagem": getattr(it, "embalagem", None),
            "peso_kg": float(it.peso_kg or 0),
            "condicao_pagamento": it.condicao_pagamento,
            "tabela_comissao": it.tabela_comissao,
            "preco_unit": round(p_sem, 2),
            "preco_unit_frt": round(p_com, 2),
            "valor_frete_unitario": v_frete,
            "quantidade": qtd,
            "subtotal_sem_f": round(p_sem * qtd, 2),
            "subtotal_com_f": round(p_com * qtd, 2),
            "markup": float(it.markup or 0.0)
        })
        
    db.commit()
    
    # Agendar envio do E-mail
    nova_tarefa = BackgroundTaskModel(
        tipo_tarefa="ENVIO_EMAIL_CONFIRMACAO",
        referencia_id=new_id,
        status="PENDENTE",
        tentativas=0
    )
    db.add(nova_tarefa)
    db.commit()
    
    return {
        "id_pedido": new_id,
        "status": "CRIADO"
    }
