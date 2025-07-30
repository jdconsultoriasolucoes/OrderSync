from fastapi import APIRouter, HTTPException
from models.tabela_preco import tabelapreco
from typing import List

router = APIRouter()

# Simula um banco de dados em memória
tabelas_de_preco_db: List[tabelapreco] = []


@router.post("/", response_model=tabelapreco)
def criar_tabela_preco(tabela: tabelapreco):
    tabela.id = len(tabelas_de_preco_db) + 1
    tabelas_de_preco_db.append(tabela)
    return tabela


@router.get("/", response_model=List[tabelapreco])
def listar_tabelas_preco():
    return tabelas_de_preco_db


@router.get("/{tabela_id}", response_model=tabelapreco)
def obter_tabela_preco(tabela_id: int):
    for tabela in tabelas_de_preco_db:
        if tabela.id == tabela_id:
            return tabela
    raise HTTPException(status_code=404, detail="Tabela de preço não encontrada")


@router.put("/{tabela_id}", response_model=tabelapreco)
def atualizar_tabela_preco(tabela_id: int, tabela_atualizada: tabelapreco):
    for idx, tabela in enumerate(tabelas_de_preco_db):
        if tabela.id == tabela_id:
            tabela_atualizada.id = tabela_id
            tabelas_de_preco_db[idx] = tabela_atualizada
            return tabela_atualizada
    raise HTTPException(status_code=404, detail="Tabela de preço não encontrada")


@router.delete("/{tabela_id}")
def deletar_tabela_preco(tabela_id: int):
    for idx, tabela in enumerate(tabelas_de_preco_db):
        if tabela.id == tabela_id:
            del tabelas_de_preco_db[idx]
            return {"message": "Tabela de preço deletada com sucesso"}
    raise HTTPException(status_code=404, detail="Tabela de preço não encontrada")
