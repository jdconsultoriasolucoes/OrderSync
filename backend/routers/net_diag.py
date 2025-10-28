# routers/net_diag.py
from fastapi import APIRouter, HTTPException, Query
import socket
import ssl
import time

router = APIRouter(prefix="/admin/netdiag", tags=["netdiag"])

# ---------- helpers ----------
def _iter_ipv4(host: str, port: int):
    """Resolve somente IPv4 para evitar problemas de IPv6 sem rota."""
    return socket.getaddrinfo(
        host,
        port,
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )

def _tcp_check_ipv4(host: str, port: int, timeout: float):
    """Tenta conectar por IPv4; em 465 faz handshake TLS. Retorna (ok, tried_ips, last_error)."""
    tried = []
    last_err = None
    try:
        infos = _iter_ipv4(host, port)
    except Exception as e:
        raise HTTPException(502, detail={"error": f"Falha DNS para {host}:{port} - {type(e).__name__}: {e}"})

    for _fam, _type, _proto, _cname, sockaddr in infos:
        ip = sockaddr[0]
        tried.append(ip)
        try:
            sock = socket.create_connection((ip, port), timeout=timeout)
            if port == 465:
                # valida handshake TLS (SNI com hostname)
                ctx = ssl.create_default_context()
                with ctx.wrap_socket(sock, server_hostname=host) as _:
                    pass
            else:
                sock.close()
            return True, tried, None
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
    return False, tried, last_err

# ---------- endpoints ----------
@router.get("/netcheck")
def netcheck(
    host: str = Query(..., description="Ex.: smtp.gmail.com"),
    port: int = Query(..., description="Ex.: 587 / 465 / 2525 / 25"),
    timeout: float = Query(10.0, description="Timeout (s) por tentativa"),
):
    """
    Testa do SERVIDOR (Render) -> host:port (IPv4).
    Para 465, valida handshake TLS. Não faz login SMTP.
    """
    t0 = time.time()
    ok, tried, last_err = _tcp_check_ipv4(host, port, timeout)
    dt = round((time.time() - t0) * 1000)

    if ok:
        return {"host": host, "port": port, "family": "IPv4", "latency_ms": dt, "tried": tried, "status": "open"}

    detail = {"host": host, "port": port, "family": "IPv4", "latency_ms": dt, "tried": tried}
    if last_err and "timed out" in last_err.lower():
        detail["error"] = "Timeout (porta provavelmente bloqueada/filtrada no provedor)"
        raise HTTPException(504, detail=detail)
    if last_err and "Network is unreachable" in last_err:
        detail["error"] = "Network unreachable (bloqueio de egress ou IPv6 sem rota)"
        raise HTTPException(504, detail=detail)
    detail["error"] = last_err or "Falha desconhecida"
    raise HTTPException(502, detail=detail)


@router.get("/netmatrix")
def netmatrix(timeout: float = Query(8.0, description="Timeout (s) por tentativa")):
    """
    Matriz de testes em provedores/portas comuns.
    Útil para ver rapidamente o que está aberto/fechado.
    """
    targets = [
        # Gmail
        ("smtp.gmail.com", 587, "Gmail STARTTLS"),
        ("smtp.gmail.com", 465, "Gmail SSL"),
        # Microsoft 365
        ("smtp.office365.com", 587, "MS365 STARTTLS"),
        ("outlook.office365.com", 587, "Outlook STARTTLS"),
        # Provedores com 2525
        ("smtp.sendgrid.net", 587, "SendGrid 587"),
        ("smtp.sendgrid.net", 465, "SendGrid 465"),
        ("smtp.sendgrid.net", 2525, "SendGrid 2525"),
        ("in-v3.mailjet.com", 587, "Mailjet 587"),
        ("in-v3.mailjet.com", 465, "Mailjet 465"),
        ("in-v3.mailjet.com", 2525, "Mailjet 2525"),
        ("smtp.elasticemail.com", 2525, "ElasticEmail 2525"),
    ]
    results = []
    for host, port, label in targets:
        t0 = time.time()
        try:
            ok, tried, err = _tcp_check_ipv4(host, port, timeout)
            status = "open" if ok else "blocked/timeout"
        except HTTPException as he:
            status = "dns_error"
            tried = []
            err = he.detail
        dt = round((time.time() - t0) * 1000)
        results.append({
            "label": label,
            "host": host,
            "port": port,
            "status": status,
            "latency_ms": dt,
            "tried": tried,
            "error": err,
        })
    return {"timeout_s": timeout, "results": results}


@router.get("/diag")
def diag():
    """Resumo rápido para screenshot/report."""
    quick = [
        ("smtp.gmail.com", 587, "Gmail 587"),
        ("smtp.gmail.com", 465, "Gmail 465"),
        ("smtp.office365.com", 587, "MS365 587"),
        ("smtp.sendgrid.net", 2525, "SendGrid 2525"),
    ]
    out = []
    for host, port, label in quick:
        try:
            ok, tried, err = _tcp_check_ipv4(host, port, timeout=6.0)
            out.append({
                "label": label,
                "target": f"{host}:{port}",
                "status": "open" if ok else "blocked",
                "tried": tried,
                "last_error": err
            })
        except HTTPException as he:
            out.append({"label": label, "target": f"{host}:{port}", "status": "dns_error", "last_error": he.detail})
    return {"diag": out}
