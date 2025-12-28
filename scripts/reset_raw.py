import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# Get pwd hash logic

# Get pwd hash logic
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password):
    return pwd_context.hash(password)

def reset_raw():
    db_url = os.environ.get("DATABASE_URL")
    print(f"Connecting to: {db_url}")
    
    conn = None
    try:
        # Append sslmode if missing
        if "sslmode" not in db_url:
            db_url += "?sslmode=require"
            
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        email = "admin@ordersync.com"
        senha = "admin123"
        senha_hash = get_password_hash(senha)
        
        print(f"Checking {email}...")
        cur.execute("SELECT id FROM usuario WHERE email = %s", (email,))
        row = cur.fetchone()
        
        if row:
            print(f"User found (ID: {row[0]}). Updating password...")
            cur.execute("UPDATE usuario SET senha_hash = %s, ativo = true, funcao = 'admin' WHERE id = %s", (senha_hash, row[0]))
            print("Updated.")
        else:
            print("User not found. Inserting...")
            cur.execute("INSERT INTO usuario (nome, email, senha_hash, funcao, ativo) VALUES (%s, %s, %s, 'admin', true)", 
                        ("Administrador", email, senha_hash))
            print("Inserted.")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    reset_raw()
