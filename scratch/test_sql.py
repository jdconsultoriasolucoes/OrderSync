import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL") or "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

def check_queries():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    try:
        # 1. Test get_vendas_cliente query syntax
        query_cliente = """
            SELECT DISTINCT
                p.id_pedido                             AS numero_pedido,
                p.pedido_supra                          AS pedido_supra,
                p.nota_fiscal                           AS danfe,
                p.codigo_cliente                        AS codigo_cliente,
                COALESCE(c.cadastro_nome_cliente, p.cliente) AS cliente,
                COALESCE(c.cadastro_nome_fantasia, 'Sem Nome Fantasia') AS nome_fantasia,
                COALESCE(c.entrega_municipio, 'Sem Município') AS municipio,
                (
                    SELECT SUM(COALESCE(pr_sub.peso, 0) * pi_sub.quantidade)
                    FROM public.tb_pedidos_itens pi_sub
                    LEFT JOIN public.t_cadastro_produto_v2 pr_sub ON pr_sub.codigo_supra = pi_sub.codigo
                    WHERE pi_sub.id_pedido = p.id_pedido
                )                                       AS peso_liquido,
                CASE
                    WHEN COALESCE(p.total_sem_frete, 0) > 0 AND COALESCE(p.total_com_frete, 0) > 0 THEN p.total_sem_frete
                    WHEN COALESCE(p.total_sem_frete, 0) = 0 AND COALESCE(p.total_com_frete, 0) > 0 THEN p.total_com_frete
                    ELSE COALESCE(p.total_sem_frete, 0)
                END                                     AS valor_sem_frete,
                CASE
                    WHEN COALESCE(p.total_sem_frete, 0) > 0 AND COALESCE(p.total_com_frete, 0) > 0 THEN p.total_com_frete
                    WHEN COALESCE(p.total_sem_frete, 0) = 0 AND COALESCE(p.total_com_frete, 0) > 0 
                        THEN p.total_com_frete + (COALESCE(p.peso_total_kg, 0) * COALESCE(p.valor_frete_to, 0) / 1000)
                    WHEN COALESCE(p.total_sem_frete, 0) > 0 AND COALESCE(p.total_com_frete, 0) = 0 THEN p.total_sem_frete
                    ELSE COALESCE(p.total_com_frete, p.total_sem_frete, 0)
                END                                     AS valor_com_frete
            FROM public.tb_pedidos p
            LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
            WHERE 1=1
            ORDER BY p.id_pedido DESC
            LIMIT 5;
        """
        print("Testando query_cliente...")
        cur.execute(query_cliente)
        rows_cli = cur.fetchall()
        print("Sucesso! Retornou:", len(rows_cli), "linhas.")
        print("Primeira linha:", rows_cli[0] if rows_cli else "Nenhuma")

        # 2. Test get_vendas_produtos query syntax
        query_produtos = """
            SELECT
                i.codigo                                AS codigo_produto,
                MAX(i.nome)                            AS produto,
                MAX(i.embalagem)                       AS embalagem,
                CAST(MAX(COALESCE(pr.peso, 0)) AS FLOAT) AS peso_liquido_unitario,
                CAST(SUM(i.quantidade) AS FLOAT)        AS quantidade,
                CAST(SUM(COALESCE(pr.peso, 0) * i.quantidade) AS FLOAT) AS peso_liquido_acumulado,
                CAST(SUM(
                    CASE
                        WHEN COALESCE(i.subtotal_sem_f, 0) > 0 AND COALESCE(i.subtotal_com_f, 0) > 0 THEN i.subtotal_sem_f
                        WHEN COALESCE(i.subtotal_sem_f, 0) = 0 AND COALESCE(i.subtotal_com_f, 0) > 0 THEN i.subtotal_com_f
                        ELSE COALESCE(i.subtotal_sem_f, 0)
                    END
                ) AS FLOAT) AS valor_sem_frete,
                CAST(SUM(
                    CASE
                        WHEN COALESCE(i.subtotal_sem_f, 0) > 0 AND COALESCE(i.subtotal_com_f, 0) > 0 THEN i.subtotal_com_f
                        WHEN COALESCE(i.subtotal_sem_f, 0) = 0 AND COALESCE(i.subtotal_com_f, 0) > 0 
                            THEN i.subtotal_com_f + (i.quantidade * COALESCE(NULLIF(pr.peso_bruto, 0), pr.peso, 0) * COALESCE(i.valor_frete_to, 0) / 1000)
                        WHEN COALESCE(i.subtotal_sem_f, 0) > 0 AND COALESCE(i.subtotal_com_f, 0) = 0 THEN i.subtotal_sem_f
                        ELSE COALESCE(i.subtotal_com_f, i.subtotal_sem_f, 0)
                    END
                ) AS FLOAT) AS valor_com_frete
            FROM public.tb_pedidos_itens i
            JOIN public.tb_pedidos p ON p.id_pedido = i.id_pedido
            LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
            LEFT JOIN public.t_cadastro_produto_v2 pr ON pr.codigo_supra = i.codigo
            WHERE i.quantidade > 0
            GROUP BY i.codigo
            ORDER BY peso_liquido_acumulado DESC
            LIMIT 5;
        """
        print("\nTestando query_produtos...")
        cur.execute(query_produtos)
        rows_prod = cur.fetchall()
        print("Sucesso! Retornou:", len(rows_prod), "linhas.")
        print("Primeira linha:", rows_prod[0] if rows_prod else "Nenhuma")
        
    except Exception as e:
        print("Erro:", e)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    check_queries()
