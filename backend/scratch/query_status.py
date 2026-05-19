import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get("DATABASE_URL")
print(f"Tentando conectar ao banco: {db_url.split('@')[-1] if db_url else 'Nenhum'}")

def check_status():
    if not db_url:
        print("DATABASE_URL não configurado no ambiente.")
        return
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("Conexão estabelecida com sucesso!")
        result = conn.execute(text("SELECT codigo, rotulo, cor_hex, ordem, ativo FROM public.pedido_status ORDER BY ordem"))
        print("--- STATUS ATUAIS ---")
        for r in result:
            print(f"Código: {r[0]} | Rótulo: {r[1]} | Cor: {r[2]} | Ordem: {r[3]} | Ativo: {r[4]}")

if __name__ == "__main__":
    check_status()
