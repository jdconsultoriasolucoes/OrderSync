import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

url = 'postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo?sslmode=require'
engine = create_engine(url)
SessionLocal = sessionmaker(bind=engine)

with SessionLocal() as db:
    # Get table 4 header
    cab = db.execute(text("SELECT * FROM tb_tabela_preco WHERE id_tabela = 4 AND ativo = True LIMIT 1")).mappings().fetchone()
    if cab:
        print("Header:")
        print("observacao:", cab.get('observacao'))
        
        itens = db.execute(text("SELECT * FROM tb_tabela_preco WHERE id_tabela = 4 AND ativo = True ORDER BY id_linha")).mappings().fetchall()
        print("\nItems:")
        for item in itens:
            print(f"Produto: {item.get('codigo_produto_supra')}")
            print(f"  manual_freight: {item.get('manual_freight')}")
            print(f"  valor_frete_aplicado: {item.get('valor_frete_aplicado')}")
            print(f"  markup: {item.get('markup')}")
    else:
        print("Table 4 not found.")
