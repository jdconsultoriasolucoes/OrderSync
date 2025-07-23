import sys #Linha temporaria
import os #Linha temporaria
sys.path.append(os.path.dirname(os.path.abspath(__file__))) #Linha temporaria
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import cliente

app = FastAPI()

from db import fake_db  # Força a execução de fake_db e popula a lista

# Middleware de CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # pode restringir depois para seu domínio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir os routers
app.include_router(cliente.router, prefix="/cliente", tags=["Cliente"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
