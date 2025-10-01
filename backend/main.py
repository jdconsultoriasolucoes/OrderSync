import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- imports extras para o middleware de erro ---
import logging, traceback, uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# Routers
from routers import cliente, listas, fiscal
from routers.tabela_preco import router_meta, router as router_tabela
from routers import pedido_preview, link_pedido

# ---- logging base (simples) ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ordersync.errors")

app = FastAPI()

@app.get("/")
def root():
    return {"mensagem": "API do OrderSync está rodando"}

# ---- CORS ----
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
    allow_headers=["*"],
)

# ---- MIDDLEWARE: loga qualquer 5xx e captura exceções com error_id ----
@app.middleware("http")
async def log_5xx(request: Request, call_next):
    try:
        resp = await call_next(request)
        if resp.status_code >= 500:
            logger.error(
                "5xx: %s %s?%s -> %s",
                request.method, request.url.path, request.url.query, resp.status_code
            )
        return resp
    except Exception:
        err_id = uuid.uuid4().hex[:8]
        logger.error(
            "EXC %s: %s %s?%s\n%s",
            err_id, request.method, request.url.path, request.url.query,
            traceback.format_exc()
        )
        return JSONResponse(
            {"detail": "Internal Server Error", "error_id": err_id},
            status_code=500
        )

# (mantive teu header de debug)
@app.middleware("http")
async def add_debug_header(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["x-cors-debug"] = "main.py-cors-v1"
    return resp

# ---- Routers (mesma ordem que você já usava) ----
app.include_router(router_meta)          # /tabela_preco/meta/*
app.include_router(router_tabela)        # /tabela_preco/*
app.include_router(cliente.router, prefix="/cliente", tags=["Cliente"])
app.include_router(listas.router, prefix="/listas", tags=["Listas"])
app.include_router(fiscal.router)        # (sem prefixo se o router já tiver)
app.include_router(pedido_preview.router)
app.include_router(link_pedido.router)        
app.include_router(link_pedido.router_short)


from fastapi.staticfiles import StaticFiles
import os

# caminho real onde estão seus arquivos (ajuste se necessário)
static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "public")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
