import os
from sqlalchemy import create_engine, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("=== TOTAL CLIENTS ===")
        res = conn.execute(text("SELECT COUNT(*) FROM public.t_cadastro_cliente_v2"))
        print(f"Total: {res.scalar()}")

        print("\n=== SAMPLE CNPJs ===")
        res = conn.execute(text("SELECT id, cadastro_nome_cliente, cadastro_cnpj, cadastro_cpf FROM public.t_cadastro_cliente_v2 WHERE cadastro_cnpj IS NOT NULL AND cadastro_cnpj != '' LIMIT 10"))
        for row in res:
            print(f"ID: {row[0]} | Name: {row[1]} | CNPJ: {repr(row[2])} | CPF: {repr(row[3])}")

        print("\n=== EMPTY OR NULL CNPJs AND CPFs ===")
        res_null_both = conn.execute(text("SELECT COUNT(*) FROM public.t_cadastro_cliente_v2 WHERE (cadastro_cnpj IS NULL OR cadastro_cnpj = '') AND (cadastro_cpf IS NULL OR cadastro_cpf = '')"))
        print(f"Clients with both CPF/CNPJ empty/null: {res_null_both.scalar()}")

        print("\n=== DUPLICATE CNPJs (RAW QUERY) ===")
        res_dup = conn.execute(text("""
            SELECT cadastro_cnpj, COUNT(*)
            FROM public.t_cadastro_cliente_v2
            WHERE cadastro_cnpj IS NOT NULL AND cadastro_cnpj != ''
            GROUP BY cadastro_cnpj
            HAVING COUNT(*) > 1
        """))
        dups = res_dup.fetchall()
        print(f"Found {len(dups)} duplicate CNPJ groups:")
        for row in dups:
            print(f"CNPJ: {repr(row[0])} | Count: {row[1]}")

        print("\n=== DUPLICATE CNPJs (CLEANED DIGITS) ===")
        res_clean_dup = conn.execute(text("""
            SELECT regexp_replace(cadastro_cnpj, '\\D', '', 'g') as clean_cnpj, COUNT(*)
            FROM public.t_cadastro_cliente_v2
            WHERE cadastro_cnpj IS NOT NULL AND cadastro_cnpj != ''
            GROUP BY clean_cnpj
            HAVING COUNT(*) > 1
        """))
        clean_dups = res_clean_dup.fetchall()
        print(f"Found {len(clean_dups)} duplicate clean CNPJ groups:")
        for row in clean_dups:
            print(f"Clean CNPJ: {repr(row[0])} | Count: {row[1]}")

except Exception as e:
    print(f"Error: {e}")
