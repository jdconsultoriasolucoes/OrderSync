import os
import sys
from sqlalchemy import create_engine, MetaData, Table, Column, BigInteger, String, Boolean, DateTime, Sequence, func
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

# Need passlib for hashing. Assuming it's installed in the env.
try:
    from passlib.context import CryptContext
except ImportError:
    # Fallback or strict error. 
    # Usually backend has passlib. 
    # If not, we might need to rely on the backend's code, but imports might be messy path-wise.
    # Let's assume requirements are met or import from backend/core/security.py if path allows.
    pass

sys.path.append(os.path.join(os.getcwd(), 'backend'))
try:
    from core.security import get_password_hash
except ImportError:
    print("Could not import get_password_hash. Using dummy hash for testing? No, must be real.")
    # Implement simple backup or fail
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def get_password_hash(password):
        return pwd_context.hash(password)

PROD_DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

engine = create_engine(PROD_DB_URL, pool_pre_ping=True)
Base = declarative_base()

class UsuarioModel(Base):
    __tablename__ = "t_usuario"
    id = Column(BigInteger, Sequence('usuario_id_seq'), primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    funcao = Column(String, default="vendedor")
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now())
    criado_por = Column(String, nullable=True)

SessionLocal = sessionmaker(bind=engine)

def setup_admin():
    print("Connecting to Prod...")
    # 1. Ensure Table Exists
    Base.metadata.create_all(bind=engine)
    print("Table t_usuario verified/created.")

    session = SessionLocal()
    try:
        email = "admin@ordersync.com"
        password = "admin123"
        
        user = session.query(UsuarioModel).filter(UsuarioModel.email == email).first()
        if user:
            print(f"Update existing admin: {email}")
            user.senha_hash = get_password_hash(password)
            user.ativo = True
            user.funcao = "admin"
        else:
            print(f"Creating NEW admin: {email}")
            new_user = UsuarioModel(
                email=email,
                nome="Admin",
                senha_hash=get_password_hash(password),
                funcao="admin",
                ativo=True
            )
            session.add(new_user)
        
        session.commit()
        print(f"Admin setup complete. User: {email} / Pass: {password}")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    setup_admin()
