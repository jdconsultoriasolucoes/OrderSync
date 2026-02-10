import sys
import os

# Adiciona o diretório raiz ao path para importar modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from database import SessionLocal, engine
from sqlalchemy import text

def migrate():
    with SessionLocal() as db:
        print("Verificando colunas na tabela config_email_mensagem...")
        try:
            # Tenta selecionar as colunas novas
            db.execute(text("SELECT assunto_cliente, corpo_html_cliente FROM config_email_mensagem LIMIT 1"))
            print("Colunas já existem.")
        except Exception as e:
            print("Colunas não encontradas (ou erro). Tentando criá-las...")
            try:
                # Rollback da transação falhada anterior
                db.rollback()
                
                # Adiciona as colunas
                db.execute(text("ALTER TABLE config_email_mensagem ADD COLUMN assunto_cliente TEXT"))
                db.execute(text("ALTER TABLE config_email_mensagem ADD COLUMN corpo_html_cliente TEXT"))
                db.commit()
                print("Colunas 'assunto_cliente' e 'corpo_html_cliente' adicionadas com SUCESSO.")
            except Exception as e2:
                print(f"Erro ao adicionar colunas: {e2}")
                db.rollback()

if __name__ == "__main__":
    migrate()
