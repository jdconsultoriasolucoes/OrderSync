import requests
import json

API_URL = "http://127.0.0.1:8000"
# We need a token. I'll assume I can login or I'll try to cheat/mock it.
# Actually, the user says "POST /usuarios/ HTTP/1.1 422".
# I need to be authenticated as admin/gerente to even reach the validation step?
# Check `routers/usuario.py`: 
# `current_user: UsuarioModel = Depends(get_current_user)`
# If I'm not authenticated, I get 401. The user got 422.
# So the user IS authenticated.

# To reproduce, I need to login first. 
# But I don't have the password for an admin user easily available (unless I fetch from DB).
# I'll try to use a known default or just print the payload logic.

# Better: I will create a script that tries to validate the payload against the Pydantic model directly 
# by importing the schema. This avoids needing a running server/auth.

import sys
sys.path.append(r"e:\OrderSync\backend")

try:
    from schemas.usuario import UsuarioCreate
    from pydantic import ValidationError

    # Payload as sent by frontend
    payload = {
        "user_id": "",
        "nome": "Teste",
        "email": "teste@example.com",
        "senha": "Mudar@123",
        "funcao": "vendedor",
        "ativo": True
    }

    print("Attempting to validate payload:", payload)
    
    try:
        model = UsuarioCreate(**payload)
        print("Validation Successful!")
        print(model.dict())
    except ValidationError as e:
        print("\nVALIDATION ERROR:")
        print(e.json())

except ImportError as e:
    print(f"Import Error: {e}")
    # Fallback to requests if I can't import (path issues)
except Exception as e:
    print(f"Error: {e}")
