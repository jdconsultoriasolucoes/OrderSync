import sys
import os

# Ensure backend in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy.orm import Session
# Import the exact engine and session from the working app
from database import engine, SessionLocal 
from models.usuario import UsuarioModel
from core.security import get_password_hash
from sqlalchemy import text

def reset_with_app_engine():
    print("Connecting using backend.database engine...")
    
    # Test connection first
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Engine connection successful.")
    except Exception as e:
        print(f"Engine connection FAILED: {e}")
        return

    db = SessionLocal()
    try:
        email = "admin@ordersync.com"
        senha_nova = "admin123"
        print(f"Looking up {email}...")

        user = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
        
        if user:
            print(f"User found. Resetting...")
            user.senha_hash = get_password_hash(senha_nova)
            user.ativo = True
            user.funcao = "admin"
            db.commit()
            print("RESET SUCCESSFUL.")
        else:
            print(f"User NOT found. Creating...")
            new_user = UsuarioModel(
                email=email,
                nome="Admin",
                senha_hash=get_password_hash(senha_nova),
                funcao="admin",
                ativo=True
            )
            db.add(new_user)
            db.commit()
            print("CREATE SUCCESSFUL.")

    except Exception as e:
        print(f"Transaction ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_with_app_engine()
