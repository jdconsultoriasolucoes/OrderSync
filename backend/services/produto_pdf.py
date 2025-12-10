# services/produtos_v2_service.py

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from datetime import date
from services.produto_regras import sincronizar_produtos_com_listas_ativas
from models.produto import ProdutoV2, ImpostoV2
from schemas.produto import (
    ProdutoV2Create,
    ProdutoV2Update,
    ImpostoV2Create,
    ProdutoV2Out,
    ImpostoV2Out,
)
import pandas as pd


# ----------------------------
# Helpers
# ----------------------------
def _row_to_out(db: Session, row: Dict[str, Any], include_imposto: bool = True) -> ProdutoV2Out:
    data = dict(row)
    if include_imposto and "id" in data:
        imp = db.query(ImpostoV2).filter(ImpostoV2.produto_id == data["id"]).one_or_none()
        if imp:
            data["imposto"] = ImpostoV2Out.model_validate(imp)
    return ProdutoV2Out(**data)


def _validate_business(update: Dict[str, Any]):
    # já validamos no Pydantic; aqui reforçamos regra de datas (caso PATCH parcial sem fim chegar setado)
    ini = update.get("data_desconto_inicio")
    fim = update.get("data_desconto_fim")

    if (ini and not fim) or (fim and not ini):
        raise HTTPException(422, detail="Preencha data_desconto_inicio e data_desconto_fim juntos")
    if ini and fim and ini > fim:
        raise HTTPException(422, detail="data_desconto_inicio deve ser <= data_desconto_fim")

    for campo in ("preco", "preco_tonelada", "desconto_valor_tonelada"):
        v = update.get(campo)
        if v is not None and v < 0:
            raise HTTPException(422, detail=f"{campo} não pode ser negativo")


# ----------------------------
# CRUD via ORM + leitura pela VIEW
# ----------------------------
def create_produto(db: Session, produto_in: ProdutoV2Create, imposto_in: Optional[ImpostoV2Create] = None) -> ProdutoV2Out:
    try:
        # 1) INSERT produto base
        obj = ProdutoV2(**produto_in.dict(exclude_unset=True))
        db.add(obj)
        db.flush()  # garante obj.id

        # 2) imposto (opcional)
        if imposto_in:
            imp = ImpostoV2(produto_id=obj.id, **imposto_in.dict(exclude_unset=True))
            db.add(imp)

        db.commit()
        db.refresh(obj)

    except Exception as e:
        db.rollback()
        # logue o erro para saber a raiz:
        # print(f"[create_produto] commit error: {e}")
        raise

    # 3) Tentar montar o retorno pela VIEW (se existir)
    try:
        row = db.execute(
            text("SELECT * FROM v_produto_v2_preco WHERE id = :id"),
            {"id": obj.id},
        ).mappings().first()
        if row:
            return ProdutoV2Out(**row)
    except Exception:
        # print(f"[create_produto] view fallback: {e}")
        pass

    # 4) Fallback: monta resposta a partir do ORM (sem view)
    imposto_out = None
    if obj.imposto:  # relacionamento 1–1
        imposto_out = ImpostoV2Out.from_orm(obj.imposto)

    return ProdutoV2Out(
        id=obj.id,
        codigo_supra=obj.codigo_supra,
        status_produto=obj.status_produto,
        nome_produto=obj.nome_produto,
        tipo_giro=obj.tipo_giro,
        estoque_disponivel=obj.estoque_disponivel,
        unidade=obj.unidade,
        peso=obj.peso,
        peso_bruto=obj.peso_bruto,
        estoque_ideal=obj.estoque_ideal,
        embalagem_venda=obj.embalagem_venda,
        unidade_embalagem=obj.unidade_embalagem,
        codigo_ean=obj.codigo_ean,
        codigo_embalagem=obj.codigo_embalagem,
        ncm=obj.ncm,
        fornecedor=obj.fornecedor,
        filhos=obj.filhos,
        familia=obj.familia,
        preco=obj.preco,
        preco_tonelada=obj.preco_tonelada,
        validade_tabela=obj.validade_tabela,
        desconto_valor_tonelada=obj.desconto_valor_tonelada,
        data_desconto_inicio=obj.data_desconto_inicio,
        data_desconto_fim=obj.data_desconto_fim,
        # calculados ficam None se não vierem da view/trigger:
        preco_final=None,
        reajuste_percentual=None,
        vigencia_ativa=None,
        # imposto:
        imposto=imposto_out,
        # snapshots anteriores (se tiver no modelo, deixe None):
        unidade_anterior=None,
        preco_anterior=None,
        preco_tonelada_anterior=None,
        validade_tabela_anterior=None,
    )


