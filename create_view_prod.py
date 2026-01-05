import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(r"e:\OrderSync\.env")

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL and os.getenv("PROD_DB_URL"):
    DB_URL = os.getenv("PROD_DB_URL")

# Fallback string logic if env not loaded correctly contextually
if not DB_URL:
    DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(DB_URL)

sql_create_view = """
DROP VIEW IF EXISTS v_produto_v2_preco CASCADE;

CREATE OR REPLACE VIEW v_produto_v2_preco AS
SELECT
    p.id,
    p.codigo_supra,
    p.nome_produto,
    p.embalagem_venda,
    p.peso,
    p.preco,
    p.marca,
    p.familia,
    p.id_familia,
    p.fornecedor,
    p.tipo,
    p.validade_tabela,
    p.status_produto,
    p.unidade,
    COALESCE(i.ipi, 0.00) AS ipi,
    COALESCE(i.iva_st, 0.00) AS iva_st,
    COALESCE(i.icms, 0.00) AS icms
FROM t_cadastro_produto_v2 p
LEFT JOIN t_imposto_v2 i ON p.id = i.produto_id;
"""

print(f"Connecting to DB...")
with engine.connect() as conn:
    print("Creating view v_produto_v2_preco...")
    conn.execute(text(sql_create_view))
    conn.commit()
    print("View created successfully.")
