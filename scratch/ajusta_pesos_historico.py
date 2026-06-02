import os
import psycopg2
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env se existir
load_dotenv()

DB_URL = os.getenv("DATABASE_URL") or "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

import time

def connect_with_retry(db_url, max_retries=5, delay=2):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return psycopg2.connect(db_url)
        except psycopg2.OperationalError as e:
            last_error = e
            print(f"Tentativa de conexao {attempt}/{max_retries} falhou: {e}. Retentando em {delay}s...")
            time.sleep(delay)
    raise last_error

def ajustar_pesos():
    conn = None
    cur = None
    try:
        conn = connect_with_retry(DB_URL)
        cur = conn.cursor()
        
        print("=== INICIANDO INSPEÇÃO DE PESOS ZERADOS ===")
        
        # 1. Contar itens com peso zerado ou nulo
        cur.execute("""
            SELECT COUNT(*) 
            FROM public.tb_pedidos_itens 
            WHERE peso_kg IS NULL OR peso_kg = 0;
        """)
        itens_zerados = cur.fetchone()[0]
        print(f"Itens com peso unitário (peso_kg) zerado ou nulo: {itens_zerados}")
        
        # 2. Contar pedidos com peso total zerado ou nulo
        cur.execute("""
            SELECT COUNT(*) 
            FROM public.tb_pedidos 
            WHERE peso_total_kg IS NULL OR peso_total_kg = 0;
        """)
        pedidos_zerados = cur.fetchone()[0]
        print(f"Pedidos com peso total (peso_total_kg) zerado ou nulo: {pedidos_zerados}")
        
        print("\n=== ATUALIZANDO PESO UNITÁRIO DOS ITENS CRUTANDO COM PRODUTOS ===")
        # Atualiza peso_kg na tb_pedidos_itens usando o peso_bruto (se > 0) senão o peso líquido do cadastro
        cur.execute("""
            UPDATE public.tb_pedidos_itens it
            SET peso_kg = COALESCE(NULLIF(p.peso_bruto, 0), p.peso, 0)
            FROM public.t_cadastro_produto_v2 p
            WHERE it.codigo = p.codigo_supra
              AND (it.peso_kg IS NULL OR it.peso_kg = 0);
        """)
        itens_atualizados = cur.rowcount
        print(f"Total de itens atualizados com peso do cadastro: {itens_atualizados}")
        
        print("\n=== RECALCULANDO PESO TOTAL DOS PEDIDOS NO CABEÇALHO ===")
        # Atualiza peso_total_kg na tb_pedidos somando (peso_kg * quantidade) de todos os seus itens
        cur.execute("""
            UPDATE public.tb_pedidos p
            SET peso_total_kg = (
                SELECT COALESCE(SUM(it.peso_kg * it.quantidade), 0)
                FROM public.tb_pedidos_itens it
                WHERE it.id_pedido = p.id_pedido
            )
            WHERE p.peso_total_kg IS NULL OR p.peso_total_kg = 0;
        """)
        pedidos_atualizados = cur.rowcount
        print(f"Total de pedidos atualizados com o novo peso total: {pedidos_atualizados}")
        
        # 3. Mostrar estado atual pós-atualização
        cur.execute("""
            SELECT COUNT(*) 
            FROM public.tb_pedidos_itens 
            WHERE peso_kg IS NULL OR peso_kg = 0;
        """)
        itens_zerados_pos = cur.fetchone()[0]
        print(f"Itens ainda zerados/nulos após o script: {itens_zerados_pos}")
        
        cur.execute("""
            SELECT COUNT(*) 
            FROM public.tb_pedidos 
            WHERE peso_total_kg IS NULL OR peso_total_kg = 0;
        """)
        pedidos_zerados_pos = cur.fetchone()[0]
        print(f"Pedidos ainda zerados/nulos após o script: {pedidos_zerados_pos}")
        
        conn.commit()
        print("\n=== PROCESSO CONCLUÍDO COM SUCESSO E TRANSACÕES COMMITA DAS! ===")
        
    except Exception as e:
        print(f"Erro ao ajustar pesos: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == '__main__':
    ajustar_pesos()
