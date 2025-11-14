from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from database import SessionLocal
from models.pedido_pdf import PedidoPdf
from services.pedido_pdf_data import carregar_pedido_pdf
from services.pdf_service import gerar_pdf_pedido
import os

router = APIRouter(prefix="/pedido", tags=["Pedido PDF"])

@router.get("/{pedido_id}/dados_pdf", response_model=PedidoPdf)
def get_dados_pdf(pedido_id: int):
    with SessionLocal() as db:
        try:
            pedido_pdf = carregar_pedido_pdf(db, pedido_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        return pedido_pdf


@router.get("/{pedido_id}/pdf")
def gerar_pdf_pedido_endpoint(pedido_id: int):
    with SessionLocal() as db:
        try:
            pedido_pdf = carregar_pedido_pdf(db, pedido_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")

        path = gerar_pdf_pedido(pedido_pdf)

        filename = os.path.basename(path)
        return StreamingResponse(
            open(path, "rb"),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename=\"{filename}\"'}
        )
