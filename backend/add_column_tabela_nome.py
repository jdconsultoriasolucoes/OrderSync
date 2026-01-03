from sqlalchemy import create_engine, text
import os
import sys
sys.path.append(os.getcwd())
from database import SessionLocal

db = SessionLocal()
try:
    print("Verificando se a coluna tabela_preco_nome existe...")
    check = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='tb_pedidos' AND column_name='tabela_preco_nome'")).scalar()
    
    if check:
        print("Coluna tabela_preco_nome JÁ EXISTE.")
    else:
        print("Adicionando coluna tabela_preco_nome...")
        db.execute(text("ALTER TABLE tb_pedidos ADD COLUMN tabela_preco_nome VARCHAR(255);"))
        db.commit()
        print("Coluna adicionada com SUCESSO.")
        
except Exception as e:
    print(f"Erro ao migrar banco: {e}")
    db.rollback()
finally:
    db.close()
