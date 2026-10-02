from sqlalchemy import create_engine, text

url = "postgresql+psycopg2://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
engine = create_engine(url)

with engine.begin() as conn:
    print("--- 1. Current State Before Update ---")
    rows = conn.execute(text("SELECT id, numero_carga, nome_carga, is_retirada FROM tb_cargas ORDER BY id DESC LIMIT 10")).mappings().all()
    for r in rows:
        print(f"ID: {r['id']} | num: {r['numero_carga']} | nome: {r['nome_carga']}")

    # Update in descending order to avoid temporary collisions on UNIQUE constraint
    divergent = conn.execute(text("""
        SELECT id, numero_carga FROM tb_cargas 
        WHERE (is_retirada = FALSE OR is_retirada IS NULL) AND numero_carga != CAST(id AS VARCHAR)
        ORDER BY id DESC
    """)).mappings().all()
    
    print(f"\n--- 2. Updating {len(divergent)} divergent rows ---")
    for row in divergent:
        old_num = row['numero_carga']
        new_num = str(row['id'])
        conn.execute(
            text("UPDATE tb_cargas SET numero_carga = :new_num WHERE id = :id"),
            {"new_num": new_num, "id": row['id']}
        )
        print(f"Carga ID {row['id']}: updated numero_carga from '{old_num}' -> '{new_num}'")

    # If nome_carga was also typed as old number (like nome: '42' on ID 43), let's check
    for row in divergent:
        old_num = row['numero_carga']
        new_num = str(row['id'])
        # If nome_carga == old_num, update nome_carga to new_num as well
        conn.execute(
            text("UPDATE tb_cargas SET nome_carga = :new_num WHERE id = :id AND nome_carga = :old_num"),
            {"new_num": new_num, "old_num": old_num, "id": row['id']}
        )

    # 3. Check and set sequence
    seq_res = conn.execute(text("""
        SELECT setval(pg_get_serial_sequence('tb_cargas', 'id'), COALESCE(MAX(id), 1)) FROM tb_cargas;
    """)).scalar()
    print(f"\n--- 3. Sequence updated to: {seq_res} ---")

    # 4. Verification
    print("\n--- 4. Verification After Update ---")
    verified = conn.execute(text("SELECT id, numero_carga, nome_carga, is_retirada FROM tb_cargas ORDER BY id DESC LIMIT 10")).mappings().all()
    for r in verified:
        print(f"ID: {r['id']} | num: {r['numero_carga']} | nome: {r['nome_carga']}")
