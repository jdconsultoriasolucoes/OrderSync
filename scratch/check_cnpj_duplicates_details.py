import os
from sqlalchemy import create_engine, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("=== DUPLICATES FOR CLEAN CNPJ '39292357000126' ===")
        res = conn.execute(text("SELECT id, cadastro_nome_cliente, cadastro_cnpj, cadastro_cpf, cadastro_ativo, cadastro_situacao FROM public.t_cadastro_cliente_v2 WHERE regexp_replace(cadastro_cnpj, '\\D', '', 'g') = '39292357000126'"))
        for row in res:
            print(row)

        print("\n=== DUPLICATES FOR CLEAN CNPJ '15158626000106' ===")
        res = conn.execute(text("SELECT id, cadastro_nome_cliente, cadastro_cnpj, cadastro_cpf, cadastro_ativo, cadastro_situacao FROM public.t_cadastro_cliente_v2 WHERE regexp_replace(cadastro_cnpj, '\\D', '', 'g') = '15158626000106'"))
        for row in res:
            print(row)

        print("\n=== DUPLICATES FOR CLEAN CNPJ '39326989000163' ===")
        res = conn.execute(text("SELECT id, cadastro_nome_cliente, cadastro_cnpj, cadastro_cpf, cadastro_ativo, cadastro_situacao FROM public.t_cadastro_cliente_v2 WHERE regexp_replace(cadastro_cnpj, '\\D', '', 'g') = '39326989000163'"))
        for row in res:
            print(row)

        print("\n=== DUPLICATES FOR CLEAN CNPJ '09055857000183' ===")
        res = conn.execute(text("SELECT id, cadastro_nome_cliente, cadastro_cnpj, cadastro_cpf, cadastro_ativo, cadastro_situacao FROM public.t_cadastro_cliente_v2 WHERE regexp_replace(cadastro_cnpj, '\\D', '', 'g') = '09055857000183'"))
        for row in res:
            print(row)

except Exception as e:
    print(f"Error: {e}")
