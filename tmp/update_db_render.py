import psycopg2
from psycopg2.extras import RealDictCursor
import sys

# DSN providenciado pelo usuário
DSN = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def update_db():
    conn = None
    try:
        conn = psycopg2.connect(DSN)
        conn.autocommit = True
        cur = conn.cursor()

        print("1. Verificando e adicionando colunas (canal_id, canal_tipo, canal_linha) na t_cadastro_cliente_v2...")
        
        # Colunas a serem adicionadas
        columns_to_add = [
            ("canal_id", "INTEGER"),
            ("canal_tipo", "VARCHAR"),
            ("canal_linha", "VARCHAR")
        ]

        for col_name, col_type in columns_to_add:
            try:
                cur.execute(f"ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN {col_name} {col_type};")
                print(f" [+] Coluna {col_name} adicionada com sucesso.")
            except psycopg2.errors.DuplicateColumn:
                print(f" [!] Coluna {col_name} já existe na tabela t_cadastro_cliente_v2.")
                continue # Continua para a próxima

        print("\n2. Garantindo a existência das 5 novas tabelas de catálogo...")

        # tb_canal_venda
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tb_canal_venda (
                "Id" SERIAL PRIMARY KEY,
                tipo VARCHAR,
                linha VARCHAR
            );
        """)
        
        # tb_cidade_supervisor
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tb_cidade_supervisor (
                codigo SERIAL PRIMARY KEY,
                numero_supervisor_insumos FLOAT,
                nome_supervisor_insumos VARCHAR,
                numero_supervisor_pet FLOAT,
                nome_supervisor_pet VARCHAR,
                cidades VARCHAR NOT NULL,
                uf VARCHAR(2)
            );
        """)

        # tb_municipio_rota
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tb_municipio_rota (
                id SERIAL PRIMARY KEY,
                rota INTEGER,
                municipio VARCHAR,
                km VARCHAR
            );
        """)

        # tb_referencias
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tb_referencias (
                codigo SERIAL PRIMARY KEY,
                empresa VARCHAR,
                cidade VARCHAR,
                telefone VARCHAR,
                contato VARCHAR
            );
        """)

        # tb_supervisores
        # note o mapeamento "e-mail"
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tb_supervisores (
                id SERIAL PRIMARY KEY,
                codigo FLOAT,
                supervisores VARCHAR,
                tipo VARCHAR,
                telefone VARCHAR,
                "e-mail" VARCHAR
            );
        """)

        print(" [+] Verificação/Criação das 5 tabelas concluída.")
        
        cur.close()
        print("\n>>> Operação finalizada com sucesso! Todas as atualizações aplicadas diretamente no Render.")

    except Exception as e:
        print(f"Erro Crítico durante a atualização: {e}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    update_db()
