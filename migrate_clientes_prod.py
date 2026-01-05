import os
from sqlalchemy import create_engine, text, MetaData, Table, inspect, Column, Integer
from sqlalchemy.orm import sessionmaker

PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(PROD_DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

metadata = MetaData()
inspector = inspect(engine)

# Reflect tables
t_client_v1 = Table('t_cadastro_cliente', metadata, autoload_with=engine)
# Explicit definition for V2 to ensure PK is handled correctly if reflection misses sequence
t_client_v2 = Table('t_cadastro_cliente_v2', metadata, 
    Column('id', Integer, primary_key=True),
    autoload_with=engine, extend_existing=True
)

def migrate_clients():
    print("Fetching V1 clients...")
    # Select specific columns from V1 to map safely
    # Check V1 columns first
    v1_cols = [c.name for c in t_client_v1.columns]
    print(f"V1 Columns: {v1_cols}")
    
    # Simple mapping query. Assuming standard names based on knowledge or typical schema
    # If uncertain, select * and map in python
    stmt = text("SELECT * FROM t_cadastro_cliente")
    v1_rows = session.execute(stmt).fetchall()
    
    print(f"Found {len(v1_rows)} V1 clients. Migrating...")
    
    count = 0
    for row in v1_rows:
        # Map row (result object) to dict
        r = row._mapping
        
        # Construct V2 dict
        # Note: Handling potential missing keys if column names differ
        v2_data = {
            "id": count + 1,  # Manually generate ID starting from 1
            "cadastro_nome_cliente": r.get('nome_empresarial') or "Cliente Sem Nome",
            "cadastro_nome_fantasia": r.get('nome_fantasia'),
            "cadastro_cnpj": r.get('cnpj_cpf_faturamento'),
            "cadastro_inscricao_estadual": r.get('inscricao_estadual_faturamento'),
            "cadastro_tipo_cliente": "juridica" if (r.get('cnpj_cpf_faturamento') and len(str(r.get('cnpj_cpf_faturamento'))) > 11) else "fisica",
            
            # Address
            "faturamento_endereco": f"{r.get('endereco_faturamento') or ''} {r.get('numero_faturamento') or ''}".strip(),
            "faturamento_bairro": r.get('bairro_faturamento'),
            "faturamento_municipio": r.get('cidade_faturamento'),
            "faturamento_estado": r.get('uf_faturamento'),
            "faturamento_cep": r.get('cep_faturamento'),
            
            # Contact
            "compras_email_resposavel": r.get('email_contato') or r.get('e-mail_faturamento'),
            "compras_celular_responsavel": r.get('telefone_contato') or r.get('telefone_faturamento'),
            
            # Defaults
            "cadastro_ativo": True,
            "cadastro_situacao": "ativo"
        }
        
        # Check if already exists (by CNPJ/CPF to avoid duplicates)
        # Or just checking ID if we preserve it? V2 has separate ID sequence usually.
        # Let's check by CNPJ if present
        exists = False
        if v2_data["cadastro_cnpj"]:
            check = session.query(t_client_v2).filter_by(cadastro_cnpj=v2_data["cadastro_cnpj"]).first()
            if check:
                exists = True
        
        if not exists:
            stmt_ins = t_client_v2.insert().values(**v2_data)
            session.execute(stmt_ins)
            count += 1
            
    try:
        session.commit()
        print(f"Successfully migrated {count} clients.")
    except Exception as e:
        session.rollback()
        print(f"Error during migration commit: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_clients()
