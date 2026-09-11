import psycopg2

def run():
    print("Connecting to production DB...")
    conn = psycopg2.connect('postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync')
    cur = conn.cursor()
    
    print("Creating tb_logistica_auditoria table...")
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tb_logistica_auditoria (
                id SERIAL PRIMARY KEY,
                tipo_operacao VARCHAR(50) NOT NULL,
                id_original INTEGER NOT NULL,
                numero_identificador VARCHAR(100),
                data_criacao_original TIMESTAMP,
                data_finalizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_responsavel VARCHAR(255),
                snapshot_dados TEXT
            );
            CREATE INDEX IF NOT EXISTS ix_tb_logistica_auditoria_id_original ON tb_logistica_auditoria (id_original);
            CREATE INDEX IF NOT EXISTS ix_tb_logistica_auditoria_tipo_operacao ON tb_logistica_auditoria (tipo_operacao);
        """)
        conn.commit()
        print("Successfully created tb_logistica_auditoria table.")
    except Exception as e:
        conn.rollback()
        print(f"Error creating table: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run()
