import psycopg2
from psycopg2 import sql

DSN = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS tb_canal_venda (
    "Id" SERIAL PRIMARY KEY,
    tipo VARCHAR,
    linha VARCHAR
);

CREATE TABLE IF NOT EXISTS tb_cidade_supervisor (
    codigo SERIAL PRIMARY KEY,
    numero_supervisor_insumos FLOAT,
    nome_supervisor_insumos VARCHAR,
    numero_supervisor_pet FLOAT,
    nome_supervisor_pet VARCHAR,
    cidades VARCHAR NOT NULL,
    uf VARCHAR(2)
);

CREATE TABLE IF NOT EXISTS tb_municipio_rota (
    id SERIAL PRIMARY KEY,
    rota INTEGER NOT NULL,
    municipio VARCHAR,
    km VARCHAR
);

CREATE TABLE IF NOT EXISTS tb_referencias (
    codigo SERIAL PRIMARY KEY,
    empresa VARCHAR NOT NULL,
    cidade VARCHAR,
    telefone VARCHAR,
    contato VARCHAR
);

CREATE TABLE IF NOT EXISTS tb_supervisores (
    id SERIAL PRIMARY KEY,
    codigo FLOAT,
    supervisores VARCHAR NOT NULL,
    tipo VARCHAR,
    telefone VARCHAR,
    email VARCHAR
);
"""

def create_tables():
    try:
        conn = psycopg2.connect(DSN)
        cur = conn.cursor()
        cur.execute(CREATE_TABLES)
        conn.commit()
        print("Tabelas de catálogo criadas com sucesso no Render DB!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")

if __name__ == "__main__":
    create_tables()
