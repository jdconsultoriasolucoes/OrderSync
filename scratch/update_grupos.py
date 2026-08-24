import sys
from sqlalchemy import create_engine, text

url = 'postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync'
engine = create_engine(url)
with engine.connect() as conn:
    trans = conn.begin()
    try:
        res = conn.execute(text("UPDATE t_cadastro_produto_v2 SET marca = REGEXP_REPLACE(trim(marca), '\\s+', ' ', 'g') WHERE marca IS NOT NULL AND marca != REGEXP_REPLACE(trim(marca), '\\s+', ' ', 'g')"))
        print(f"Updated {res.rowcount} rows in t_cadastro_produto_v2")
        
        # Opcionalmente, podemos setar NaN para NULL ou 'Sem Grupo'
        res2 = conn.execute(text("UPDATE t_cadastro_produto_v2 SET marca = NULL WHERE UPPER(marca) = 'NAN'"))
        print(f"Updated {res2.rowcount} rows with NaN")
        
        trans.commit()
    except Exception as e:
        trans.rollback()
        print(e)
