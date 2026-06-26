import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, engine
# Import all models to register them on Base.metadata
from models.usuario import UsuarioModel
from models.produto import ProdutoV2, HistoricoEstoqueV2, ImpostoV2
from models.tabela_preco import TabelaPreco as TabelaPrecoModel
from models.pedido import PedidoModel
from models.pedido_pdf import PedidoPdf, PedidoPdfItem
from models.idempotency import IdempotencyKeyModel
from models.background_task import BackgroundTaskModel
from models.automation_config import AutomationConfigModel

print("Creating tables...")
Base.metadata.create_all(bind=engine)

print("Running migrations...")
from services.db_migrations import run_migrations
run_migrations()
print("Done!")
