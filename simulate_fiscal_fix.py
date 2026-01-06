from decimal import Decimal

# Mocked functions from fiscal.py
def _norm(s):
    return (s or "").strip().lower()

def decide_st(tipo, tipo_cliente, forcar_iva_st):
    motivos = []
    
    # Logic copied from UPDATED fiscal.py
    is_pet = _norm(tipo) == "pet" or _norm(tipo) == "insumos"
    if is_pet:
        motivos.append(f"tipo={tipo}")

    is_revenda = _norm(tipo_cliente) == "revenda" 
    if is_revenda:
        motivos.append("cliente=Revenda")

    aplica = is_pet and is_revenda
    return aplica, motivos

# Simulation
print("--- Simulation for Gabriela (Revenda) and Product (INSUMOS) ---")
tipo_prod = "INSUMOS"
tipo_cli = "Revenda"

aplica, motivos = decide_st(tipo_prod, tipo_cli, False)
print(f"Product Type: {tipo_prod}")
print(f"Client Type: {tipo_cli}")
print(f"Result: Apply ST? {aplica}")
print(f"Reasons: {motivos}")

if aplica:
    print("SUCCESS: Logic now accepts INSUMOS.")
else:
    print("FAILURE: Logic still rejects INSUMOS.")
