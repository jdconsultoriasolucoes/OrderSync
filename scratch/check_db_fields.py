import re

# Read migration_dev_to_prod.sql to find create table for t_cadastro_cliente_v2 and tb_clientes
with open(r'e:\OrderSync\migration_dev_to_prod.sql', 'r', encoding='utf-8', errors='ignore') as f:
    sql = f.read()

tables = re.findall(r'CREATE TABLE [^;]+;', sql, re.IGNORECASE)
for t in tables:
    if 't_cadastro_cliente' in t or 'tb_clientes' in t:
        print('=== SQL TABLE DEFINITION ===')
        print(t)

