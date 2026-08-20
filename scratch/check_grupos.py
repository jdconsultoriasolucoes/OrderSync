import sys
from sqlalchemy import create_engine, text

url = 'postgresql://jd_user:UsjVKivz7R6MlJFSxdNi9zfA8LNPJnIZ@dpg-d7nncm9j2pic73cmdor0-a.oregon-postgres.render.com/db_ordersync_work_gngo?sslmode=require'
engine = create_engine(url)
with engine.connect() as conn:
    rs = conn.execute(text("select distinct trim(marca) as grupo from t_cadastro_produto_v2 WHERE marca IS NOT NULL AND trim(marca) != '' order by trim(marca)"))
    
    with open(r"E:\OrderSync\scratch\grupos_saida.txt", "w", encoding="utf-8") as f:
        for row in rs:
            f.write(f"'{row[0]}'\n")
