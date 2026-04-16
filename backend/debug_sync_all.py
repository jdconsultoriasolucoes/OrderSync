import os
import sys

# Injeta a URL no sistema para o database.py não falhar quando rodado avulso no PowerShell
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

# Ajuste do PATH para aceitar imports da raiz do backend
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import SessionLocal
from models.catalogo_referencias import CidadeSupervisorModel, MunicipioRotaModel, ReferenciasModel
from services.sync_service import sync_cidade_supervisor, sync_municipio_rota, sync_referencia_comercial, sync_profile_comissao

def mass_sync_all():
    db = SessionLocal()
    print("Iniciando Sincronização em Massa (Cura Global do Banco de Dados)...")
    try:
        # 1. Sincroniza todas as Cidades-Supervisores conhecidas
        cidades = db.query(CidadeSupervisorModel).all()
        for c in cidades:
            if c.cidades:
                sync_cidade_supervisor(db, c.cidades, c)
                
        # 2. Sincroniza todas as Rotas
        rotas = db.query(MunicipioRotaModel).all()
        for r in rotas:
            if r.municipio:
                sync_municipio_rota(db, r.municipio, r.rota)
                
        # 3. Sincroniza Referências (JSONB)
        refs = db.query(ReferenciasModel).all()
        for ref in refs:
            if ref.empresa:
                sync_referencia_comercial(db, ref.empresa, ref)
                
        # 4. Sincroniza Perfil global (Comissões)
        sync_profile_comissao(db)
        
        print("\nSincronização 360 finalizada com sucesso! Todos os clientes foram atualizados.")
    except Exception as e:
        print(f"Erro durante a sincronização em massa: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    mass_sync_all()
