import os
import sys
import re
from sqlalchemy import text
from database import SessionLocal

def run():
    db = SessionLocal()
    try:
        # Get all distinct client names and codes from tb_tabela_preco
        # that need to be evaluated.
        rows = db.execute(text("""
            SELECT DISTINCT cliente, codigo_cliente 
            FROM tb_tabela_preco
            WHERE cliente IS NOT NULL AND cliente != ''
        """)).fetchall()

        # Build a mapping from t_cadastro_cliente_v2
        clients = db.execute(text("""
            SELECT cadastro_codigo_da_empresa, cadastro_cnpj, cadastro_cpf, cadastro_nome_cliente, cadastro_nome_fantasia
            FROM t_cadastro_cliente_v2
        """)).fetchall()

        # Create dictionaries for fast lookup
        cnpj_to_code = {}
        name_to_code = {}
        for c in clients:
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

        mismatches = []
        for row in rows:
            cliente_str = row.cliente
            current_code = row.codigo_cliente
            
            # Extract potential CNPJ from the string
            cnpj_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', cliente_str)
            found_code = None
            match_type = None
            
            if cnpj_match:
                cnpj_clean = re.sub(r'\D', '', cnpj_match.group(0))
                found_code = cnpj_to_code.get(cnpj_clean)
                match_type = 'CNPJ'
            
            # Extract name part (remove CNPJ prefix if present)
            # Usually format is "CNPJ - NAME" or just "NAME"
            name_part = cliente_str
            if '-' in cliente_str and sum(c.isdigit() for c in cliente_str.split('-')[0]) > 10:
                name_part = '-'.join(cliente_str.split('-')[1:]).strip()
            
            if not found_code:
                name_clean = name_part.strip().lower()
                found_code = name_to_code.get(name_clean)
                match_type = 'NOME EXATO'
                
                # Try partial match if exact match fails
                if not found_code:
                    for db_name, db_code in name_to_code.items():
                        if name_clean in db_name or db_name in name_clean:
                            found_code = db_code
                            match_type = 'NOME PARCIAL'
                            break

            if found_code and current_code != found_code:
                mismatches.append({
                    'cliente_string': cliente_str,
                    'current_code': current_code,
                    'new_code': found_code,
                    'match_type': match_type
                })

        print(f"Total de tabelas únicas analisadas: {len(rows)}")
        print(f"Total de correções propostas: {len(mismatches)}")
        for m in mismatches[:10]:
            print(f" -> '{m['cliente_string']}': {m['current_code']} => {m['new_code']} ({m['match_type']})")
            
        if len(mismatches) > 10:
            print("... e mais")

    finally:
        db.close()

if __name__ == '__main__':
    run()
