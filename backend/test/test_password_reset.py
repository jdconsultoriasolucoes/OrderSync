
import sys
import os
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MOCK SMTP BEFORE IMPORTING SERVICE
import services.email_service
services.email_service._abrir_conexao = MagicMock()
mock_server = MagicMock()
services.email_service._abrir_conexao.return_value.__enter__.return_value = mock_server

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models.usuario import UsuarioModel
from core.security import get_password_hash, verify_password

client = TestClient(app)

def setup_test_user():
    db = SessionLocal()
    email = "reset_test@example.com"
    pwd = "OldPassword1!"
    
    # Clean up old
    old = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
    if old:
        db.delete(old)
        db.commit()

    # Create new
    user = UsuarioModel(
        email=email,
        nome="Reset Tester",
        senha_hash=get_password_hash(pwd),
        funcao="vendedor",
        ativo=True
    )
    db.add(user)
    db.commit()
    db.close()
    return email

def test_password_reset_flow():
    email = setup_test_user()
    print(f"Testing Reset Flow for {email}...")

    # 1. Request Password Reset (Forgot Password)
    print("STEP 1: Requesting /forgot-password...")
    resp = client.post("/token/forgot-password", json={"email": email})
    assert resp.status_code == 200
    print("✅ Request sent (200 OK).")
    
    # Verify email mock was called
    # Note: extracting the link from the mock call args to use in step 2 is tricky but possible.
    # The email service calls: server.sendmail(remetente, [dest], msg.as_string())
    # The message body contains link.
    
    if mock_server.sendmail.called:
        print("✅ SMTP sendmail was called.")
        call_args = mock_server.sendmail.call_args
        msg_str = call_args[0][2] # 3rd arg is msg string
        
        # Parse MIME message to find the HTML part
        import email as email_lib
        import re
        
        msg = email_lib.message_from_string(msg_str)
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    payload = part.get_payload(decode=True)
                    body = payload.decode('utf-8', errors='ignore')
                    break
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

        # Extract token from link in body
        match = re.search(r"token=([A-Za-z0-9\.\-_]+)", body)
        if match:
            token = match.group(1)
            print(f"✅ Token extracted: {token[:10]}...")
            
            # 2. Reset Password
            print("STEP 2: Resetting password...")
            new_pass = "NewStrongPass1!"
            
            resp_reset = client.post("/token/reset-password", json={
                "token": token,
                "senha_nova": new_pass
            })
            if resp_reset.status_code != 200:
                print(f"❌ Reset failed: {resp_reset.text}")
            assert resp_reset.status_code == 200
            print("✅ Password Reset Success (200 OK).")
            
            # 3. Verify Login with New Password
            print("STEP 3: Verifying Login with New Password...")
            
            # DEBUG: Check DB manually
            db = SessionLocal()
            u = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
            if u:
                print(f"DEBUG: Unknown user hash in DB: {u.senha_hash[:10]}...")
                from core.security import verify_password
                is_valid = verify_password(new_pass, u.senha_hash)
                print(f"DEBUG: verify_password(new_pass, db_hash) = {is_valid}")
            db.close()

            resp_login = client.post("/token", data={"username": email, "password": new_pass})
            if resp_login.status_code != 200:
                 print(f"❌ Login failed: {resp_login.text}")

            assert resp_login.status_code == 200
            print("✅ Login with New Password SUCCESS.")
            
        else:
            print("❌ Failed to extract token from email body:")
            print(body[:500]) # First 500 chars
            assert False, "Token not found in email"
    else:
        print("❌ SMTP sendmail was NOT called!")
        assert False, "Email not sent"

if __name__ == "__main__":
    test_password_reset_flow()
