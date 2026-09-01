import sys
import os
import argparse
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from database import SessionLocal
from sqlalchemy import text

def anonimizar_cliente(codigo_cliente: str, db):
    """
    LGPD Compliance (Right to be Forgotten / Anonimização)
    Anonimiza os dados sensíveis de um cliente e de todos os pedidos relacionados a ele.
    Mantém o histórico financeiro/contábil dos pedidos, mas embaralha/remove PII.
    """
    
    # 1. Anonimizar o Cadastro de Cliente
    update_cliente = text("""
        UPDATE public.t_cadastro_cliente_v2
        SET 
            cadastro_nome_cliente = 'ANONIMIZADO_LGPD_' || substr(md5(random()::text), 1, 6),
            cadastro_nome_fantasia = 'ANONIMIZADO',
            cadastro_cnpj_cpf = '000.000.000-00',
            contato_nome_completo = 'ANONIMIZADO',
            contato_email = 'anonimizado@lgpd.local',
            contato_telefone = '(00) 0000-0000',
            contato_celular = '(00) 00000-0000',
            entrega_endereco = 'Rua Anonimizada, 0',
            entrega_bairro = 'Bairro Anonimizado',
            entrega_cep = '00000-000',
            cobranca_endereco = 'Rua Anonimizada, 0'
        WHERE cadastro_codigo_da_empresa = :codigo
    """)
    
    # 2. Anonimizar PII no cabeçalho dos pedidos daquele cliente
    update_pedidos = text("""
        UPDATE public.tb_pedidos
        SET 
            cliente = 'ANONIMIZADO_LGPD',
            contato_nome = 'ANONIMIZADO',
            contato_email = 'anonimizado@lgpd.local',
            contato_fone = '(00) 0000-0000'
        WHERE codigo_cliente = :codigo
    """)
    
    print(f"[*] Iniciando processo de anonimização LGPD para o cliente: {codigo_cliente}")
    
    try:
        res1 = db.execute(update_cliente, {"codigo": codigo_cliente})
        if res1.rowcount == 0:
            print("[!] Cliente não encontrado ou já anonimizado.")
        else:
            print(f"[+] Cadastro do cliente {codigo_cliente} anonimizado com sucesso.")
            
        res2 = db.execute(update_pedidos, {"codigo": codigo_cliente})
        print(f"[+] {res2.rowcount} pedidos relacionados tiveram seus PIIs removidos.")
        
        db.commit()
        print("[*] Processo concluído com sucesso. Transação persistida.")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Falha na anonimização: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script LGPD - Anonimização de Dados Sensíveis (PII)")
    parser.add_argument("--codigo", required=True, help="Código do cliente para anonimizar")
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        anonimizar_cliente(args.codigo, db)
    finally:
        db.close()
