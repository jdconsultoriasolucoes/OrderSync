import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configuração básica de logs no terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QA_TEST_V2")

# Adiciona o diretório backend ao path para importação
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

# Configurações do Banco para o teste local (Render DB)
os.environ.setdefault("DATABASE_URL", "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync")

from backend.database import DATABASE_URL
from backend.models.cliente_v2 import ClienteModelV2
from backend.services.excel_supra_service import gerar_excel_cliente_supra
from backend.services.pdf_supra_service import gerar_pdf_cliente_supra

def run_qa_test():
    logger.info("Iniciando Smoke Test V2: Exportação Supra Pixel-Perfect...")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Busca o primeiro cliente disponível para teste real
        cliente = db.query(ClienteModelV2).first()
        if not cliente:
            logger.error("Falha Crítica: Nenhum cliente encontrado no banco para teste.")
            return

        logger.info(f"Cliente selecionado para teste: {cliente.cadastro_nome_cliente} (ID: {cliente.id})")

        # 1. Teste EXCEL (Verificação de 500 error)
        logger.info("Fase 1: Testando exportação Excel (Motor Robusto)...")
        try:
            excel_bytes = gerar_excel_cliente_supra(cliente)
            with open("test_final_supra_v2.xlsx", "wb") as f:
                f.write(excel_bytes)
            logger.info("OK: Excel gerado com sucesso (test_final_supra_v2.xlsx)")
        except PermissionError:
            logger.error("FALHA: Arquivo Excel está aberto ou bloqueado pelo sistema.")
        except Exception as e:
            logger.error(f"FALHA na exportação Excel: {e}")

        # 2. Teste PDF (Verificação de Layout Pixel-Perfect)
        logger.info("Fase 2: Testando exportação PDF (Motor Grid-Based)...")
        try:
            pdf_bytes = gerar_pdf_cliente_supra(cliente)
            with open("test_final_supra_v2.pdf", "wb") as f:
                f.write(pdf_bytes)
            logger.info("OK: PDF gerado com sucesso (test_final_supra_v2.pdf)")
        except Exception as e:
            logger.error(f"FALHA na exportação PDF: {e}")

        logger.info("--- TESTE DE QA V2 CONCLUÍDO ---")

    except Exception as e:
        logger.error(f"Erro inesperado no script de teste: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_qa_test()
