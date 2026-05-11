import os
import shutil
import time
import logging
from pathlib import Path

logger = logging.getLogger("ordersync.manutencao")

def limpar_arquivos_temporarios():
    """
    Remove arquivos temporários antigos das pastas de cache e scratch.
    Foco: /tmp (Render) e pastas de exportação.
    """
    logger.info("Iniciando limpeza de arquivos temporários...")
    
    # Lista de diretórios para limpar
    dirs_to_clean = [
        "/tmp",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "scratch")
    ]
    
    count = 0
    now = time.time()
    day_in_seconds = 24 * 3600
    
    for d in dirs_to_clean:
        if not os.path.exists(d):
            continue
            
        try:
            for item in os.listdir(d):
                # Não apaga pastas ocultas ou críticas
                if item.startswith('.') or item == 'template_supra.xlsx':
                    continue
                    
                item_path = os.path.join(d, item)
                # Verifica idade do arquivo (mais de 24h)
                if os.path.isfile(item_path):
                    if os.stat(item_path).st_mtime < (now - day_in_seconds):
                        os.remove(item_path)
                        count += 1
                elif os.path.isdir(item_path):
                    # Se for pasta (ex: em /tmp), apaga se for antiga
                    if os.stat(item_path).st_mtime < (now - day_in_seconds):
                        shutil.rmtree(item_path)
                        count += 1
        except Exception as e:
            logger.error(f"Erro ao limpar diretório {d}: {e}")
            
    logger.info(f"Limpeza concluída. {count} itens removidos.")
    return count
