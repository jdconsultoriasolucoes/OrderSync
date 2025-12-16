
import io
from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException
from fastapi.testclient import TestClient
from typing import Optional
from datetime import date, datetime

# --- MOCKING SERVICES TO AVOID DEPENDENCIES ---
def parse_lista_precos(file_obj, tipo_lista=None, filename=None):
    import pandas as pd
    # Return a dummy DF
    return pd.DataFrame([{'codigo': '123', 'descricao': 'TESTE', 'preco_ton': 100}])

def importar_pdf_para_produto(db, df, nome_arquivo, usuario):
    return {
        "total_linhas": 1,
        "lista": "TEST LIST",
        "fornecedor": "TEST FORNECEDOR",
        "sync": {}
    }

# --- REPLICATING ROUTE LOGIC ---
app = FastAPI()

@app.post("/importar-lista")
async def importar_lista(
    request: Request,
    tipo_lista: str = Form(..., description="Tipo de lista: INSUMOS ou PET"),
    validade_tabela: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    # Mock DB extraction (not used in mock service anyway)
    db = None

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="O arquivo precisa ser um PDF.")

    tipo_raw = tipo_lista.upper().strip()

    if tipo_raw in ("INS", "INSUMO", "INSUMOS"):
        tipo = "INSUMOS"
    elif tipo_raw in ("PET", "PETS", "PET"):
        tipo = "PET"
    else:
        raise HTTPException(
            status_code=400,
            detail="Tipo de lista inválido. Use INSUMOS ou PET.",
        )

    # --- FIX LOGIC BEING TESTED ---
    dt_validade: Optional[date] = None
    if validade_tabela and validade_tabela.strip():
        try:
            dt_validade = date.fromisoformat(validade_tabela.strip())
        except ValueError:
            try:
                dt_validade = datetime.strptime(validade_tabela.strip(), "%Y-%m-%d").date()
            except:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Data de validade inválida: {validade_tabela}. Use o formato AAAA-MM-DD."
                )
    # ------------------------------

    try:
        df = parse_lista_precos(file.file, tipo_lista=tipo, filename=file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler PDF: {e}")

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Nenhuma linha válida encontrada no PDF.",
        )

    df["validade_tabela"] = dt_validade

    resumo = importar_pdf_para_produto(
        db,
        df,
        nome_arquivo=file.filename,
        usuario="IMPORT_MANUAL",  # depois trocar pelo usuário logado
    )

    sync = resumo.get("sync", {})

    return {
        "arquivo": file.filename,
        "tipo_lista": tipo,
        "validade_tabela": dt_validade,
        "total_linhas_pdf": int(len(df)),
    }

client = TestClient(app)

def test_request():
    print("Testing correct request (valid ISO date)...")
    files = {'file': ('test.pdf', b'dummy content', 'application/pdf')}
    data = {
        'tipo_lista': 'INSUMOS',
        'validade_tabela': '2025-12-15'
    }
    response = client.post("/importar-lista", data=data, files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200:
        print("SUCCESS: Valid ISO date accepted.")
    else:
        print("FAILURE: Valid ISO date rejected.")
    
    print("\nTesting empty date request (should be accepted as None)...")
    data_empty = {
        'tipo_lista': 'INSUMOS',
        'validade_tabela': '' 
    }
    response_empty = client.post("/importar-lista", data=data_empty, files=files)
    print(f"Status: {response_empty.status_code}")
    print(f"Response: {response_empty.json()}")
    if response_empty.status_code == 200:
        print("SUCCESS: Empty date accepted.")
    else:
        print("FAILURE: Empty date rejected.")

    print("\nTesting INVALID date request (should be 400)...")
    data_invalid = {
        'tipo_lista': 'INSUMOS',
        'validade_tabela': 'batata' 
    }
    response_invalid = client.post("/importar-lista", data=data_invalid, files=files)
    print(f"Status: {response_invalid.status_code}")
    print(f"Response: {response_invalid.json()}")
    if response_invalid.status_code == 400:
         print("SUCCESS: Invalid date rejected correctly.")
    else:
         print("FAILURE: Invalid date NOT rejected.")

if __name__ == "__main__":
    try:
        test_request()
    except ImportError:
        print("Skipping tests: Dependencies (pandas/fastapi) not installed in this shell.")
