import os
import re
from sqlalchemy import text
from database import SessionLocal

def run_fix():
    db = SessionLocal()
    try:
        print("--- INICIANDO CORREÇÃO DE CLIENTES NAS TABELAS ---")
        
        # Busca todas as tabelas de preços
        tabelas = db.execute(text("""
            SELECT id_tabela, cliente, codigo_cliente 
            FROM tb_tabela_preco
            WHERE cliente IS NOT NULL AND cliente != ''
        """)).fetchall()

        # Busca todos os clientes cadastrados para cruzamento
        clientes_cadastrados = db.execute(text("""
            SELECT cadastro_codigo_da_empresa, cadastro_cnpj, cadastro_cpf, cadastro_nome_cliente, cadastro_nome_fantasia
            FROM t_cadastro_cliente_v2
        """)).fetchall()

        # Constrói dicionários para busca rápida
        cnpj_to_code = {}
        name_to_code = {}
        
        for c in clientes_cadastrados:
            code = c.cadastro_codigo_da_empresa
            cnpj = c.cadastro_cnpj or c.cadastro_cpf
            name = c.cadastro_nome_cliente
            fantasia = c.cadastro_nome_fantasia
            
            if cnpj:
                cnpj_clean = re.sub(r'\D', '', cnpj)
                if cnpj_clean:
                    cnpj_to_code[cnpj_clean] = code
            
            if name:
                name_clean = name.strip().lower()
                name_to_code[name_clean] = code
            
            if fantasia:
                fantasia_clean = fantasia.strip().lower()
                name_to_code[fantasia_clean] = code

        updates_feitos = 0

        # Verifica e atualiza tabelas
        for row in tabelas:
            id_tabela = row.id_tabela
            cliente_str = row.cliente
            current_code = row.codigo_cliente
            
            # Tenta encontrar um CNPJ na string do cliente
            cnpj_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', cliente_str)
            found_code = None
            
            if cnpj_match:
                cnpj_clean = re.sub(r'\D', '', cnpj_match.group(0))
                found_code = cnpj_to_code.get(cnpj_clean)
            
            # Tenta buscar pelo nome
            if not found_code:
                name_part = cliente_str
                # Remove prefixo de CNPJ se existir na string (ex: "12.345.678/0001-90 - Empresa")
                if '-' in cliente_str and sum(c.isdigit() for c in cliente_str.split('-')[0]) > 10:
                    name_part = '-'.join(cliente_str.split('-')[1:]).strip()
                
                name_clean = name_part.strip().lower()
                found_code = name_to_code.get(name_clean)
                
                # Se ainda não encontrou, tenta uma busca parcial (ILIKE equivalente)
                if not found_code:
                    for db_name, db_code in name_to_code.items():
                        if name_clean in db_name or db_name in name_clean:
                            found_code = db_code
                            break

            # Se encontrou o código correto e ele é diferente do atual na tabela
            if found_code and current_code != found_code:
                db.execute(
                    text("UPDATE tb_tabela_preco SET codigo_cliente = :novo_codigo WHERE id_tabela = :id_tabela"),
                    {"novo_codigo": found_code, "id_tabela": id_tabela}
                )
                
                db.execute(
                    text("UPDATE tb_pedidos SET codigo_cliente = :novo_codigo WHERE tabela_preco_id = :id_tabela"),
                    {"novo_codigo": found_code, "id_tabela": id_tabela}
                )
                
                updates_feitos += 1
                print(f"[CORRIGIDO] Tabela {id_tabela} corrigida: '{cliente_str}' de ({current_code}) para ({found_code})")

        db.commit()
        print(f"\n--- SUCESSO! Foram corrigidas {updates_feitos} tabelas e pedidos associados. ---")

    except Exception as e:
        db.rollback()
        print(f"Erro ao executar a correção: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    run_fix()
