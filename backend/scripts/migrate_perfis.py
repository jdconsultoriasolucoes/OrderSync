import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.perfil import PerfilModel, PerfilPermissaoModel
from models.usuario import UsuarioModel

DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

def run():
    print("Iniciando migração de Perfis e Permissões (RBAC)...")
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Cria as novas tabelas
    print("Criando tabelas tb_perfis e tb_perfil_permissoes...")
    PerfilModel.__table__.create(engine, checkfirst=True)
    PerfilPermissaoModel.__table__.create(engine, checkfirst=True)
    
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE t_usuario ADD COLUMN perfil_id INTEGER REFERENCES tb_perfis(id) ON DELETE SET NULL"))
            conn.commit()
            print("Coluna perfil_id adicionada em t_usuario.")
    except Exception as e:
        print("Coluna perfil_id já existe ou erro ignorado:", e)

    # Cria perfis padrão
    modulos = ["pedidos", "clientes", "relatorios", "tabelas_preco", "usuarios_e_perfis"]
    
    perfis_padrao = {
        "admin": {
            "descricao": "Administrador do sistema com acesso irrestrito.",
            "is_system": True,
            "permissoes": {m: (True, True, True, True) for m in modulos}
        },
        "gerente": {
            "descricao": "Gerente de equipe. Visualiza relatorios e clientes.",
            "is_system": True,
            "permissoes": {
                "pedidos": (True, True, True, False),
                "clientes": (True, True, True, False),
                "relatorios": (True, False, False, False),
                "tabelas_preco": (True, False, False, False),
                "usuarios_e_perfis": (False, False, False, False)
            }
        },
        "vendedor": {
            "descricao": "Vendedor comum.",
            "is_system": True,
            "permissoes": {
                "pedidos": (True, True, True, False),
                "clientes": (True, True, True, False),
                "relatorios": (False, False, False, False),
                "tabelas_preco": (True, False, False, False),
                "usuarios_e_perfis": (False, False, False, False)
            }
        }
    }

    perfil_ids = {}

    try:
        for p_name, p_data in perfis_padrao.items():
            perfil = db.query(PerfilModel).filter_by(nome=p_name).first()
            if not perfil:
                perfil = PerfilModel(nome=p_name, descricao=p_data["descricao"], is_system=p_data["is_system"])
                db.add(perfil)
                db.flush()
                
                for mod, perms in p_data["permissoes"].items():
                    p_perm = PerfilPermissaoModel(
                        perfil_id=perfil.id,
                        modulo=mod,
                        pode_visualizar=perms[0],
                        pode_criar=perms[1],
                        pode_editar=perms[2],
                        pode_excluir=perms[3]
                    )
                    db.add(p_perm)
                print(f"Perfil '{p_name}' criado com sucesso.")
            perfil_ids[p_name] = perfil.id
            
        # Atualiza os usuários existentes para referenciar o perfil_id
        for user in db.query(UsuarioModel).all():
            if not user.perfil_id:
                funcao = user.funcao or "vendedor"
                if funcao in perfil_ids:
                    user.perfil_id = perfil_ids[funcao]
        
        db.commit()
        print("Migração concluída com sucesso! Todos os usuários estão mapeados para os perfis.")
    except Exception as e:
        db.rollback()
        print("Erro durante a migração:", e)
    finally:
        db.close()

if __name__ == "__main__":
    run()
