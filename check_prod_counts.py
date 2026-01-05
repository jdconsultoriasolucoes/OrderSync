import os
from sqlalchemy import create_engine, text

PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(PROD_DB_URL)

tables_to_check = [
    "t_cadastro_produto_v2",
    "t_cadastro_cliente_v2",
    "tb_tabela_preco",
    "tb_pedidos",
    "t_usuario"
]

print("-- PROD DB ROW COUNTS --")
with engine.connect() as conn:
    for t in tables_to_check:
        try:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"{t}: {count} rows")
        except Exception as e:
            print(f"{t}: Error ({e})")
