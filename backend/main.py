# main.py
import os
import sys
import logging
import traceback
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers.tabela_preco import router_meta, router as router_tabela
from routers import pedido_preview, link_pedido, admin_config_email, cliente, listas, fiscal, pedidos, net_diag, produto
# Garante imports relativos (ex.: routers/*)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Logging básico ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ordersync")

# --- App ---
app = FastAPI(title="OrderSync")

# --- CORS (robusto + compatível com seu código existente) ---
_raw = os.getenv("CORS_ORIGINS", "")  # ex.: "http://localhost:5500,https://front.onrender.com"

# Suporta "*" (DEV), remove espaços e barra final
if _raw.strip() == "*":
    ALLOWED_ORIGINS = ["*"]
else:
    ALLOWED_ORIGINS = [
        o.strip().rstrip("/") for o in _raw.split(",") if o.strip()
    ] or [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]

# Conjunto auxiliar (só quando não é curinga)
_ALLOWED_SET = set(ALLOWED_ORIGINS) if ALLOWED_ORIGINS != ["*"] else None


def _apply_cors_headers(resp: JSONResponse, origin: str | None):
    """
    Aplica CORS também nas respostas de erro (exceptions), para o navegador não bloquear.
    """
    if ALLOWED_ORIGINS == ["*"]:
        # Sem credentials quando é "*"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Vary"] = "Origin"
        return resp

    if origin and origin.rstrip("/") in _ALLOWED_SET:
        resp.headers["Access-Control-Allow-Origin"] = origin.rstrip("/")
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Vary"] = "Origin"
    return resp


# --- Middleware de erro com CORS ---
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


# (opcional) middleware para marcar origem aceita nas respostas de sucesso
@app.middleware("http")
async def attach_cors_debug_header(request: Request, call_next):
    resp = await call_next(request)
    origin = request.headers.get("origin")
    if ALLOWED_ORIGINS == ["*"]:
        resp.headers["x-cors-debug"] = "*"
    elif origin and origin.rstrip("/") in (_ALLOWED_SET or set()):
        resp.headers["x-cors-debug"] = "allowed"
    else:
        resp.headers["x-cors-debug"] = "blocked"
    return resp


# --- Static /public ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
candidates = [
    os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "public")),
    os.path.abspath(os.path.join(BASE_DIR, "frontend", "public")),
]
static_dir = next((p for p in candidates if os.path.isdir(p)), None)
if not static_dir:
    logger.error("[STATIC] 'frontend/public' NÃO encontrado. Candidatos: %s", candidates)
    static_dir = candidates[0]  # fallback para não quebrar o mount

logger.info("[STATIC] /static -> %s", static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Config pages
@app.get("/admin/config-email")
def config_email_page():
    # Sempre aponta para o HTML dentro do /static
    return RedirectResponse(url="/static/config_email/config_email.html")

# Raiz -> SPA/landing do frontend
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")


# --- Middlewares simples de cache opcional (ex.: desabilitar cache em algumas pastas estáticas) ---
@app.middleware("http")
async def static_no_cache(request: Request, call_next):
    resp = await call_next(request)
    path = request.url.path
    no_cache_roots = ("/static/tabela_preco/", "/static/config_email/")
    if any(path.startswith(r) for r in no_cache_roots) and path.endswith((".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".webp")):
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    return resp


# --- Routers (mantenha como no seu projeto) ---


app.include_router(router_meta)
app.include_router(router_tabela)
app.include_router(pedido_preview.router)
app.include_router(link_pedido.router)
app.include_router(admin_config_email.router)
app.include_router(cliente.router)
app.include_router(listas.router)
app.include_router(fiscal.router)
app.include_router(pedidos.router)
app.include_router(net_diag.router)
app.include_router(produto.router)


# --- CORSMiddleware por fora (último) ---
allow_creds = ALLOWED_ORIGINS != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-cors-debug", "x-error-id"],
    max_age=86400,
)

# # Alternativa: se o subdomínio do Render variar (use UMA OU OUTRA abordagem, não ambas):
# app.add_middleware(
#     CORSMiddleware,
#     allow_origin_regex=r"https://ordersync-[a-z0-9]+\.onrender\.com$",
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["x-cors-debug", "x-error-id"],
#     max_age=86400,
# )