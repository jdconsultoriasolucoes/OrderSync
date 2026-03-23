import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- imports extras para o middleware de erro ---
import logging, traceback, uuid
from fastapi import FastAPI, Request, HTTPException, APIRouter, Depends
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path  
# Routers
from routers.tabela_preco import router_meta, router as router_tabela
from routers import pedido_preview, link_pedido, admin_config_email, cliente, listas, fiscal,pedidos,net_diag, produto, pedido_pdf, auth, usuario, fornecedor, dashboard, captacao_pedidos
from database import SessionLocal

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.rate_limit import limiter
from core.exceptions import OrderSyncException

# ---- logging base (estruturado em JSON p/ APM) ----
import logging.config

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(error_id)s %(trace_id)s",
            "datefmt": "%Y-%m-%dT%H:%M:%SZ"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        },
    },
    "loggers": {
        "ordersync.errors": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
        "ordersync.worker": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
})

logger = logging.getLogger("ordersync.errors")

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        resp.headers["Cache-Control"] = "no-store"  # browser não guarda nada
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        
        # Enforce UTF-8 for text files (important for Prod on Render)
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type and "charset" not in content_type.lower():
            resp.headers["content-type"] = "text/html; charset=utf-8"
        elif content_type.startswith("text/") and "charset" not in content_type.lower():
            resp.headers["content-type"] = f"{content_type}; charset=utf-8"
            
        return resp

class Utf8StaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        
        # Enforce UTF-8 for text files
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type and "charset" not in content_type.lower():
            resp.headers["content-type"] = "text/html; charset=utf-8"
        elif content_type.startswith("text/") and "charset" not in content_type.lower():
            resp.headers["content-type"] = f"{content_type}; charset=utf-8"
            
        return resp


app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- STARTUP: Garantir usuario Admin ---
@app.on_event("startup")
def startup_ensure_admin():
    from database import SessionLocal
    from models.usuario import UsuarioModel
    from core.security import get_password_hash
    # --- FIX CRITICO: Criar tabelas antes de consultar ---
    from database import Base, engine
    from models.idempotency import IdempotencyKeyModel
    from models.background_task import BackgroundTaskModel
    Base.metadata.create_all(bind=engine)

    # --- MIGRAÇOES DE SCHEMA (Colunas novas) ---
    from services.db_migrations import run_migrations
    run_migrations()
    
    db = SessionLocal()
    try:
        from core.worker import start_background_worker
        start_background_worker()
        
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
    "https://ordersync-qwc1.onrender.com",     # NOVO FRONT (Production)
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

@app.exception_handler(OrderSyncException)
async def ordersync_exception_handler(request: Request, exc: OrderSyncException):
    logger.warning("OrderSyncException %s: %s\n%s", exc.trace_id, exc.message, traceback.format_exc())
    resp = JSONResponse(exc.to_dict(), status_code=exc.status_code)
    resp.headers["x-error-id"] = exc.trace_id
    return _apply_cors_headers(resp, request.headers.get("origin"))

# ---- Routers ----
app.include_router(router_meta)                # /tabela_preco/meta/*
app.include_router(router_tabela)              # /tabela_preco/*
app.include_router(cliente.router, prefix="/cliente", tags=["Cliente"])
app.include_router(listas.router, prefix="/listas", tags=["Listas"])
app.include_router(fiscal.router, prefix="/fiscal")              # (prefixo padronizado)
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
app.include_router(fornecedor.router)
app.include_router(dashboard.router)

from routers import system_tables, transporte, relatorios
app.include_router(system_tables.router)

# ---- Novos Módulos de Relatórios/Logística ----
app.include_router(transporte.router)
app.include_router(relatorios.router)
app.include_router(captacao_pedidos.router, prefix="/captacao-pedidos", tags=["Captacao Pedidos"])

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
            app.mount(f"/{item}", Utf8StaticFiles(directory=full_path), name=item)

# Also mount /static explicitly
app.mount("/static", Utf8StaticFiles(directory=static_dir), name="static")

@app.get("/design-system.css")
def get_design_system_css():
    css_path = os.path.join(static_dir, "design-system.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css; charset=utf-8")
    return Response(status_code=404)

@app.get("/")
def root():
    # Attempt to find index.html in frontend root (parent of public)
    # static_dir is .../frontend/public
    # so .../frontend/index.html is one level up
    index_path = os.path.abspath(os.path.join(static_dir, "..", "index.html"))
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html; charset=utf-8")
    return {"mensagem": "API do OrderSync está rodando (Frontend não encontrado)"}

@app.get("/api/health")
def healthcheck(db: SessionLocal = Depends(lambda: SessionLocal())):
    try:
        from sqlalchemy import text
        # Verifica 1 registro leve para atestar conectividade
        db.execute(text("SELECT 1")).scalar()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        logger.error(f"Healthcheck failed: {e}")
        return JSONResponse(status_code=503, content={"status": "error", "db": "disconnected"})
    finally:
         db.close()

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

# ---- CORS: Usando Regex para garantir todos os subdominios Render ----
app.add_middleware(
    CORSMiddleware,
    # Permite qualquer subdominio ordersync-XXXX.onrender.com
    allow_origin_regex=r"https://ordersync.*\.onrender\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-cors-debug", "x-error-id"],
    max_age=86400,
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=ALLOWED_ORIGINS,     # não usar "*" se há credenciais
#     allow_credentials=True,
#     allow_methods=["*"],               # GET/POST/PUT/PATCH/DELETE/OPTIONS
#     allow_headers=["*"],
#     expose_headers=["x-cors-debug", "x-error-id"],
#     max_age=86400,
# )




        
