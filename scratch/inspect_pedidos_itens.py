
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://ordersync_db_user:E0P2m6x1I8v7mX9uE4V7s1A6i3U8v2@dpg-cuid6n9u0jms73ep37gg-a.oregon-postgres.render.com/ordersync_db?sslmode=require"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tb_pedidos_itens'"))
    for row in res:
        print(f"{row[0]}: {row[1]}")
