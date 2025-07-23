from typing import List, Optional
from datetime import datetime
from db.fake_db import clientes_db

def listar_clientes() -> List[dict]:
    """
    Retorna apenas os campos essenciais para a listagem de clientes.
    """
    return [
        {
            "id": c.get("id"),
            "nome": c.get("cadastrocliente", {}).get("nome_cliente"),
            "cpf": c.get("cadastrocliente", {}).get("cpf"),
            "cnpj": c.get("cadastrocliente", {}).get("cnpj"),
            "email": c.get("responsavel_compras", {}).get("email_resposavel"),
            "estado": c.get("endereco_faturamento", {}).get("estado_faturamento"),
            "ativo": c.get("cadastrocliente", {}).get("ativo"),
        }
        for c in clientes_db
    ]

def obter_cliente(codigo_da_empresa: str) -> Optional[dict]:
    for cliente in clientes_db:
        if cliente.get("cadastrocliente", {}).get("codigo_da_empresa") == codigo_da_empresa:
            return cliente
    return None


def criar_cliente(cliente: dict) -> dict:
    novo_id = _gerar_proximo_id()
    cliente["id"] = novo_id
    cliente["data_criacao"] = datetime.utcnow()
    cliente["data_atualizacao"] = datetime.utcnow()

    # Garante que existe bloco cadastrocliente e campo obrigatório
    if "cadastrocliente" not in cliente or "codigo_da_empresa" not in cliente["cadastrocliente"]:
        raise ValueError("Campo 'cadastrocliente.codigo_da_empresa' é obrigatório")

    clientes_db.append(cliente)
    return cliente

def atualizar_cliente(codigo_da_empresa: str, cliente_atualizado: dict) -> Optional[dict]:
    for i, cliente in enumerate(clientes_db):
        if cliente.get("cadastrocliente", {}).get("codigo_da_empresa") == codigo_da_empresa:
            cliente_atualizado["id"] = cliente.get("id")
            cliente_atualizado.setdefault("cadastrocliente", {})["codigo_da_empresa"] = codigo_da_empresa
            cliente_atualizado["data_criacao"] = cliente.get("data_criacao")
            cliente_atualizado["data_atualizacao"] = datetime.utcnow()
            clientes_db[i] = cliente_atualizado
            return cliente_atualizado
    return None



def deletar_cliente(codigo_da_empresa: str) -> Optional[dict]:
    
    """
    ❗ Para desativar esta função, comente ou remova a chamada no router.
    ❗ Alternativamente, implemente um "soft delete" marcando o cliente como inativo.
    """
    for i, cliente in enumerate(clientes_db):
        if cliente.get("cadastrocliente", {}).get("codigo_da_empresa") == codigo_da_empresa:
            return clientes_db.pop(i)
    return None

 


def _gerar_proximo_id() -> int:
    """
    Gera o próximo ID com base nos clientes existentes.
    No futuro, essa função será substituída por uma consulta ao banco.
    """
    if not clientes_db:
        return 1
    return max(cliente.get("id", 0) for cliente in clientes_db) + 1
