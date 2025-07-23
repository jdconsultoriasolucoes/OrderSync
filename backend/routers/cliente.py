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

router = APIRouter()

@router.get("/", response_model=List[ClienteResumo])
def get_clientes():
    return listar_clientes()

@router.get("/{codigo_da_empresa}", response_model=ClienteCompleto)
def get_cliente(codigo_da_empresa: str):
    cliente = obter_cliente(codigo_da_empresa)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente

@router.delete("/{codigo_da_empresa}", response_model=ClienteCompleto)
def delete_cliente(codigo_da_empresa: str):
    cliente = deletar_cliente(codigo_da_empresa)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente

@router.post("/", response_model=ClienteCompleto)
def post_cliente(cliente: ClienteCompleto):
    return criar_cliente(cliente.model_dump())

@router.put("/{codigo_da_empresa}", response_model=ClienteCompleto)
def put_cliente(codigo_da_empresa: str, cliente: ClienteCompleto):
    atualizado = atualizar_cliente(codigo_da_empresa, cliente.model_dump())
    if not atualizado:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return atualizado


