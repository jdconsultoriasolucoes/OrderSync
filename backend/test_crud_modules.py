import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Setup paths to import backend models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.usuario import UsuarioModel
from models.fornecedor import Fornecedor
from models.produto import ProdutoV2
from models.cliente import ClienteModel
from models.tabela_preco import TabelaPreco
from models.pedido import PedidoModel

DB_URL = "postgresql://jd_user:ltryHa5XouJvN4rrmEnXerhB5aWPRVL1@dpg-d67lpugboq4c73828vg0-a.oregon-postgres.render.com/db_ordersync_jmyq"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def render_result(module_name, success, error=None):
    status = "PASS" if success else "FAIL"
    msg = "" if success else f" - Error: {error}"
    print(f"[{status}] {module_name}{msg}")

def test_crud_usuario(db):
    try:
        # Create
        new_user = UsuarioModel(nome="Test CRUD User", email="testcrud@example.com", senha_hash="testpass")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Read
        user = db.query(UsuarioModel).filter(UsuarioModel.email == "testcrud@example.com").first()
        if not user: raise Exception("Read failed")
        
        # Update
        user.nome = "Test CRUD User Updated"
        db.commit()
        
        # Delete
        db.delete(user)
        db.commit()
        
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)

def test_crud_fornecedor(db):
    try:
        new_forn = Fornecedor(id=999999, nome_fornecedor="Test CRUD Fornecedor")
        db.add(new_forn)
        db.commit()
        db.refresh(new_forn)
        
        forn = db.query(Fornecedor).filter(Fornecedor.id == new_forn.id).first()
        if not forn: raise Exception("Read failed")
        
        forn.nome_fornecedor = "Test CRUD Fornecedor Updated"
        db.commit()
        
        db.delete(forn)
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)

def test_crud_produto(db):
    try:
        new_prod = ProdutoV2(codigo_supra="TESTE_9999", status_produto="ATIVO", nome_produto="Test CRUD Produto")
        db.add(new_prod)
        db.commit()
        db.refresh(new_prod)
        
        prod = db.query(ProdutoV2).filter(ProdutoV2.id == new_prod.id).first()
        if not prod: raise Exception("Read failed")
        
        prod.nome_produto = "Test CRUD Produto Updated"
        db.commit()
        
        db.delete(prod)
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)

def test_crud_cliente(db):
    try:
        new_cli = ClienteModel(
            codigo_cliente="TEST_CLI", 
            nome_cliente="Test CRUD Cliente", 
            ativo=True,
            data_criacao=datetime.now(),
            data_atualizacao=datetime.now()
        )
        db.add(new_cli)
        db.commit()
        db.refresh(new_cli)
        
        cli = db.query(ClienteModel).filter(ClienteModel.id == new_cli.id).first()
        if not cli: raise Exception("Read failed")
        
        cli.nome_cliente = "Test CRUD Cliente Updated"
        db.commit()
        
        db.delete(cli)
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)

def test_crud_tabela_preco(db):
    try:
        new_tab = TabelaPreco(
            id_tabela=999999, nome_tabela="TABELA_TESTE", fornecedor="FORN", cliente="CLI",
            codigo_produto_supra="PROD_TESTE", descricao_produto="TESTE", embalagem="UN",
            peso_liquido=1.0, valor_produto=10.0, descricao_fator_comissao="TESTE", codigo_plano_pagamento="TESTE",
            grupo="GP", departamento="DP", ipi=0, icms_st=0, iva_st=0, valor_frete=0, valor_s_frete=0
        )
        db.add(new_tab)
        db.commit()
        db.refresh(new_tab)
        
        tab = db.query(TabelaPreco).filter(TabelaPreco.id_linha == new_tab.id_linha).first()
        if not tab: raise Exception("Read failed")
        
        tab.nome_tabela = "TABELA_TESTE_UPDATED"
        db.commit()
        
        db.delete(tab)
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)

def test_crud_pedido(db):
    try:
        new_ped = PedidoModel(
            tabela_preco_id=999999,
            tabela_preco_nome="TABELA_TESTE", 
            codigo_cliente="TEST_CLI",
            cliente="TEST CLI",
            status="CRIADO",
            usar_valor_com_frete=True
        )
        db.add(new_ped)
        db.commit()
        db.refresh(new_ped)
        
        ped = db.query(PedidoModel).filter(PedidoModel.id == new_ped.id).first()
        if not ped: raise Exception("Read failed")
        
        ped.status = "ATUALIZADO"
        db.commit()
        
        db.delete(ped)
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)

def main():
    print("Iniciando testes CRUD nos modulos do sistema...")
    db = SessionLocal()
    
    modules = {
        "Usuario": test_crud_usuario,
        "Fornecedor": test_crud_fornecedor,
        "ProdutoV2": test_crud_produto,
        "Cliente": test_crud_cliente,
        "TabelaPreco": test_crud_tabela_preco,
        "Pedido": test_crud_pedido
    }
    
    for mod_name, func in modules.items():
        succ, err = func(db)
        render_result(mod_name, succ, err)
        
    db.close()

if __name__ == "__main__":
    main()
