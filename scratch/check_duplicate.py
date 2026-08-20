import sys
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:postgres@localhost:5432/ordersync')
with engine.connect() as conn:
    rs = conn.execute(text("select distinct marca, length(marca) from t_cadastro_produto_v2 where marca like '06 EQUINOS%'"))
    for row in rs:
        print(f"'{row[0]}', length: {row[1]}")
