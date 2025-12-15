
import os
from sqlalchemy import create_engine, text

# Fallback string if env not set
DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ordersync")

def fix_view():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("Recreating View v_produto_v2_preco...")
        # Simplest definition checking just the main table first.
        # If the backend expects some calculated fields, we might need to add them.
        # But looking at ProdutoV2Out, standard fields exist in t_cadastro_produto_v2.
        # 'preco_final', 'reajuste_percentual', 'vigencia_ativa' are marked Optional.
        
        sql = """
        CREATE OR REPLACE VIEW v_produto_v2_preco AS
        SELECT 
             p.*,
             -- Placeholder logic for calculated fields if they are missing in table
             p.preco as preco_final, 
             0.0 as reajuste_percentual,
             true as vigencia_ativa
        FROM t_cadastro_produto_v2 p;
        """
        conn.execute(text(sql))
        conn.commit()
        print("View recreated successfully.")

if __name__ == "__main__":
    fix_view()
