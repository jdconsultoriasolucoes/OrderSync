import sys
import os

# 1. Setup paths
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# 2. Imports
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from models.usuario import UsuarioModel
    from core.security import verify_password, get_password_hash, pwd_context
    from fastapi.testclient import TestClient
    from main import app
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

# 3. Connection Config (Explicit from User Request)
# "postgresql://jd_user:I2UjiqAE9Gfqy0cFE2nAhWxzR3J460Ef@dpg-d51l29l6ubrc738p5v5g-a.oregon-postgres.render.com/db_ordersync_kxha"
DB_URL_RAW = "postgresql://jd_user:I2UjiqAE9Gfqy0cFE2nAhWxzR3J460Ef@dpg-d51l29l6ubrc738p5v5g-a.oregon-postgres.render.com/db_ordersync_kxha"

# Ensure SSL is requested
if "sslmode" not in DB_URL_RAW:
    DB_URL = DB_URL_RAW + "?sslmode=require"
else:
    DB_URL = DB_URL_RAW

print(f"Target DB: {DB_URL.split('@')[1]}") # Print host only for sanity

def debug_login():
    print("\n[1/3] Connecting to DB...")
    try:
        engine = create_engine(DB_URL, pool_pre_ping=True)
        SessionDebug = sessionmaker(bind=engine)
        db = SessionDebug()
        
        # Test Connection
        db.execute(text("SELECT 1"))
        print(">> Connection OK.")
    except Exception as e:
        print(f">> DB Connection FAILED: {e}")
        return

    print("\n[2/3] Checking Admin User...")
    try:
        email = "admin@ordersync.com"
        user = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
        
        if not user:
            print(f">> User {email} NOT FOUND. Creating...")
            user = UsuarioModel(
                email=email,
                nome="Admin Debug",
                senha_hash=get_password_hash("admin123"),
                funcao="admin",
                ativo=True
            )
            db.add(user)
            db.commit()
            print(">> User CREATED with password 'admin123'.")
        else:
            print(f">> User Found: ID={user.id}, Role={user.funcao}, Active={user.ativo}")
            
            # Check password
            if verify_password("admin123", user.senha_hash):
                print(">> Password 'admin123' MATCHES the hash in DB.")
            else:
                print(">> Password DOES NOT MATCH. Resetting...")
                user.senha_hash = get_password_hash("admin123")
                db.commit()
                print(">> Password RESET to 'admin123'.")
                
    except Exception as e:
        print(f">> User Check FAILED: {e}")
    finally:
        db.close()

    print("\n[3/3] Testing API Login via Application...")
    try:
        # Override session in app (optional, but good if app uses env var that might be different)
        # But TestClient uses the app as configured. 
        # If app is configured with .env, it might use a different URL? 
        # Let's trust app configuration for now.
        
        client = TestClient(app)
        payload = {"username": "admin@ordersync.com", "password": "admin123"}
        response = client.post("/token", data=payload)
        
        print(f">> Status: {response.status_code}")
        if response.status_code == 200:
            print(">> LOGIN SUCCESS! Token received.")
            # print(response.json())
        else:
            print(f">> LOGIN FAILED: {response.text}")
            
    except Exception as e:
        print(f">> API Test FAILED: {e}")

if __name__ == "__main__":
    debug_login()
