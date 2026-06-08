import sqlalchemy
from sqlalchemy import create_engine, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

engine = create_engine(db_url)

with engine.connect() as conn:
    print("Contagem por cadastro_situacao:")
    res = conn.execute(text("SELECT cadastro_situacao, COUNT(*), cadastro_ativo FROM t_cadastro_cliente_v2 GROUP BY cadastro_situacao, cadastro_ativo ORDER BY COUNT(*) DESC"))
    for row in res:
        print(f"  Situação: {row[0]} | Ativo: {row[2]} | Qtd: {row[1]}")
