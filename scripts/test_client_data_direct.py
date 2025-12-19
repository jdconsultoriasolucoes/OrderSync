import sys
import os

# Adiciona o diretório backend ao path para importar database
sys.path.append(os.path.abspath("e:/OrderSync - Dev/backend"))

from database import SessionLocal
from sqlalchemy import text

def test_db():
    try:
        db = SessionLocal()
        # Simula a query exata do busca_cliente
        sql = """
            SELECT
              codigo,
              cnpj_cpf_faturamento_formatted AS cnpj_cpf,
              nome_empresarial     AS nome_cliente,
              ramo_juridico
            FROM public.t_cadastro_cliente
            WHERE nome_empresarial IS NOT NULL
            LIMIT 5
        """
        rows = db.execute(text(sql)).mappings().all()
        print("\n--- Resultado DB (Simulando API) ---")
        for i, row in enumerate(rows):
            d = dict(row)
            print(f"Item {i}: {d}")
            if 'codigo' not in d or d['codigo'] is None:
                print("⚠️  ATENÇÃO: Campo 'codigo' ausente ou nulo!")
            else:
                print(f"✅ 'codigo': {d['codigo']} (Tipo: {type(d['codigo'])})")

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_db()
