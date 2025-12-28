import sys
import os
# Ensure backend path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy.orm import Session
from database import SessionLocal
from core.security import get_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.usuario import UsuarioModel

def reset_admin():
    # Force SSL for Render and Keepalive
    url = os.environ["DATABASE_URL"]
    
    # Ensure URL has valid lib if needed, but standard should work.
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 60,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
    
    engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
    SessionManual = sessionmaker(bind=engine)
    db = SessionManual()
    
    try:
        email = "admin@ordersync.com"
        senha_nova = "admin123"
        print(f"Checking user: {email}...")

        user = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
        
        if user:
            print(f"User found (ID: {user.id}). Resetting password to '{senha_nova}'...")
            user.senha_hash = get_password_hash(senha_nova)
            user.ativo = True
            user.funcao = "admin" # Ensure admin role
            db.commit()
            print("Password reset successfully.")
        else:
            print(f"User NOT found. Creating new admin...")
            new_user = UsuarioModel(
                email=email,
                nome="Administrador Sistema",
                senha_hash=get_password_hash(senha_nova),
                funcao="admin",
                ativo=True
            )
            db.add(new_user)
            db.commit()
            print(f"User created successfully with password '{senha_nova}'.")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin()
