import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- imports extras para o middleware de erro ---
import logging, traceback, uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path  
# Routers
from routers.tabela_preco import router_meta, router as router_tabela
from routers import pedido_preview, link_pedido, admin_config_email, cliente, listas, fiscal,pedidos

# ---- logging base (simples) ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ordersync.errors")

app = FastAPI()

@app.get("/")
def root():
    return {"mensagem": "API do OrderSync está rodando"}

# ---- Origens permitidas ----
ALLOWED_ORIGINS = [
    "https://ordersync-v7kg.onrender.com",  # FRONT (Render) - deixa os dois se alterna
    "https://ordersync-y7kg.onrender.com",
    "http://localhost:5500",                # FRONT local (ex. Live Server)
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
_ALLOWED_SET = set(ALLOWED_ORIGINS)

def _apply_cors_headers(resp: JSONResponse, origin: str | None):
    """Garante CORS mesmo em respostas de erro criadas pelo nosso middleware."""
    if origin and origin in _ALLOWED_SET:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
        resp.headers["Access-Control-Allow-Credentials"] = "true"
    return resp

# ---- MIDDLEWARE: loga 5xx e SEMPRE devolve CORS em erros ----
@app.middleware("http")
async def errors_with_cors(request: Request, call_next):
    try:
        resp = await call_next(request)
        if resp.status_code >= 500:
            logger.error(
                "5xx: %s %s?%s -> %s",
                request.method, request.url.path, request.url.query, resp.status_code
            )
        return resp
    except HTTPException as e:
        err_id = uuid.uuid4().hex[:8]
        logger.error(
            "HTTPEXC %s: %s %s?%s\n%s",
            err_id, request.method, request.url.path, request.url.query,
            traceback.format_exc()
        )
        body = {"detail": e.detail, "error_id": err_id}
        resp = JSONResponse(body, status_code=e.status_code)
        resp.headers["x-error-id"] = err_id
        return _apply_cors_headers(resp, request.headers.get("origin"))
    except Exception:
        err_id = uuid.uuid4().hex[:8]
        logger.error(
            "EXC %s: %s %s?%s\n%s",
            err_id, request.method, request.url.path, request.url.query,
            traceback.format_exc()
        )
        body = {"detail": "Internal Server Error", "error_id": err_id}
        resp = JSONResponse(body, status_code=500)
        resp.headers["x-error-id"] = err_id
        return _apply_cors_headers(resp, request.headers.get("origin"))

# (debug header p/ inspecionar no navegador)
@app.middleware("http")
async def add_debug_header(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["x-cors-debug"] = "main.py-cors-v2"
    return resp

# ---- Routers ----
app.include_router(router_meta)                # /tabela_preco/meta/*
app.include_router(router_tabela)              # /tabela_preco/*
app.include_router(cliente.router, prefix="/cliente", tags=["Cliente"])
app.include_router(listas.router, prefix="/listas", tags=["Listas"])
app.include_router(fiscal.router)              # (sem prefixo se o router já tiver)
app.include_router(pedido_preview.router)
app.include_router(link_pedido.router)
app.include_router(link_pedido.router_short)
app.include_router(pedidos.router)
app.include_router(admin_config_email.router)
# ---- Static (se precisar servir arquivos públicos do front) ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "public"))
CONFIG_STATIC = Path(static_dir) / "config_email"

# logs úteis pra saber o caminho real em produção
logger.info(f"[STATIC] /static -> {static_dir}")
if not os.path.isdir(static_dir):
    logger.error(f"[STATIC] Pasta NÃO existe: {static_dir}")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ---- Rota de debug para listar o conteúdo de /static ----
from fastapi.responses import JSONResponse

@app.get("/_debug/static-list", include_in_schema=False)
def _debug_static_list():
    try:
        paths = []
        for root, _, files in os.walk(static_dir):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), static_dir).replace("\\", "/")
                paths.append(rel)
        return {"static_dir": static_dir, "files": sorted(paths)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/admin/static/config_email.css", include_in_schema=False)
def serve_cfg_email_css():
    p = CONFIG_STATIC / "config_email.css"
    if not p.exists():
        raise HTTPException(status_code=404, detail="CSS não encontrado")
    return FileResponse(
        p,
        media_type="text/css",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )

@app.get("/admin/static/config_email.js", include_in_schema=False)
def serve_cfg_email_js():
    p = CONFIG_STATIC / "config_email.js"
    if not p.exists():
        raise HTTPException(status_code=404, detail="JS não encontrado")
    return FileResponse(
        p,
        media_type="application/javascript",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )







@app.middleware("http")
async def no_cache_static_tabela_preco(request, call_next):
    resp = await call_next(request)
    p = request.url.path

    if p.startswith("/static/tabela_preco/") and any(
        p.endswith(ext) for ext in (".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".webp")
    ):
        # Mata cache do browser e de proxies/CDNs
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    return resp

# ---- CORS: adicionar por ÚLTIMO (camada mais externa) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,     # não usar "*" se há credenciais
    allow_credentials=True,
    allow_methods=["*"],               # GET/POST/PUT/PATCH/DELETE/OPTIONS
    allow_headers=["*"],
    expose_headers=["x-cors-debug", "x-error-id"],
    max_age=86400,
)

# # Alternativa, se o subdomínio do Render variar:
# app.add_middleware(
#     CORSMiddleware,
#     allow_origin_regex=r"https://ordersync-[a-z0-9]+\.onrender\.com$",
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["x-cors-debug", "x-error-id"],
#     max_age=86400,
# )
