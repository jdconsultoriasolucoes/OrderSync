import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(r"e:\OrderSync\.env")
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL and os.getenv("PROD_DB_URL"):
    DB_URL = os.getenv("PROD_DB_URL")
if not DB_URL:
    DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(DB_URL)

def verify():
    print("Verifying migration...")
    with engine.connect() as conn:
        # Check one record
        sql = text("""
            SELECT t.codigo_supra, t.id_familia, t.peso, t.status_produto, i.familia, i.peso_liquido, i.status_produto
            FROM t_cadastro_produto_v2 t
            JOIN ingestao_produto i ON t.codigo_supra = i.codigo_supra
            LIMIT 5
        """)
        rows = conn.execute(sql).mappings().all()
        for r in rows:
            print(f"Code: {r['codigo_supra']}")
            print(f"  Tabela   -> id_familia: {r['id_familia']}, peso: {r['peso']}, status: {r['status_produto']}")
            print(f"  Ingestao -> familia:    {r['familia']}, peso: {r['peso_liquido']}, status: {r['status_produto']}")
            print("-" * 20)

if __name__ == "__main__":
    verify()
