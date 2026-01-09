from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()

# Use the hardcoded URL if env is missing, just for safety in this specific task context if needed, 
# but preferably verify env loading.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found")
    exit(1)

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)
columns = inspector.get_columns("t_cadastro_produto_v2")

found = False
for col in columns:
    if col["name"] == "filhos":
        print(f"Column 'filhos' found: {col}")
        found = True
        break

if not found:
    print("Column 'filhos' NOT found in t_cadastro_produto_v2")
