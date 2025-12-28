
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

print("Checking imports...")

try:
    print("1. Importing core.deps...")
    from core.deps import get_current_user, get_db
    print("   -> OK")

    print("2. Importing models...")
    from models.usuario import UsuarioModel
    from models.cliente_v2 import ClienteModelV2
    from models.produto import ProdutoV2
    from models.pedido_link import PedidoLink
    from models.config_email_smtp import ConfigEmailSMTP
    from models.config_email_mensagem import ConfigEmailMensagem
    print("   -> OK")

    print("3. Importing routers...")
    from routers import usuario
    from routers import tabela_preco
    from routers import cliente
    from routers import produto
    from routers import link_pedido
    from routers import admin_config_email
    print("   -> OK")

    print("ALL SYNTAX CHECKS PASSED.")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
