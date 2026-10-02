from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg2://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
engine = create_engine(DATABASE_URL)

def run():
    with engine.begin() as conn:
        print("=== 1. ESTADO ATUAL ANTES DO AJUSTE ===")
        rows = conn.execute(text("SELECT id, numero_carga, nome_carga, is_retirada FROM tb_cargas ORDER BY id ASC")).mappings().all()
        for r in rows:
            print(f"ID: {r['id']:<3} | numero_carga: {str(r['numero_carga']):<5} | nome_carga: {str(r['nome_carga'])}")

        divergent = [r for r in rows if str(r['id']) != str(r['numero_carga']) and not r.get('is_retirada')]
        print(f"\nTotal de cargas divergentes encontradas: {len(divergent)}")

        if divergent:
            print("\n=== 2. EXECUTANDO UPDATE NO BANCO ===")
            # Atualiza em ordem decrescente de ID para evitar conflito na constraint UNIQUE de numero_carga
            for r in sorted(divergent, key=lambda x: x['id'], reverse=True):
                cid = r['id']
                old_num = r['numero_carga']
                new_num = str(cid)
                
                # Atualiza numero_carga
                conn.execute(
                    text("UPDATE tb_cargas SET numero_carga = :new_num WHERE id = :id"),
                    {"new_num": new_num, "id": cid}
                )
                
                # Se o nome_carga estava preenchido exatamente com o número antigo (ex: '42' no ID 43), atualiza o nome também
                conn.execute(
                    text("UPDATE tb_cargas SET nome_carga = :new_num WHERE id = :id AND nome_carga = :old_num"),
                    {"new_num": new_num, "old_num": old_num, "id": cid}
                )
                print(f"Carga ID {cid}: numero_carga atualizado de '{old_num}' -> '{new_num}'")

        # Ajusta a sequence do ID para que a próxima inserção seja MAX(id) + 1
        seq_val = conn.execute(text("""
            SELECT setval(pg_get_serial_sequence('tb_cargas', 'id'), COALESCE((SELECT MAX(id) FROM tb_cargas), 1), true)
        """)).scalar()
        print(f"\nSequence 'tb_cargas_id_seq' ajustada para: {seq_val}")

        print("\n=== 3. VERIFICAÇÃO FINAL APÓS O AJUSTE ===")
        verified = conn.execute(text("SELECT id, numero_carga, nome_carga, is_retirada FROM tb_cargas ORDER BY id ASC")).mappings().all()
        for r in verified:
            status = "OK (IGUAIS)" if str(r['id']) == str(r['numero_carga']) or r.get('is_retirada') else "DIVERGENTE"
            print(f"ID: {r['id']:<3} | numero_carga: {str(r['numero_carga']):<5} | nome_carga: {str(r['nome_carga']):<25} | Status: {status}")

if __name__ == "__main__":
    run()
