import sqlalchemy
from sqlalchemy import create_engine, inspect, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

engine = create_engine(db_url)
inspector = inspect(engine)

# Inspeciona colunas de t_cadastro_cliente_v2
columns = inspector.get_columns('t_cadastro_cliente_v2')
print("Colunas de t_cadastro_cliente_v2:")
for col in columns:
    # Se contiver 'situacao', 'status', 'ativo', etc.
    name = col['name'].lower()
    if any(k in name for k in ['situacao', 'status', 'ativo', 'sit', 'cond', 'bloq']):
        print(f"  -> {col['name']} ({col['type']})")
    else:
        print(f"  {col['name']} ({col['type']})")
