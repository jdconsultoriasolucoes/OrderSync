from fastapi import APIRouter, HTTPException
from typing import List
from schemas.cliente import ClienteCompleto, ClienteResumo
from services.cliente import (
    listar_clientes,
    obter_cliente,
    criar_cliente,
    atualizar_cliente,
    deletar_cliente
)
from fastapi import Depends
from core.deps import get_current_user
from models.usuario import UsuarioModel
from database import SessionLocal
from sqlalchemy import text

router = APIRouter()

@router.get("/", response_model=List[ClienteCompleto])
def get_clientes():
    return listar_clientes()

@router.get("/{codigo_da_empresa}/ultimas_compras")
def get_ultimas_compras(codigo_da_empresa: str):
    """Retorna as últimas 3 compras (pedidos) de um cliente, incluindo cancelados."""
    try:
        with SessionLocal() as db:
            rows = db.execute(text("""
                SELECT
                    a.id_pedido,
                    a.created_at,
                    a.total_pedido,
                    a.frete_total,
                    a.status,
                    COALESCE(a.tabela_preco_nome, b.nome_tabela) AS tabela_preco_nome
                FROM public.tb_pedidos a
                LEFT JOIN public.tb_tabela_preco b ON a.tabela_preco_id = b.id_tabela
                WHERE a.codigo_cliente = :codigo
                ORDER BY a.created_at DESC
                LIMIT 3
            """), {"codigo": codigo_da_empresa}).mappings().all()
        return [
            {
                "id_pedido": r["id_pedido"],
                "data": r["created_at"].strftime("%d/%m/%Y") if r["created_at"] else "-",
                "tabela_preco_nome": r["tabela_preco_nome"] or "-",
                "total_pedido": float(r["total_pedido"] or 0),
                "frete_total": float(r["frete_total"] or 0),
                "status": r["status"] or "-",
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar compras: {e}")

@router.get("/{codigo_da_empresa}/tabelas_preco")
def get_tabelas_preco_cliente(codigo_da_empresa: str):
    """Retorna as tabelas de preço ativas vinculadas ao codigo_cliente."""
    try:
        with SessionLocal() as db:
            rows = db.execute(text("""
                SELECT DISTINCT id_tabela, nome_tabela
                FROM tb_tabela_preco
                WHERE codigo_cliente = :codigo
                  AND ativo IS TRUE
                ORDER BY nome_tabela
            """), {"codigo": codigo_da_empresa}).mappings().all()
        return [
            {"id_tabela": r["id_tabela"], "nome_tabela": r["nome_tabela"]}
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar tabelas: {e}")

@router.get("/{codigo_da_empresa}", response_model=ClienteCompleto)
def get_cliente(codigo_da_empresa: str):
    cliente = obter_cliente(codigo_da_empresa)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente

@router.delete("/{codigo_da_empresa}", response_model=dict)
def delete_cliente(codigo_da_empresa: str, current_user: UsuarioModel = Depends(get_current_user)):
    success = deletar_cliente(codigo_da_empresa)
    if not success:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return {"message": "Cliente removido com sucesso"}

@router.post("/", response_model=ClienteCompleto)
def post_cliente(cliente: ClienteCompleto, current_user: UsuarioModel = Depends(get_current_user)):
    data = cliente.model_dump()
    data["criado_por"] = current_user.email
    data["atualizado_por"] = current_user.email
    return criar_cliente(data)

@router.put("/{codigo_da_empresa}", response_model=ClienteCompleto)
def put_cliente(codigo_da_empresa: str, cliente: ClienteCompleto, current_user: UsuarioModel = Depends(get_current_user)):
    data = cliente.model_dump()
    data["atualizado_por"] = current_user.email
    atualizado = atualizar_cliente(codigo_da_empresa, data)
    if not atualizado:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return atualizado
