import sys
sys.path.append('backend')
from database import SessionLocal
from models.cliente_v2 import ClienteModelV2
from services.excel_recadastro_service import gerar_excel_cliente_recadastro, gerar_nome_arquivo_recadastro

db = SessionLocal()
cli = db.query(ClienteModelV2).first()

if cli:
    print(f"Testing export for Client ID {cli.id} ({cli.cadastro_nome_cliente})...")
    excel_bytes = gerar_excel_cliente_recadastro(cli)
    filename = gerar_nome_arquivo_recadastro(cli)
    print(f"Successfully generated {len(excel_bytes)} bytes of Excel data!")
    print(f"Filename: {filename}.xlsx")
    with open(r'e:\OrderSync\scratch\test_output_recadastro.xlsx', 'wb') as f:
        f.write(excel_bytes)
    print("Saved test output to scratch/test_output_recadastro.xlsx!")
else:
    print("No client found in DB to test.")

db.close()
