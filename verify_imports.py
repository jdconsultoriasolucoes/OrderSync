
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

print("Verifying imports...")
try:
    import backend.services.produto_pdf
    print("MATCH: services.produto_pdf")
    import backend.services.produto_regras
    print("MATCH: services.produto_regras")
    import backend.routers.produto
    print("MATCH: routers.produto")
    print("ALL GOOD")
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"GENERAL ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
