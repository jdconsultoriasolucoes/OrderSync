import sys
import os

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from database import SessionLocal
from services.email_service import enviar_email_notificacao
from models.pedido import PedidoModel
from services.pedido_pdf_data import carregar_pedido_pdf
from services.pdf_service import gerar_pdf_pedido

def debug_email(pedido_id):
    db = SessionLocal()
    try:
        print(f"--- Debugging Email for Pedido {pedido_id} ---")
        
        # 1. Fetch Order
        pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
        if not pedido:
            print("Pedido not found!")
            return

        print(f"Pedido Client Code: {pedido.codigo_cliente}")
        print(f"Pedido Client Name: {pedido.cliente}")

        # 2. Generate PDF (to check if that fails)
        print("Generating PDF...")
        try:
            pedido_pdf = carregar_pedido_pdf(db, pedido_id)
            pdf_bytes = gerar_pdf_pedido(pedido_pdf)
            print(f"PDF Generated: {len(pdf_bytes)} bytes")
        except Exception as e:
            print(f"PDF Generation Failed: {e}")
            pdf_bytes = None

        # 3. Send Email
        print("Sending Email...")
        # Create a dummy object if needed or pass the model if compatible
        # The service expects an object with attributes. PedidoModel might work if it has the attrs.
        # But `enviar_email_notificacao` constructs `pedido_info` from attributes.
        
        # Let's verify what `enviar_email_notificacao` expects.
        # It expects `pedido` object with: id, cliente_nome, total_pedido, codigo_cliente 
        # (and cliente_email for client copy).
        
        # PedidoModel has: id, cliente, total_pedido, codigo_cliente.
        # It does NOT have 'cliente_nome' directly (it uses 'cliente').
        # The service tries: getattr(pedido, "cliente_nome", "") or getattr(pedido, "nome_cliente", "")
        # Wait, PedidoModel usually has 'cliente'.
        # Let's check `enviar_email_notificacao` in `email_service` again carefully.
        # It converts: cliente_nome = getattr ...
        
        # I'll let it run and see.
        enviar_email_notificacao(db, pedido, pdf_bytes=pdf_bytes)
        print("Email Sent logic executed (Check logs for internal prints).")

    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_email.py <pedido_id>")
    else:
        debug_email(int(sys.argv[1]))
