import sys
import os

# Ajusta o sys.path para garantir que o import dos módulos encontre os arquivos corretamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.cliente import verificar_inatividade_clientes
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    print("Iniciando rotina oficial de inativação para teste manual...")
    count = verificar_inatividade_clientes()
    print(f"\\n>>> RESULTADO FINAL: {count} cliente(s) inativado(s) <<<")
