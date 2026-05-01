import os
from sqlalchemy import create_engine, text

url = 'postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo?sslmode=require'
engine = create_engine(url)

with engine.connect() as conn:
    res = conn.execute(text('SELECT id_tabela, observacao, manual_freight, valor_frete_aplicado FROM tb_tabela_preco ORDER BY id_tabela DESC LIMIT 1')).mappings().fetchone()
    print(dict(res) if res else "No rows")
