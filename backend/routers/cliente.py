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

router = APIRouter()

@router.get("/", response_model=List[ClienteCompleto])
def get_clientes():
    return listar_clientes()

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


