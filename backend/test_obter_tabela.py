import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append('e:\\OrderSync - Dev\\backend')
from models.tabela_preco import TabelaPreco as TabelaPrecoModel

url = 'postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo?sslmode=require'
engine = create_engine(url)
SessionLocal = sessionmaker(bind=engine)

with SessionLocal() as db:
    cab = db.query(TabelaPrecoModel).filter_by(id_tabela=4, ativo=True).first()
    itens = db.query(TabelaPrecoModel).filter_by(id_tabela=4, ativo=True).all()
    
    if cab:
        print("Observacao:", getattr(cab, "observacao", ""))
        for p in itens:
            print(f"Produto: {p.codigo_produto_supra}")
            print(f"  manual_freight: {getattr(p, 'manual_freight', False)}")
            print(f"  valor_frete_aplicado: {p.valor_frete_aplicado}")
            break
