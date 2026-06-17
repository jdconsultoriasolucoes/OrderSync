import sqlalchemy
from sqlalchemy import create_engine, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("--- DESCONTOS ---")
        descontos = conn.execute(text("SELECT id_desconto, fator_comissao, ativo FROM t_desconto")).all()
        for d in descontos:
            print(d)
        
        print("\n--- CONDICOES ---")
        condicoes = conn.execute(text("SELECT codigo_prazo, prazo, custo, ativo FROM t_condicoes_pagamento")).all()
        for c in condicoes:
            print(c)
except Exception as e:
    print(f"Erro: {e}")
