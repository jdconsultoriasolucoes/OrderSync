import psycopg2
import os

db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Busca triggers e suas definições
    cur.execute("""
        SELECT 
            event_object_table AS table_name,
            trigger_name,
            event_manipulation AS event,
            action_statement AS definition
        FROM information_schema.triggers
        WHERE event_object_schema = 'public'
    """)
    
    triggers = cur.fetchall()
    print(f"Triggers encontrados ({len(triggers)}):")
    for t in triggers:
        print(f"Tabela: {t[0]} | Nome: {t[1]} | Evento: {t[2]}")
        # print(f"Definição: {t[3][:100]}...") # truncate for brevity
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"Erro: {e}")
