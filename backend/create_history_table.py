from database import SessionLocal
from sqlalchemy import text

def create_historico_table():
    db = SessionLocal()
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS tb_pedido_historico (
            id SERIAL PRIMARY KEY,
            pedido_id INTEGER NOT NULL REFERENCES tb_pedidos(id_pedido),
            de_status VARCHAR(50),
            para_status VARCHAR(50),
            user_id VARCHAR(100),
            motivo TEXT,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        print("Creating tb_pedido_historico...")
        db.execute(text(sql))
        db.commit()
        print("Table created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_historico_table()
