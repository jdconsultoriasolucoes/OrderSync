import sys #Linha temporaria
import os #Linha temporaria
sys.path.append(os.path.dirname(os.path.abspath(__file__))) #Linha temporaria
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import cliente, listas, tabela_preco

app = FastAPI()

@app.get("/")
def root():
    return {"mensagem": "API do OrderSync está rodando"}

# Incluir os routers
app.include_router(cliente.router, prefix="/cliente", tags=["Cliente"])

#Deletar biblioteca abaixo apos conexão com o banco, para listagem de itens para o frontend.
app.include_router(listas.router, prefix="/listas", tags=["Listas"])

#Teste de conexão com o banco
#app.include_router(teste.router)

app.include_router(tabela_preco.router, prefix="/tabela_preco", tags=["Tabela de Preço"])

from db import fake_db  # Força a execução de fake_db e popula a lista

# Middleware de CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # pode restringir depois para seu domínio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)


