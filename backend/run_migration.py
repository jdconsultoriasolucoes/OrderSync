import psycopg2

conn_str = "postgres://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

sql_create = """
CREATE TABLE IF NOT EXISTS tb_status_cadastro (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR UNIQUE
);
"""

sql_insert = """
INSERT INTO tb_status_cadastro (descricao)
SELECT DISTINCT cadastro_status_cadastro
FROM t_cadastro_cliente_v2
WHERE cadastro_status_cadastro IS NOT NULL
  AND cadastro_status_cadastro != ''
  AND cadastro_status_cadastro NOT IN (SELECT descricao FROM tb_status_cadastro)
ON CONFLICT (descricao) DO NOTHING;
"""

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute(sql_create)
    cur.execute(sql_insert)
    conn.commit()
    print("Migracao concluida com sucesso!")
except Exception as e:
    print(f"Erro: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
