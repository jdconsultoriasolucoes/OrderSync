import sqlalchemy
from sqlalchemy import create_engine, text

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

try:
    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS public.pedido_status_event (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                pedido_id BIGINT NOT NULL,
                de_status VARCHAR(100),
                para_status VARCHAR(100),
                user_id VARCHAR(100),
                motivo TEXT,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pedido_status_event_pedido_id 
            ON public.pedido_status_event(pedido_id);
        """))
    print("Tabela pedido_status_event criada com sucesso (ou ja existia) e indexada.")
except Exception as e:
    print(f"Erro ao executar migracao: {e}")
