import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.cliente_v2 import ClienteModelV2
from services.excel_recadastro_service import gerar_excel_cliente_recadastro

def test_export_mock():
    try:
        # Create a mock cliente with data that should go into the second sheet
        mock_cliente = ClienteModelV2(
            id=9999,
            cadastro_nome_cliente="CLIENTE TESTE LIMITADO",
            cadastro_codigo_da_empresa="987654",
            referencias_comerciais=[
                {"empresa": "EMPRESA A", "cidade": "SÃO PAULO", "telefone": "1199999999", "contato": "JOÃO"},
                {"empresa": "EMPRESA B", "cidade": "CAMPINAS", "telefone": "1988888888", "contato": "MARIA"}
            ],
            bens_imoveis=[
                {"imovel": "FAZENDA", "localizacao": "INTERIOR", "area": "100ha", "valor": 1500000.0, "hipotecado": "Não"}
            ],
            planteis_animais=[
                {"especie": "BOVINO", "numero": 500, "consumo_diario": 2.5, "consumo_mensal": 37500}
            ],
            bens_moveis=[
                {"marca": "JOHN DEERE", "modelo": "TRATOR", "valor": 300000.0, "alienado": "Sim"}
            ]
        )
            
        print(f"Testando exportação (Recadastro) para cliente mock: {mock_cliente.cadastro_nome_cliente}...")
        
        excel_bytes = gerar_excel_cliente_recadastro(mock_cliente)
        
        output_path = os.path.join(os.path.dirname(__file__), f"test_recadastro_mock.xlsx")
        with open(output_path, "wb") as f:
            f.write(excel_bytes)
            
        print(f"Sucesso! Arquivo salvo em: {output_path}")
    except Exception as e:
        print("====== ERRO CAPTURADO ======")
        traceback.print_exc()

if __name__ == "__main__":
    test_export_mock()
