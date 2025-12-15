
import io
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.testclient import TestClient
from typing import Optional
from datetime import date

app = FastAPI()

@app.post("/importar-lista")
async def importar_lista(
    tipo_lista: str = Form(...),
    validade_tabela: Optional[date] = Form(None),
    file: UploadFile = File(...),
):
    return {
        "tipo": tipo_lista,
        "validade": validade_tabela,
        "filename": file.filename
    }

client = TestClient(app)

def test_request():
    print("Testing correct request...")
    files = {'file': ('test.pdf', b'dummy content', 'application/pdf')}
    data = {
        'tipo_lista': 'INSUMOS',
        'validade_tabela': '2025-12-15'
    }
    response = client.post("/importar-lista", data=data, files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\nTesting empty date request (should be invalid if strictly date?)...")
    data_empty = {
        'tipo_lista': 'INSUMOS',
        'validade_tabela': '' 
    }
    response_empty = client.post("/importar-lista", data=data_empty, files=files)
    print(f"Status: {response_empty.status_code}")
    print(f"Response: {response_empty.json()}")

if __name__ == "__main__":
    test_request()
