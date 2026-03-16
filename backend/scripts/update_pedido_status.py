import sys
import os

# Adds backend to pythonpath to import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"
engine = create_engine(DB_URL, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_statuses():
    db = SessionLocal()
    try:
        # Desativar todos os status antigos
        db.execute(text("UPDATE public.pedido_status SET ativo = FALSE;"))
        
        # Inserir ou Reativar os 5 permitidos
        novos_status = [
            {"codigo": "ORCAMENTO", "rotulo": "Orçamento", "ordem": 1, "ativo": True},
            {"codigo": "PEDIDO", "rotulo": "Pedido", "ordem": 2, "ativo": True},
            {"codigo": "FATURADO_SUPRA", "rotulo": "Faturado Supra", "ordem": 3, "ativo": True},
            {"codigo": "FATURADO_DISPET", "rotulo": "Faturado Dispet", "ordem": 4, "ativo": True},
            {"codigo": "CANCELADO", "rotulo": "Cancelado", "ordem": 5, "ativo": True}
        ]
        
        for st in novos_status:
            sql = text("""
                INSERT INTO public.pedido_status (codigo, rotulo, ordem, ativo)
                VALUES (:codigo, :rotulo, :ordem, :ativo)
                ON CONFLICT (codigo) DO UPDATE 
                SET rotulo = EXCLUDED.rotulo, 
                    ordem = EXCLUDED.ordem, 
                    ativo = TRUE;
            """)
            db.execute(sql, st)
            
        db.commit()
        print("✅ Status atualizados com sucesso no banco de dados!")
    except Exception as e:
        print(f"❌ Erro ao atualizar status: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_statuses()
