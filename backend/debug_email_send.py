import sys
import os

# Adiciona o diretório atual ao path para importar modulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from services.email_service import get_email_cliente_responsavel_compras, enviar_email_notificacao

def testar_envio(codigo_cliente):
    print(f"--- Iniciando teste de envio de email para cliente: {codigo_cliente} ---")
    
    db = SessionLocal()
    try:
        # 1. Testar busca de email
        print("1. Buscando email...")
        email = get_email_cliente_responsavel_compras(db, codigo_cliente)
        
        if not email:
            print(f"ERRO: Nenhum email encontrado para o código '{codigo_cliente}'.")
            print("Verifique se o cliente existe na tabela 't_cadastro_cliente_v2' e se possui algum email cadastrado (compras, nfe, recebimento, etc).")
            return
            
        print(f"SUCESSO: Email encontrado: {email}")
        
        # 2. Perguntar se deseja enviar email de teste
        resp = input(f"Deseja enviar um email de teste para '{email}'? (s/n): ")
        if resp.lower() != 's':
            print("Envio cancelado pelo usuário.")
            return

        # 3. Criar Pedido Dummy
        class PedidoDummy:
            def __init__(self):
                self.id = 999999 # ID ficticio
                self.cliente_nome = "CLIENTE DE TESTE (DEBUG)"
                self.total_pedido = 100.00
                self.codigo_cliente = codigo_cliente
                self.cliente_email = email # Força o email encontrado

        pedido_teste = PedidoDummy()
        
        print("2. Tentando enviar email...")
        try:
            enviar_email_notificacao(db, pedido_teste)
            print("SUCESSO: Email enviado para a fila/servidor SMTP.")
            print("Verifique a caixa de entrada do destinatário.")
        except Exception as e:
            print(f"ERRO ao enviar email: {e}")
            import traceback
            traceback.print_exc()

    finally:
        db.close()
        print("--- Fim do teste ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python debug_email_send.py <CODIGO_DO_CLIENTE>")
        sys.exit(1)
    
    codigo = sys.argv[1]
    testar_envio(codigo)
