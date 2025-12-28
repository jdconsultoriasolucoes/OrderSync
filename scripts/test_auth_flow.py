
import sys
import os

# Ensure backend path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_auth():
    print("Testing Auth Flow with TestClient...")

    # 1. Login with Admin
    print("\n1. Login (Admin)...")
    login_data = {"username": "admin@ordersync.com", "password": "admin123"}
    resp = client.post("/token", data=login_data)
    
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        print(f"   Success! Token: {token[:15]}...")
    else:
        print(f"   Failed Login: {resp.text}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check Protected Route (List Users - Admin only)
    print("\n2. List Users (Protected)...")
    resp = client.get("/usuarios/", headers=headers)
    if resp.status_code == 200:
        print(f"   Success! Users found: {len(resp.json())}")
    else:
        print(f"   Failed: {resp.status_code} - {resp.text}")

    # 3. Create Vendedor
    print("\n3. Create Restricted User (Vendedor)...")
    new_user = {
        "email": "vendedor@teste.com",
        "senha": "123", 
        "nome": "Vendedor Teste",
        "funcao": "vendedor",
        "ativo": True
    }
    resp = client.post("/usuarios/", json=new_user, headers=headers)
    if resp.status_code == 200 or "already registered" in resp.text:
         print("   User Created/Exists.")
    else:
         print(f"   Failed: {resp.text}")

    # 4. Login as Vendedor
    print("\n4. Login (Vendedor)...")
    login_v = {"username": "vendedor@teste.com", "password": "123"}
    resp = client.post("/token", data=login_v)
    token_v = resp.json().get("access_token")
    headers_v = {"Authorization": f"Bearer {token_v}"}

    # 5. Vendedor trying Admin route
    print("\n5. Vendedor accessing Users Route (Should Fail/Forbidden)...")
    # Note: Our router logic says "admin" or "gerente" for list users. Vendedor should fail.
    resp = client.get("/usuarios/", headers=headers_v)
    if resp.status_code == 403:
        print("   Success! Access Forbidden as expected.")
    else:
        print(f"   FAIL! Vendedor accessed admin route: {resp.status_code}")

if __name__ == "__main__":
    test_auth()
