import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- imports extras para o middleware de erro ---
import logging, traceback, uuid
from fastapi import FastAPI, Request, HTTPException,APIRouter
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path  
# Routers
from routers.tabela_preco import router_meta, router as router_tabela
from routers import pedido_preview, link_pedido, admin_config_email, cliente, listas, fiscal,pedidos,net_diag, produto, pedido_pdf, auth, usuario
from database import SessionLocal
# ---- logging base (simples) ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ordersync.errors")

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        resp.headers["Cache-Control"] = "no-store"  # browser não guarda nada
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp


app = FastAPI()

# --- STARTUP: Garantir usuario Admin ---
@app.on_event("startup")
def startup_ensure_admin():
    from database import SessionLocal
    from models.usuario import UsuarioModel
    from core.security import get_password_hash
    
    db = SessionLocal()
    try:
        email = "admin@ordersync.com"
        # Reset force
        user = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
        if user:
            # Se já existe, NÃO reseta a senha. Apenas loga que encontrou.
            logger.info("Admin user found. Skipping password reset.")
        else:
            new_user = UsuarioModel(
                email=email, 
                nome="Admin", 
                senha_hash=get_password_hash(os.environ.get("ADMIN_PASSWORD", "admin123")), 
                funcao="admin", 
                ativo=True
            )
            db.add(new_user)
            logger.info("ADMIN USER CREATED: admin123")
            
        db.commit()
    except Exception as e:
        logger.error(f"Startup Admin Reset Failed: {e}")
    finally:
        db.close()


# Root route handled by StaticFiles
# @app.get("/")
# def root():
#     return {"mensagem": "API do OrderSync está rodando"}

# ---- Origens permitidas ----
ALLOWED_ORIGINS = [
    "https://ordersync-y7kg.onrender.com",  # FRONT (Render)
    "https://ordersync-frontend.onrender.com", # Caso mude nome
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
    except Exception as e:
        err_id = uuid.uuid4().hex[:8]
        logger.error(
            "EXC %s: %s %s?%s\n%s",
            err_id, request.method, request.url.path, request.url.query,
            traceback.format_exc()
        )
        # Show real error in Dev, generic in Prod (based on ENV)
        is_dev = os.environ.get("ENVIRONMENT", "development") == "development"
        detail_msg = f"Internal Server Error: {str(e)}" if is_dev else "Internal Server Error"
        
        body = {"detail": detail_msg, "error_id": err_id}
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
app.include_router(net_diag.router)
app.include_router(produto.router)
app.include_router(pedido_pdf.router)
app.include_router(auth.router)
app.include_router(usuario.router)

# ---- Static (se precisar servir arquivos públicos do front) ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Suporta 2 layouts de repo:
# 1) main.py em src/ -> repo_root/frontend/public
# 2) main.py na raiz  -> raiz/frontend/public
candidates = [
    os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "public")),
    os.path.abspath(os.path.join(BASE_DIR, "frontend", "public")),
]

static_dir = next((p for p in candidates if os.path.isdir(p)), None)
if not static_dir:
    logger.error("[STATIC] 'frontend/public' NÃO encontrado. Candidatos: %s", candidates)
    # mantém o primeiro como fallback pra evitar quebrar o mount
    static_dir = candidates[0]

CONFIG_STATIC = Path(static_dir) / "config_email"

logger.info("[STATIC] /static -> %s", static_dir)
if not os.path.isdir(static_dir):
    logger.error("[STATIC] Pasta NÃO existe: %s", static_dir)

# Auto-mount subdirectories of public to root
if os.path.exists(static_dir):
    for item in os.listdir(static_dir):
        full_path = os.path.join(static_dir, item)
        if os.path.isdir(full_path):
            # Mount /js, /css, /clientes, /produto, etc.
            app.mount(f"/{item}", StaticFiles(directory=full_path), name=item)

# Also mount /static explicitly
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def root():
    # Attempt to find index.html in frontend root (parent of public)
    # static_dir is .../frontend/public
    # so .../frontend/index.html is one level up
    index_path = os.path.abspath(os.path.join(static_dir, "..", "index.html"))
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"mensagem": "API do OrderSync está rodando (Frontend não encontrado)"}

@app.get("/admin/config-email")
def config_email_page():
    # sempre aponta para o HTML dentro do /static
    return RedirectResponse(url="/static/config_email/config_email.html")


@app.middleware("http")
async def no_cache_static_tabela_preco(request, call_next):
    resp = await call_next(request)
    p = request.url.path

    no_cache_roots = ("/static/tabela_preco/", "/static/config_email/")
    exts = (".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".webp")

    if any(p.startswith(root) for root in no_cache_roots) and any(p.endswith(ext) for ext in exts):
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



        
