import os
import sys
# Adiciona o diretório backend ao path para conseguir importar database e services
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.db_migrations import run_migrations
import logging

# Configura logging básico para ver o progresso
logging.basicConfig(level=logging.INFO)

print("Iniciando migrações e deduplicação no novo banco...")
try:
    run_migrations()
    print("Migrações concluídas com sucesso!")
except Exception as e:
    print(f"Erro ao executar migrações: {e}")
    import traceback
    traceback.print_exc()
