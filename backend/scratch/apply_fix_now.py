import sys
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def apply_fix():
    engine = create_engine(DATABASE_URL)
    tables_to_fix = [
        ('tb_referencias', 'codigo'),
        ('tb_cidade_supervisor', 'codigo'),
        ('tb_canal_venda', 'Id'),
        ('tb_municipio_rota', 'id'),
        ('tb_supervisores', 'id')
    ]
    
    with engine.connect() as conn:
        # 1. Fix autoincrement
        for table, pk in tables_to_fix:
            try:
                # Verifica se já tem default (autoincrement)
                res = conn.execute(text(f"""
                    SELECT column_default 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{pk}'
                """)).scalar()
                
                if not res or 'nextval' not in str(res):
                    print(f"Configurando autoincremento para {table}.{pk}...")
                    seq_name = f"{table}_{pk.lower()}_seq"
                    conn.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq_name}"))
                    conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {pk} SET DEFAULT nextval('{seq_name}')"))
                    conn.execute(text(f"ALTER SEQUENCE {seq_name} OWNED BY {table}.{pk}"))
                    conn.execute(text(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX({pk}) FROM {table}), 0) + 1, false)"))
                    conn.commit()
                    print(f"Autoincremento configurado para {table}.")
                else:
                    print(f"{table}.{pk} já possui autoincremento.")
            except Exception as e:
                # conn.rollback() # connect doesn't have rollback like session, need to handle
                print(f"Erro ao configurar autoincremento em {table}: {e}")

        # 2. Add columns to tb_cidade_supervisor
        for col in ["gerente_insumos", "gerente_pet"]:
            try:
                conn.execute(text(f"SELECT {col} FROM tb_cidade_supervisor LIMIT 1"))
                print(f"Coluna {col} já existe em tb_cidade_supervisor.")
            except Exception:
                # conn.rollback()
                print(f"Adicionando coluna {col} em tb_cidade_supervisor...")
                try:
                    conn.execute(text(f"ALTER TABLE tb_cidade_supervisor ADD COLUMN {col} VARCHAR"))
                    conn.commit()
                except Exception as e:
                    print(f"Falha ao adicionar {col} em tb_cidade_supervisor: {e}")

if __name__ == "__main__":
    apply_fix()
