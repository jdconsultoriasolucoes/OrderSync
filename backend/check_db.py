from database import engine
from sqlalchemy import text
with engine.connect() as conn:
    print('--- PEDIDOS ---')
    result = conn.execute(text('SELECT id_pedido, total_pedido, total_sem_frete, total_com_frete, valor_frete_to, peso_total_kg FROM tb_pedidos LIMIT 5'))
    for row in result:
        print(row)
    print('--- ITENS ---')
    result = conn.execute(text('SELECT id_pedido, codigo, quantidade, subtotal_sem_f, subtotal_com_f, valor_frete_to FROM tb_pedidos_itens LIMIT 5'))
    for row in result:
        print(row)
