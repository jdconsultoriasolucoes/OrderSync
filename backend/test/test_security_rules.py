
import sys
import os
# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from schemas.usuario import UsuarioCreate

client = TestClient(app)

def test_password_complexity():
    print("Testing Password Complexity...")
    weak_passwords = [
        "short", "alllowercase", "ALLUPPERCASE", "NoSpecialChar1", "NoNumber!"
    ]
    
    # We validate directly against the schema to avoid needing a full DB session for this specific check
    # But actually, the validator is in the schema, so we can just instantiate the Pydantic model
    for pwd in weak_passwords:
        try:
            UsuarioCreate(email="test@example.com", nome="Test", senha=pwd)
            print(f"❌ FAILED: Weak password '{pwd}' was accepted!")
        except Exception as e:
            print(f"✅ PASSED: Weak password '{pwd}' rejected. Error: {e}")

    # Strong password
    try:
        UsuarioCreate(email="test@example.com", nome="Test", senha="StrongPassword1!")
        print("✅ PASSED: Strong password 'StrongPassword1!' accepted.")
    except Exception as e:
        print(f"❌ FAILED: Strong password rejected! Error: {e}")

if __name__ == "__main__":
    test_password_complexity()
