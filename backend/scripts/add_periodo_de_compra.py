import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import SessionLocal
from sqlalchemy import text

def run_migration():
    print("Iniciando migração de banco de dados...")
    
    for attempt in range(5):
        try:
            with SessionLocal() as db:
                print(f"Tentativa {attempt+1}... Adicionando cadastro_periodo_de_compra em t_cadastro_cliente_v2...")
                db.execute(text("ALTER TABLE t_cadastro_cliente_v2 ADD COLUMN IF NOT EXISTS cadastro_periodo_de_compra VARCHAR;"))
                db.commit()
                print("Migração concluída com sucesso!")
                return
        except Exception as e:
            print(f"Erro na tentativa {attempt+1}: {e}")
            time.sleep(2)
            
    print("Falhou após 5 tentativas.")
    sys.exit(1)

if __name__ == "__main__":
    run_migration()