def update_produto(
    db: Session,
    produto_id: int,
    payload: ProdutoV2Update,
    imposto: Optional[ImpostoV2Create],
) -> ProdutoV2Out:
    obj = db.query(ProdutoV2).filter(ProdutoV2.id == produto_id).one_or_none()
    if not obj:
        raise HTTPException(404, detail="Produto não encontrado")

    update = payload.model_dump(exclude_unset=True)
    _validate_business(update)

    for k, v in update.items():
        setattr(obj, k, v)

    if imposto is not None:
        imp = db.query(ImpostoV2).filter(ImpostoV2.produto_id == produto_id).one_or_none()
        if imp:
            for k, v in imposto.model_dump(exclude_unset=True).items():
                setattr(imp, k, v)
        else:
            db.add(ImpostoV2(produto_id=produto_id, **imposto.model_dump(exclude_unset=True)))

    db.commit()

    row = db.execute(
        text("SELECT * FROM v_produto_v2_preco WHERE id = :id"),
        {"id": produto_id},
    ).mappings().first()
    return _row_to_out(db, row)


def get_produto(db: Session, produto_id: int) -> ProdutoV2Out:
    row = db.execute(
        text("SELECT * FROM v_produto_v2_preco WHERE id = :id"),
        {"id": produto_id},
    ).mappings().first()
    if not row:
        raise HTTPException(404, detail="Produto não encontrado")
    return _row_to_out(db, row)


def list_produtos(
    db: Session,
    q: Optional[str],
    status: Optional[str],
    familia: Optional[int],
    vigencia_em: Optional[date],
    limit: int,
    offset: int,
) -> List[ProdutoV2Out]:
    base = "SELECT * FROM v_produto_v2_preco WHERE 1=1"
    params: Dict[str, Any] = {}

    if q:
        base += " AND (nome_produto ILIKE :q OR codigo_supra ILIKE :q)"
        params["q"] = f"%{q}%"
    if status:
        base += " AND status_produto = :status"
        params["status"] = status
    if familia is not None:
        base += " AND familia = :familia"
        params["familia"] = familia
    if vigencia_em:
        base += " AND validade_tabela <= :vig"
        params["vig"] = vigencia_em

    base += " ORDER BY id DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    rows = db.execute(text(base), params).mappings().all()
    return [_row_to_out(db, r, include_imposto=False) for r in rows]


def get_anteriores(db: Session, produto_id: int) -> Dict[str, Any]:
    # lê direto da tabela base (não da view)
    row = db.execute(
        text(
            """
        SELECT preco_anterior, unidade_anterior, preco_tonelada_anterior, validade_tabela_anterior
        FROM t_cadastro_produto_v2 WHERE id = :id
    """
        ),
        {"id": produto_id},
    ).mappings().first()
    if not row:
        raise HTTPException(404, detail="Produto não encontrado")
    return dict(row)


