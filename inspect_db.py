import sqlalchemy
from sqlalchemy import create_engine, inspect

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

try:
    engine = create_engine(db_url)
    inspector = inspect(engine)
    columns = inspector.get_columns('t_cadastro_cliente_v2')
    
    print("Colunas encontradas na tabela t_cadastro_cliente_v2:")
    for col in columns:
        print(f"- {col['name']} ({col['type']})")
except Exception as e:
    print(f"Erro ao conectar ou ler tabela: {e}")
