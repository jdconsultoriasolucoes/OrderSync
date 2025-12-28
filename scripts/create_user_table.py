
import os
import sys
from dotenv import load_dotenv

# Ensure backend path is available
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Import Model
from database import Base
from models.usuario import UsuarioModel

# Load Env
env_path = os.path.join(os.getcwd(), 'backend', '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.getcwd(), '.env')
load_dotenv(env_path)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found.")
    sys.exit(1)

# Usage of Passlib for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user_table():
    print("Connecting to DB...")
    engine = create_engine(DATABASE_URL)
    
    # Create Table
    print("Creating table t_usuario...")
    Base.metadata.create_all(bind=engine) # Creates if not exists
    print("Table created/verified.")

    # Create Default Admin
    session = Session(bind=engine)
    try:
        admin_email = "admin@ordersync.com"
        existing_admin = session.query(UsuarioModel).filter(UsuarioModel.email == admin_email).first()
        
        if not existing_admin:
            print(f"Creating default admin: {admin_email}")
            hashed_pw = pwd_context.hash("admin123")
            admin_user = UsuarioModel(
                nome="Administrador Sistema",
                email=admin_email,
                senha_hash=hashed_pw,
                funcao="admin",
                ativo=True
            )
            session.add(admin_user)
            session.commit()
            print("Default Admin created successfully.")
        else:
            print("Default Admin already exists.")
            
    except Exception as e:
        print(f"Error creating admin: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_user_table()
