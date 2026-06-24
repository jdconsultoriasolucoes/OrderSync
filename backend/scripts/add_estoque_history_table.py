import sys
import os

# Adjust path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text

def run_migration():
    with engine.connect() as conn:
        print("Checking if 't_historico_estoque_v2' table exists...")
        res = conn.execute(text(
            "SELECT EXISTS ("
            "   SELECT FROM information_schema.tables "
            "   WHERE table_name = 't_historico_estoque_v2'"
            ")"
        ))
        exists = res.scalar()
        if not exists:
            print("Creating 't_historico_estoque_v2' table...")
            conn.execute(text("""
                CREATE TABLE t_historico_estoque_v2 (
                    id BIGSERIAL PRIMARY KEY,
                    codigo_supra TEXT NOT NULL,
                    nome_produto TEXT,
                    qtd_estoque INTEGER,
                    qtd_pedido INTEGER,
                    af_pendentes INTEGER,
                    estoque_disponivel INTEGER,
                    estoque_futuro INTEGER,
                    data_ingestao TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                    nome_arquivo TEXT,
                    usuario TEXT
                )
            """))
            conn.commit()
            print("Table created successfully.")
        else:
            print("Table 't_historico_estoque_v2' already exists.")

if __name__ == "__main__":
    run_migration()
