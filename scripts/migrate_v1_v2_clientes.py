
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.cliente import ClienteModel
from models.cliente_v2 import ClienteModelV2
from database import DATABASE_URL

# Adjust database URL if needed (e.g. if using a local driver vs what's in env)
# Assuming DATABASE_URL is valid from backend.database

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def migrate():
    session = Session()
    try:
        # Get all V1 clients
        clients_v1 = session.query(ClienteModel).all()
        print(f"Encontrados {len(clients_v1)} clientes na tabela antiga.")

        migrated_count = 0
        updated_count = 0

        for c1 in clients_v1:
            # Check if exists in V2 by code
            code = str(c1.codigo)
            existing = session.query(ClienteModelV2).filter(
                ClienteModelV2.cadastro_codigo_da_empresa == code
            ).first()

            # Data Mapping
            data = {
                "cadastro_codigo_da_empresa": code,
                "cadastro_nome_cliente": c1.nome_empresarial or c1.nome_fantasia,
                "cadastro_nome_fantasia": c1.nome_fantasia,
                "cadastro_cnpj": c1.cnpj_cpf_faturamento, # Assuming mixed column
                "cadastro_ativo": (c1.ativo_nao_ativo == 'ATIVO'),
                "cadastro_ramo_de_atividade": c1.ramo_juridico,
                "cadastro_atividade_principal": c1.atividade_principal,
                
                # Compras (Contato)
                "compras_nome_responsavel": c1.contato_comprador,
                "compras_celular_responsavel": c1.telefone_contato,
                "compras_email_resposavel": c1.email_contato,

                # Faturamento
                "faturamento_endereco": f"{c1.endereco_faturamento or ''}, {c1.numero_faturamento or ''}".strip(', '),
                "faturamento_bairro": c1.bairro_faturamento,
                "faturamento_cep": c1.cep_faturamento,
                "faturamento_municipio": c1.cidade_faturamento,
                "faturamento_estado": c1.uf_faturamento,
                "faturamento_email_danfe": c1.e_mail_faturamento,

                # Entrega
                "entrega_endereco": c1.endereco_entrega,
                "entrega_municipio": c1.cidade_entrega,
                "entrega_observacao_motorista": c1.mensagem_motorista_entrega or c1.observacao_entrega,
                
                # Cobranca
                "cobranca_endereco": c1.endereco_cobranca,
                "cobranca_municipio": c1.cidade_cobranca,
                "cobranca_resp_nome": c1.contato_cobranca,
                "cobranca_resp_celular": c1.telefone_cobranca,
                "cobranca_resp_email": c1.email_cobranca,
                
                # Others
                "cadastro_markup": 0.0, # Default
                "criado_por": "migration_script",
                "atualizado_por": "migration_script"
            }

            if existing:
                # Update? Skip? User just said 'migrate'. 
                # I will update fields if they are empty in V2? 
                # Or overwrite cleanly. Let's overwrite cleanly to ensure data matches V1.
                for k, v in data.items():
                    setattr(existing, k, v)
                updated_count += 1
            else:
                new_client = ClienteModelV2(**data)
                session.add(new_client)
                migrated_count += 1
        
        session.commit()
        print(f"Migração concluída.")
        print(f"Criados: {migrated_count}")
        print(f"Atualizados: {updated_count}")

    except Exception as e:
        session.rollback()
        print(f"Erro na migração: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    confirm = input("Deseja iniciar a migracao (t_cadastro_cliente -> t_cadastro_cliente_v2)? [s/n]: ")
    if confirm.lower() == 's':
        migrate()
    else:
        print("Cancelado.")
