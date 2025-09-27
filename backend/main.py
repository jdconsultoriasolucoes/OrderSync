import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import cliente, listas, fiscal
from routers.tabela_preco import router_meta, router as router_tabela  # ✅ use estes
from routers import pedido_preview

app = FastAPI()

@app.get("/")
def root():
    return {"mensagem": "API do OrderSync está rodando"}

ALLOWED_ORIGINS = [
    "https://ordersync-y7kg.onrender.com",  # FRONT (Render)
    "http://localhost:5500",                # FRONT local (ex. Live Server)
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # NÃO use "*"
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
    allow_headers=["*"],)

@app.middleware("http")
async def add_debug_header(request, call_next):
    resp = await call_next(request)
    resp.headers["x-cors-debug"] = "main.py-cors-v1"
    return resp

# Routers (sem duplicar e na ordem certa)
app.include_router(router_meta)          # /tabela_preco/meta/*
app.include_router(router_tabela)        # /tabela_preco/*
app.include_router(cliente.router, prefix="/cliente", tags=["Cliente"])
app.include_router(listas.router, prefix="/listas", tags=["Listas"])
app.include_router(fiscal.router)        # (deixe sem prefixo aqui se o router já tiver)
app.include_router(pedido_preview.router)

