from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

DATABASE_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
engine = create_engine(DATABASE_URL)

def debug_client_inactivity(codigo_cliente):
    print(f"--- Debugging Cliente: {codigo_cliente} ---")
    with engine.connect() as conn:
        # 1. Verificar dados do cliente
        res = conn.execute(text("SELECT id, cadastro_codigo_da_empresa, cadastro_ativo, cadastro_nome_cliente FROM t_cadastro_cliente_v2 WHERE cadastro_codigo_da_empresa = :cod"), {"cod": codigo_cliente}).mappings().first()
        if not res:
            print("Cliente não encontrado na t_cadastro_cliente_v2")
            return
        
        print(f"Cliente found: ID={res['id']}, Cod={res['cadastro_codigo_da_empresa']}, Ativo={res['cadastro_ativo']}, Nome={res['cadastro_nome_cliente']}")

        # 2. Verificar pedidos
        print("\n--- Pedidos do Cliente (TOP 10) ---")
        pedidos = conn.execute(text("""
            SELECT id_pedido, created_at, status, total_pedido 
            FROM tb_pedidos 
            WHERE codigo_cliente = :cod 
            ORDER BY created_at DESC 
            LIMIT 10
        """), {"cod": codigo_cliente}).mappings().all()

        if not pedidos:
            print("Nenhum pedido encontrado para este cliente.")
        else:
            for p in pedidos:
                print(f"ID={p['id_pedido']}, CreatedAt={p['created_at']}, Status={p['status']}, Total={p['total_pedido']}")

        # 3. Testar a lógica da query de inativação
        print("\n--- Testing Inactivity Query ---")
        limite = datetime.now() - timedelta(days=180)
        print(f"Limite 180 dias atrás: {limite}")

        res_max = conn.execute(text("""
            SELECT MAX(created_at) as ultima_compra
            FROM tb_pedidos
            WHERE codigo_cliente = :codigo
              AND status != 'CANCELADO'
        """), {"codigo": codigo_cliente}).mappings().first()

        ultima_compra = res_max['ultima_compra']
        print(f"Última compra detectada (query): {ultima_compra}")

        if ultima_compra:
            # Em SQL as vezes types são diferentes, vamos ver se a comparação funciona
            if hasattr(ultima_compra, 'tzinfo') and ultima_compra.tzinfo:
                 ultima_compra = ultima_compra.replace(tzinfo=None)
            
            if ultima_compra < limite:
                print(">>> RESULTADO: DEVERIA INATIVAR")
            else:
                print(">>> RESULTADO: DEVE PERMANECER ATIVO")
        else:
            print(">>> RESULTADO: Nenhuma compra válida encontrada.")

if __name__ == "__main__":
    import sys
    cod = sys.argv[1] if len(sys.argv) > 1 else '222222222'
    debug_client_inactivity(cod)
