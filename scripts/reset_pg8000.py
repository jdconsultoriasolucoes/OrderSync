import os
import pg8000.native
import ssl
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password):
    return pwd_context.hash(password)

def reset_pg8000():
    db_url = os.environ.get("DATABASE_URL")
    print(f"Connecting to: {db_url}")
    
    # Parse URL manually for pg8000
    # postgresql://user:pass@host:port/dbname?sslmode=require
    from urllib.parse import urlparse
    u = urlparse(db_url)
    
    if not u.hostname:
        print("Invalid URL")
        return

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        conn = pg8000.native.Connection(
            user=u.username,
            password=u.password,
            host=u.hostname,
            port=u.port or 5432,
            database=u.path[1:], # remove leading slash
            ssl_context=ssl_context
        )
        
        email = "admin@ordersync.com"
        senha = "admin123"
        senha_hash = get_password_hash(senha)
        
        print(f"Checking {email}...")
        # pg8000 native uses :param style or ?
        result = conn.run("SELECT id FROM usuario WHERE email = :email", email=email)
        
        if result:
            row_id = result[0][0]
            print(f"User found (ID: {row_id}). Updating...")
            conn.run("UPDATE usuario SET senha_hash = :pw, ativo = true, funcao = 'admin' WHERE id = :id", 
                     pw=senha_hash, id=row_id)
            print("Updated.")
        else:
            print("User not found. Inserting...")
            conn.run("INSERT INTO usuario (nome, email, senha_hash, funcao, ativo) VALUES (:nome, :email, :pw, 'admin', true)", 
                     nome="Administrador", email=email, pw=senha_hash)
            print("Inserted.")

        conn.close()

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    reset_pg8000()
