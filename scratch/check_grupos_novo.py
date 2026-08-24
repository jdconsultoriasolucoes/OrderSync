import sys
from sqlalchemy import create_engine, text

url = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
engine = create_engine(url)
with engine.connect() as conn:
    rs = conn.execute(text("select distinct marca from t_cadastro_produto_v2 WHERE marca IS NOT NULL AND marca != '' order by marca"))
    
    with open(r"E:\OrderSync\scratch\grupos_saida_novo.txt", "w", encoding="utf-8") as f:
        for row in rs:
            f.write(f"'{row[0]}'\n")
