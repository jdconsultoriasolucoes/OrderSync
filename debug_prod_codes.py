import os
from sqlalchemy import create_engine, text

PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(PROD_DB_URL)

with engine.connect() as conn:
    v1_codes = [r[0] for r in conn.execute(text("SELECT codigo FROM t_cadastro_produto LIMIT 20")).fetchall()]
    v2_codes = [r[0] for r in conn.execute(text("SELECT codigo_supra FROM t_cadastro_produto_v2 LIMIT 20")).fetchall()]
    
    print(f"Sample V1 Codes: {v1_codes}")
    print(f"Sample V2 Codes: {v2_codes}")
    
    # Check overlap count
    overlap = conn.execute(text("""
        SELECT COUNT(*) 
        FROM t_cadastro_produto v1 
        JOIN t_cadastro_produto_v2 v2 ON CAST(v1.codigo AS TEXT) = v2.codigo_supra
    """)).scalar()
    
    print(f"Overlap (V1 code = V2 supra): {overlap}")
