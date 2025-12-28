import sys
import os

# Ensure backend path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_password_flow():
    print("Testing Password Management Flow...")
    
    # Setup: Ensure we have a clean Vendedor user
    # Login as Admin first to create/ensure user
    print("\n--- Setup: Admin Login ---")
    login_admin = {"username": "admin@ordersync.com", "password": "admin123"}
    resp = client.post("/token", data=login_admin)
    token_admin = resp.json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    
    # Create or update Vendedor
    vendedor_email = "vendedor_pwd@teste.com"
    resp_create = client.post("/usuarios/", json={
        "email": vendedor_email, "senha": "123", "nome": "Vendedor Pwd", "funcao": "vendedor", "ativo": True
    }, headers=headers_admin)
    print(f"DEBUG: Create User Response: {resp_create.status_code} - {resp_create.text}")

    if resp_create.status_code == 400 and "already registered" in resp_create.text:
        print("   User exists. Resetting password to '123' to ensure clean state...")
        # Get ID to reset
        users = client.get("/usuarios/", headers=headers_admin).json()
        target_id = next((u["id"] for u in users if u["email"] == vendedor_email), None)
        if target_id:
             client.post(f"/usuarios/{target_id}/reset-senha", json={"senha_nova": "123"}, headers=headers_admin)


    # 1. Login as Vendedor
    print("\n1. Vendedor Login (Initial Password '123')...")
    resp = client.post("/token", data={"username": vendedor_email, "password": "123"})
    if resp.status_code != 200:
        print(f"FAIL: Could not login as vendedor. {resp.text}")
        return
    token_vend = resp.json()["access_token"]
    headers_vend = {"Authorization": f"Bearer {token_vend}"}
    print("   Success.")

    # 2. Change Own Password
    print("\n2. Vendedor Changes Own Password (to '456')...")
    resp = client.post("/usuarios/me/senha", json={"senha_antiga": "123", "senha_nova": "456"}, headers=headers_vend)
    if resp.status_code == 200:
        print("   Success: Password Changed.")
    else:
        print(f"FAIL: {resp.text}")
        return

    # 3. Verify Login with New Password
    print("\n3. Verify Login with '456'...")
    resp = client.post("/token", data={"username": vendedor_email, "password": "456"})
    if resp.status_code == 200:
        print("   Success: Login worked with new password.")
    else:
        print(f"FAIL: Login failed with new password. {resp.text}")

    # 4. Admin Reset Password
    print("\n4. Admin Resets Vendedor Password (to '789')...")
    # First get user ID
    users = client.get("/usuarios/", headers=headers_admin).json()
    print(f"DEBUG: Users response: {users}")
    if isinstance(users, dict) and 'detail' in users:
         print(f"FAIL: Could not list users. {users}")
         return
    target_id = next((u["id"] for u in users if u["email"] == vendedor_email), None)
    
    resp = client.post(f"/usuarios/{target_id}/reset-senha", json={"senha_nova": "789"}, headers=headers_admin)
    if resp.status_code == 200:
        print("   Success: Admin reset password.")
    else:
        print(f"FAIL: Admin could not reset. {resp.text}")

    # 5. Verify Login with Reset Password
    print("\n5. Verify Login with '789'...")
    resp = client.post("/token", data={"username": vendedor_email, "password": "789"})
    if resp.status_code == 200:
        print("   Success: Login worked with reset password.")
    else:
        print(f"FAIL: Login failed with reset password. {resp.text}")

if __name__ == "__main__":
    test_password_flow()
