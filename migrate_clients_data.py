
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

with engine.connect() as conn:
    print("Starting migration...")
    
    # 1. Add column tipo_pessoa to t_cadastro_cliente_v2 if not exists
    print("Checking/Adding 'tipo_pessoa' column...")
    try:
        conn.execute(text("ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN IF NOT EXISTS tipo_pessoa VARCHAR;"))
        conn.commit()
        print("Column 'tipo_pessoa' checked/added.")
    except Exception as e:
        print(f"Error adding column: {e}")
        conn.rollback()

    # 2. Update data
    print("Updating data from t_cadastro_cliente...")
    try:
        # We need to update existing rows in v2 based on matching CNPJ in v1
        # Mapping:
        # v2.cadastro_atividade_principal = v1.atividade_principal
        # v2.cadastro_codigo_da_empresa = v1.codigo
        # v2.cadastro_tipo_cliente = v1.ramo_juridico
        # v2.tipo_pessoa = v1.tipo_pessoa
        
        sql = text("""
            UPDATE t_cadastro_cliente_v2 v2
            SET 
                cadastro_atividade_principal = v1.atividade_principal,
                cadastro_codigo_da_empresa = v1.codigo,
                cadastro_tipo_cliente = v1.ramo_juridico,
                tipo_pessoa = v1.tipo_pessoa
            FROM t_cadastro_cliente v1
            WHERE v2.cadastro_cnpj = v1.cnpj_cpf_faturamento
        """)
        
        result = conn.execute(sql)
        conn.commit()
        print(f"Rows updated: {result.rowcount}")
        
    except Exception as e:
        print(f"Error updating data: {e}")
        conn.rollback()

    print("Migration finished.")
