import sqlalchemy
from sqlalchemy import create_engine, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

engine = create_engine(db_url, pool_pre_ping=True)

with engine.connect() as conn:
    print("Executando migração para adicionar coluna 'cadastro_status_cadastro'...")
    try:
        conn.execute(text("ALTER TABLE public.t_cadastro_cliente_v2 ADD COLUMN IF NOT EXISTS cadastro_status_cadastro VARCHAR;"))
        conn.commit()
        print("Coluna 'cadastro_status_cadastro' adicionada com sucesso ou já existente!")
    except Exception as e:
        print(f"Erro na migração: {e}")

    res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 't_cadastro_cliente_v2' AND column_name LIKE '%status%';"))
    print("\nColunas 'status' encontradas em t_cadastro_cliente_v2:")
    for row in res:
        print(f"  - {row[0]} ({row[1]})")
