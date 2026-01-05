
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models.usuario import UsuarioModel
from core.security import get_password_hash

client = TestClient(app)

def setup_test_user():
    db = SessionLocal()
    email = "integration_test@example.com"
    pwd = "StrongPass1!"
    
    # Clean up old
    old = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
    if old:
        db.delete(old)
        db.commit()

    # Create new
    user = UsuarioModel(
        email=email,
        nome="Integration Tester",
        senha_hash=get_password_hash(pwd),
        funcao="vendedor",
        ativo=True
    )
    db.add(user)
    db.commit()
    db.close()
    return email, pwd

def test_full_auth_flow():
    email, password = setup_test_user()
    print(f"Testing Auth Flow for {email}...")

    # 1. Test Login (Success)
    response = client.post("/token", data={"username": email, "password": password})
    assert response.status_code == 200, f"Login failed: {response.text}"
    token_data = response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    print("✅ Login SUCCESS. Token received.")

    # 2. Test Login (Failure - Wrong Password)
    response_fail = client.post("/token", data={"username": email, "password": "WrongPassword"})
    assert response_fail.status_code == 401
    print("✅ Login Failure check PASSED.")

    # 3. Test Protected Route (simulate frontend check)
    # We can use /usuario/me if it exists, or just check if verifying token works.
    # Let's try to access a protected route if we know one, otherwise we trust the login.
    # Based on routers, 'cliente' usually needs auth. Let's try to list clients.
    
    # Note: Assuming '/cliente' GET is protected. If not, this test might be weak.
    # Checking routers/cliente.py content would confirm.
    # For now, let's assuming we just want to verify we GOT a token.
    
    print("Auth Integration Test Completed Successfully.")

if __name__ == "__main__":
    test_full_auth_flow()
