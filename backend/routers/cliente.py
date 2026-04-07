from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List
import io
import logging
from schemas.cliente import ClienteCompleto, ClienteResumo
from services.cliente import (
    listar_clientes,
    obter_cliente,
    criar_cliente,
    atualizar_cliente,
    deletar_cliente
)
from core.deps import get_current_user
from models.usuario import UsuarioModel
from models.cliente_v2 import ClienteModelV2
from database import SessionLocal
from sqlalchemy import text

# Configuração de logger para o router
logger = logging.getLogger("ordersync.routers.cliente")

router = APIRouter()

@router.get("/", response_model=List[ClienteCompleto])
def get_clientes():
    return listar_clientes()

@router.get("/{codigo_da_empresa}/ultimas_compras")
def get_ultimas_compras(codigo_da_empresa: str):
    """Retorna as últimas 3 compras (pedidos) de um cliente, incluindo cancelados."""
    try:
        with SessionLocal() as db:
            rows = db.execute(text("""
                SELECT
                    a.id_pedido,
                    a.created_at,
                    a.total_pedido,
                    a.frete_total,
                    a.status,
                    COALESCE(a.tabela_preco_nome, b.nome_tabela) AS tabela_preco_nome
                FROM public.tb_pedidos a
                LEFT JOIN public.tb_tabela_preco b ON a.tabela_preco_id = b.id_tabela
                WHERE a.codigo_cliente = :codigo
                ORDER BY a.created_at DESC
                LIMIT 3
            """), {"codigo": codigo_da_empresa}).mappings().all()
        return [
            {
                "id_pedido": r["id_pedido"],
                "data": r["created_at"].strftime("%d/%m/%Y") if r["created_at"] else "-",
                "tabela_preco_nome": r["tabela_preco_nome"] or "-",
                "total_pedido": float(r["total_pedido"] or 0),
                "frete_total": float(r["frete_total"] or 0),
                "status": r["status"] or "-",
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar compras: {e}")

@router.get("/{codigo_da_empresa}/tabelas_preco")
def get_tabelas_preco_cliente(codigo_da_empresa: str):
    """Retorna as tabelas de preço ativas vinculadas ao codigo_cliente."""
    try:
        with SessionLocal() as db:
            rows = db.execute(text("""
                SELECT DISTINCT id_tabela, nome_tabela
                FROM tb_tabela_preco
                WHERE codigo_cliente = :codigo
                  AND ativo IS TRUE
                ORDER BY nome_tabela
            """), {"codigo": codigo_da_empresa}).mappings().all()
        return [
            {"id_tabela": r["id_tabela"], "nome_tabela": r["nome_tabela"]}
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar tabelas: {e}")

@router.get("/{id}/exportar-supra")
def exportar_supra(
    id: int,
    format: str = "pdf",
    current_user: UsuarioModel = Depends(get_current_user)
):
    """
    Exporta a Ficha de Cadastro Alisul/Supra para .xlsx ou .pdf.
    Implementação robusta com tratamento de erros centralizado.
    """
    try:
        with SessionLocal() as db:
            cli = db.query(ClienteModelV2).filter(
                ClienteModelV2.id == id
            ).first()
        
        if not cli:
            logger.warning(f"Tentativa de exportação Supra para cliente inexistente ID: {id}")
            raise HTTPException(status_code=404, detail="Cliente não encontrado no banco de dados.")

        codigo = cli.cadastro_codigo_da_empresa or "S_COD"
        nome_arquivo = f"ficha_supra_{codigo}"

        if format.lower() == "xlsx":
            from services.excel_supra_service import gerar_excel_cliente_supra
            conteudo = gerar_excel_cliente_supra(cli)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
        else:
            from services.pdf_supra_service import gerar_pdf_cliente_supra
            conteudo = gerar_pdf_cliente_supra(cli)
            media_type = "application/pdf"
            ext = "pdf"

        headers = {
            "Content-Disposition": f'attachment; filename="{nome_arquivo}.{ext}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
        
        return StreamingResponse(io.BytesIO(conteudo), media_type=media_type, headers=headers)

    except FileNotFoundError as e:
        logger.error(f"Erro de infraestrutura na exportação (ARQUIVO AUSENTE): {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Erro técnico na geração da exportação Supra: {e}")
        raise HTTPException(status_code=500, detail="Erro técnico ao gerar o arquivo. Contate o suporte.")
    except Exception as e:
        logger.critical(f"Erro inesperado na exportação Supra: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno inesperado no servidor.")


@router.get("/lookup")
def lookup_cliente(query: str):
    """Retorna clientes para o componente de Lookup."""
    try:
        with SessionLocal() as db:
            # Busca clientes ativos e inativos
            rows = db.execute(text("""
                SELECT id, cadastro_codigo_da_empresa, cadastro_nome_cliente, cadastro_nome_fantasia
                FROM public.t_cadastro_cliente_v2
                WHERE cadastro_nome_cliente ILIKE :q
                   OR cadastro_nome_fantasia ILIKE :q
                   OR cadastro_codigo_da_empresa ILIKE :q
                LIMIT 20
            """), {"q": f"%{query}%"}).mappings().all()
        return [{"codigo": r["cadastro_codigo_da_empresa"], "nome_empresarial": r["cadastro_nome_cliente"], "nome_fantasia": r["cadastro_nome_fantasia"]} for r in rows]
    except Exception as e:
        logger.error(f"Erro no lookup de cliente: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar clientes")

@router.get("/{codigo_da_empresa}", response_model=ClienteCompleto)
def get_cliente(codigo_da_empresa: str):
    cliente = obter_cliente(codigo_da_empresa)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente

@router.delete("/{codigo_da_empresa}", response_model=dict)
def delete_cliente(codigo_da_empresa: str, current_user: UsuarioModel = Depends(get_current_user)):
    success = deletar_cliente(codigo_da_empresa)
    if not success:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return {"message": "Cliente removido com sucesso"}

@router.post("/", response_model=ClienteCompleto)
def post_cliente(cliente: ClienteCompleto, current_user: UsuarioModel = Depends(get_current_user)):
    data = cliente.model_dump()
    data["criado_por"] = current_user.email
    data["atualizado_por"] = current_user.email
    return criar_cliente(data)

@router.put("/{codigo_da_empresa}", response_model=ClienteCompleto)
def put_cliente(codigo_da_empresa: str, cliente: ClienteCompleto, current_user: UsuarioModel = Depends(get_current_user)):
    data = cliente.model_dump()
    data["atualizado_por"] = current_user.email
    atualizado = atualizar_cliente(codigo_da_empresa, data)
    if not atualizado:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return atualizado