def importar_lista_df(db: Session, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Faz upsert na t_cadastro_produto_v2 a partir do DataFrame da lista de preços.
    - chave de busca: codigo_supra (vem do campo 'codigo' do DF)
    - se não existir: cria produto novo com status 'ATIVO'
    - se existir: atualiza preço / fornecedor
    """
    inseridos = 0
    atualizados = 0

    for row in df.to_dict(orient="records"):
        codigo = row.get("codigo")
        descricao = row.get("descricao")
        fornecedor = row.get("fornecedor")
        preco_ton = row.get("preco_ton")
        preco_sc = row.get("preco_sc")

        if not codigo or not descricao:
            continue

        # procura produto pela chave única codigo_supra
        obj = (
            db.query(ProdutoV2)
            .filter(ProdutoV2.codigo_supra == codigo)
            .one_or_none()
        )

        if obj is None:
            # novo produto
            obj = ProdutoV2(
                codigo_supra=codigo,
                nome_produto=descricao,
                status_produto="ATIVO",  # se quiser outro padrão, muda aqui
            )
            inseridos += 1
            db.add(obj)
        else:
            atualizados += 1
            # mantém nome existente se você preferir:
            obj.nome_produto = descricao or obj.nome_produto

        # mapeia campos da lista pros campos do modelo
        if fornecedor:
            obj.fornecedor = fornecedor

        if preco_ton is not None:
            obj.preco_tonelada = preco_ton

        # aqui estou assumindo que preco_sc é o preço "unitário" da tabela
        if preco_sc is not None:
            obj.preco = preco_sc

        # se quiser usar 'familia' de texto num campo inteiro depois,
        # a gente trata num segundo momento (precisa do de-para).

    db.commit()

    return {
        "total_linhas": int(len(df)),
        "inseridos": inseridos,
        "atualizados": atualizados,
    }


# ----------------------------------------------------------------------
# Tabela intermediária t_preco_produto_pdf + fluxo de importação
# ----------------------------------------------------------------------
def limpar_preco_pdf_por_tipo(
    db: Session,
    lista: str,
    fornecedor: Optional[str] = None,
) -> None:
    """
    Em vez de DELETAR, marca como inativas (ativo = FALSE)
    todas as linhas da t_preco_produto_pdf_v2
    para o mesmo (lista, fornecedor).
    """
    lista = lista.upper().strip()
    conds = ["lista = :lista"]
    params: Dict[str, Any] = {"lista": lista}

    if fornecedor:
        conds.append("fornecedor = :fornecedor")
        params["fornecedor"] = fornecedor

    where_sql = " AND ".join(conds)

    sql = text(
        f"""
        UPDATE public.t_preco_produto_pdf_v2
           SET ativo = FALSE
         WHERE {where_sql}
           AND ativo = TRUE
        """
    )

    db.execute(sql, params)
    db.commit()


def salvar_t_preco_produto_pdf(
    db: Session,
    df: pd.DataFrame,
    nome_arquivo: Optional[str] = None,
    usuario: Optional[str] = None,
) -> None:
    """
    Insere o DataFrame na tabela t_preco_produto_pdf_v2.
    - Mantém histórico por data_ingestao.
    - Usa flag 'ativo' para marcar a carga atual.
    - Guarda nome do arquivo e usuário.
    """
    if df.empty:
        return

    sql = text(
        """
        INSERT INTO public.t_preco_produto_pdf_v2 (
            fornecedor,
            lista,
            familia,
            codigo,
            descricao,
            preco_ton,
            preco_sc,
            page,
            validade_tabela,
            data_ingestao,
            nome_arquivo,
            ativo,
            usuario
        )
        VALUES (
            :fornecedor,
            :lista,
            :familia,
            :codigo,
            :descricao,
            :preco_ton,
            :preco_sc,
            :page,
            :validade_tabela,
            :data_ingestao,
            :nome_arquivo,
            :ativo,
            :usuario
        )
        """
    )

    registros = df.to_dict(orient="records")

    for row in registros:
        # defaults
        row.setdefault("validade_tabela", None)
        row.setdefault("data_ingestao", date.today())
        row.setdefault("nome_arquivo", nome_arquivo)
        row.setdefault("ativo", True)
        row.setdefault("usuario", usuario)

        db.execute(sql, row)

    db.commit()

def importar_pdf_para_produto(
    db: Session,
    df: pd.DataFrame,
    nome_arquivo: Optional[str] = None,
    usuario: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fluxo completo para importação da lista:
      1) marcar como inativas as linhas antigas da t_preco_produto_pdf_v2
         para o mesmo (fornecedor, lista)
      2) salvar a nova ingestão (ativo = TRUE)
      3) sincronizar com t_cadastro_produto_v2 (atualizar, inativar, inserir)
    """
    if df.empty:
        return {"total_linhas": 0, "lista": None, "fornecedor": None, "sync": {}}

    # assume que toda a lista tem o mesmo "lista"/"fornecedor"
    lista = str(df["lista"].iloc[0]).upper().strip()
    fornecedor = None
    if "fornecedor" in df.columns and not pd.isna(df["fornecedor"].iloc[0]):
        fornecedor = str(df["fornecedor"].iloc[0]).strip() or None

    # 1) desativar cargas antigas daquele (fornecedor, lista)
    limpar_preco_pdf_por_tipo(db, lista=lista, fornecedor=fornecedor)

    # 2) salvar nova ingestão na intermediária, marcando ativo = TRUE
    salvar_t_preco_produto_pdf(
        db,
        df,
        nome_arquivo=nome_arquivo,
        usuario=usuario,
    )

    # 3) sincronizar produtos com a lista ativa
    resumo_sync = sincronizar_produtos_com_listas_ativas(
        db,
        fornecedor=fornecedor,
        lista=lista,
    )

    return {
        "lista": lista,
        "fornecedor": fornecedor,
        "total_linhas": int(len(df)),
        "sync": resumo_sync,
    }

