import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine
from sqlalchemy import text

def run_migration():
    dialect = engine.dialect.name
    with engine.begin() as conn:
        print(f"Conectado ao banco de dados usando dialeto: {dialect}")
        try:
            if dialect == 'postgresql':
                conn.execute(text("ALTER TABLE t_usuario ADD COLUMN IF NOT EXISTS email_daily_digest BOOLEAN DEFAULT TRUE;"))
            elif dialect == 'sqlite':
                # SQLite não suporta IF NOT EXISTS no ADD COLUMN. Tenta adicionar e ignora o erro se já existir.
                try:
                    conn.execute(text("ALTER TABLE t_usuario ADD COLUMN email_daily_digest BOOLEAN DEFAULT TRUE;"))
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print("Coluna já existe no SQLite.")
                    else:
                        raise e
            else:
                conn.execute(text("ALTER TABLE t_usuario ADD COLUMN email_daily_digest BOOLEAN DEFAULT TRUE;"))
            
            print("Sucesso! Coluna email_daily_digest verificada/adicionada na tabela t_usuario.")
        except Exception as e:
            print(f"Erro ao adicionar coluna: {e}")

if __name__ == "__main__":
    run_migration()
