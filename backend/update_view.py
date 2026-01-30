from database import SessionLocal
from sqlalchemy import text
import sys

def update_view():
    sql = """
CREATE OR REPLACE VIEW public.v_produto_v2_preco AS
SELECT 
    p.id,
    p.codigo_supra,
    p.nome_produto,
    p.embalagem_venda,
    p.peso,
    p.peso_bruto,
    p.preco,
    p.preco_anterior,
    p.preco_tonelada,
    p.preco_tonelada_anterior,
    p.marca,
    p.familia,
    p.id_familia,
    p.fornecedor,
    p.tipo,
    p.validade_tabela,
    p.validade_tabela_anterior,
    p.status_produto,
    p.unidade,
    p.unidade_anterior,
    p.tipo_giro,
    p.estoque_disponivel,
    p.estoque_ideal,
    p.unidade_embalagem,
    p.codigo_ean,
    p.codigo_embalagem,
    p.ncm,
    p.filhos,
    p.desconto_valor_tonelada,
    p.data_desconto_inicio,
    p.data_desconto_fim,
    COALESCE(i.ipi, 0.0000) AS ipi,
    COALESCE(i.iva_st, 0.0000) AS iva_st,
    COALESCE(i.icms, 0.0000) AS icms,
    COALESCE(i.cbs, 0.0000) AS cbs,
    COALESCE(i.ibs, 0.0000) AS ibs
FROM t_cadastro_produto_v2 p
LEFT JOIN t_imposto_v2 i ON p.id = i.produto_id;
    """

    sql_permissions = """
    ALTER TABLE public.v_produto_v2_preco OWNER TO dispet_admin_;
    GRANT ALL ON TABLE public.v_produto_v2_preco TO dispet_admin_;
    """
    
    db = SessionLocal()
    try:
        print("Executando DROP VIEW (CASCADE)...")
        db.execute(text("DROP VIEW IF EXISTS public.v_produto_v2_preco CASCADE;"))
        
        print("Executando CREATE OR REPLACE VIEW...")
        db.execute(text(sql))
        print("View atualizada com sucesso.")
        
        # Tenta aplicar permissoes, mas não falha se usuario não existir ou nao tiver permissao
        try:
            print("Aplicando permissoes...")
            db.execute(text(sql_permissions))
            print("Permissoes aplicadas.")
        except Exception as e:
            print(f"Aviso: Nao foi possivel aplicar permissoes (pode ser ignorado se o user for diferente): {e}")

        db.commit()
    except Exception as e:
        print(f"Erro ao atualizar view: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    update_view()
