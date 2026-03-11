from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from database import get_db
from models.cargas import CargaModel, CargaPedidoModel
from models.pedido import PedidoModel
from models.transporte import TransporteModel
from schemas.cargas import CargaCreate, CargaUpdate, CargaResponse, CargaPedidoCreate, CargaPedidoDetailUpdate

router = APIRouter(
    prefix="/api/relatorios",
    tags=["Relatorios e Cargas"],
    responses={404: {"description": "Not found"}},
)

# ----------------- GERENCIAMENTO DE CARGAS (CABEÇALHOS) -----------------

@router.post("/cargas", response_model=CargaResponse, status_code=status.HTTP_201_CREATED)
def create_carga(carga: CargaCreate, db: Session = Depends(get_db)):
    # Verifica se já existe carga com este número (se não estiver em branco)
    if carga.numero_carga:
        db_carga = db.query(CargaModel).filter(CargaModel.numero_carga == carga.numero_carga).first()
        if db_carga:
            raise HTTPException(status_code=400, detail="Número de carga já existe")

    # Criação do Cabeçalho
    new_carga = CargaModel(
        nome_carga=carga.nome_carga,
        numero_carga=carga.numero_carga,
        id_transporte=carga.id_transporte,
        data_carregamento=carga.data_carregamento
    )
    db.add(new_carga)
    db.commit()
    db.refresh(new_carga)

    # Inserção de itens (Pedidos vinculados à carga)
    if carga.pedidos:
        for p in carga.pedidos:
            item = CargaPedidoModel(
                id_carga=new_carga.id,
                numero_pedido=p.numero_pedido,
                ordem_carregamento=p.ordem_carregamento,
                observacoes=p.observacoes
            )
            db.add(item)
        db.commit()

    db.refresh(new_carga)
    return new_carga

@router.get("/cargas", response_model=List[CargaResponse])
def read_cargas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cargas = db.query(CargaModel).offset(skip).limit(limit).all()
    return cargas

@router.get("/cargas/{carga_id}", response_model=CargaResponse)
def read_carga(carga_id: int, db: Session = Depends(get_db)):
    carga = db.query(CargaModel).filter(CargaModel.id == carga_id).first()
    if carga is None:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    return carga

@router.put("/cargas/{carga_id}", response_model=CargaResponse)
def update_carga(carga_id: int, carga: CargaUpdate, db: Session = Depends(get_db)):
    db_carga = db.query(CargaModel).filter(CargaModel.id == carga_id).first()
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    
    update_data = carga.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_carga, key, value)
        
    db.commit()
    db.refresh(db_carga)
    return db_carga

@router.delete("/cargas/{carga_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_carga(carga_id: int, db: Session = Depends(get_db)):
    db_carga = db.query(CargaModel).filter(CargaModel.id == carga_id).first()
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    
    db.delete(db_carga)
    db.commit()
    return None

# ------------- INTEGRAÇÕES PARA FRONT-END (ROMANEIO E PRODUTOS) -------------

@router.post("/cargas/{carga_id}/pedidos")
def add_pedido_to_carga(carga_id: int, pedido: CargaPedidoCreate, db: Session = Depends(get_db)):
    db_carga = db.query(CargaModel).filter(CargaModel.id == carga_id).first()
    if not db_carga:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    
    # Prevenção de duplicidade
    existente = db.query(CargaPedidoModel).filter(
        CargaPedidoModel.id_carga == carga_id,
        CargaPedidoModel.numero_pedido == pedido.numero_pedido
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"O pedido {pedido.numero_pedido} já está nesta carga.")

    db_item = CargaPedidoModel(
        id_carga=carga_id,
        numero_pedido=pedido.numero_pedido,
        ordem_carregamento=pedido.ordem_carregamento,
        observacoes=pedido.observacoes
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"status": "success", "id_carga_pedido": db_item.id}

@router.put("/cargas/pedidos/{item_id}")
def update_carga_pedido(item_id: int, item_data: CargaPedidoDetailUpdate, db: Session = Depends(get_db)):
    db_item = db.query(CargaPedidoModel).filter(CargaPedidoModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item de carga não encontrado")
    
    update_data = item_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    db.commit()
    return {"status": "success"}

@router.delete("/cargas/pedidos/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_pedido_from_carga(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(CargaPedidoModel).filter(CargaPedidoModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item de carga não encontrado")
    
    db.delete(db_item)
    db.commit()
    return None

@router.get("/cargas/{carga_id}/resumo-produtos")
def get_resumo_produtos_carga(carga_id: int, db: Session = Depends(get_db)):
    """
    Retorna o agrupamento (SUM) de todos os itens referentes aos pedidos
    que estão vinculados nesta Carga específica.
    """
    from sqlalchemy import text
    
    # Valida carga existe
    db_carga = db.query(CargaModel).filter(CargaModel.id == carga_id).first()
    if not db_carga:
        raise HTTPException(status_code=404, detail="Carga não encontrada")

    # SQL de agregação: Pega a carga M-N, cruza com tb_pedidos e tb_pedidos_itens, soma QTD e agrupa
    sql = text("""
        SELECT 
            i.codigo,
            i.nome AS descricao,
            MAX(i.embalagem) AS embalagem,
            SUM(i.quantidade) AS qtd_total,
            MAX(prod.unidade_medida) AS unidade,
            MAX(CAST(prod.peso AS FLOAT)) AS peso_unitario,
            CAST(SUM(i.quantidade * COALESCE(prod.peso, 0)) AS FLOAT) AS peso_liquido_total
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        JOIN tb_pedidos_itens i ON p.id_pedido = i.id_pedido
        LEFT JOIN (
            SELECT codigo_supra, MAX(CAST(peso AS FLOAT)) as peso, MAX(unidade) as unidade_medida
            FROM t_cadastro_produto_v2
            GROUP BY codigo_supra
        ) prod ON prod.codigo_supra = i.codigo
        WHERE cp.id_carga = :carga_id AND i.quantidade > 0
        GROUP BY i.codigo, i.nome
        ORDER BY peso_liquido_total DESC
    """)
    
    rows = db.execute(sql, {"carga_id": carga_id}).mappings().all()
    
    return [dict(r) for r in rows]

@router.get("/cargas/{carga_id}/pedidos-detalhes")
def get_carga_pedidos_detalhes(carga_id: int, db: Session = Depends(get_db)):
    """
    Retorna a lista detalhada de pedidos vinculados a uma Carga, 
    buscando dados da tabela de pedidos e clientes para exibição.
    """
    from sqlalchemy import text
    
    # Valida carga existe
    db_carga = db.query(CargaModel).filter(CargaModel.id == carga_id).first()
    if not db_carga:
        raise HTTPException(status_code=404, detail="Carga não encontrada")

    sql = text("""
        SELECT 
            cp.id AS id_carga_pedido,
            cp.numero_pedido,
            cp.ordem_carregamento,
            p.codigo_cliente,
            p.cliente AS cliente_nome,
            c.cadastro_nome_fantasia as nome_fantasia,
            p.status,
            p.fornecedor,
            CASE WHEN p.usar_valor_com_frete THEN 'ENTREGA' ELSE 'RETIRADA' END as modalidade,
            CAST(COALESCE(p.peso_total_kg, 0) AS FLOAT) AS peso_total,
            c.entrega_municipio AS municipio,
            c.entrega_rota_principal AS rota_principal,
            c.entrega_rota_aproximacao AS rota_aproximacao,
            cp.observacoes
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        LEFT JOIN t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        WHERE cp.id_carga = :carga_id
        ORDER BY cp.ordem_carregamento ASC NULLS LAST, cp.id ASC
    """)
    
    rows = db.execute(sql, {"carga_id": carga_id}).mappings().all()
    
    return [dict(r) for r in rows]

# ------------- PDF EXPORT ENDPOINTS -------------

from fastapi.responses import Response
from services import relatorios_pdf_service

@router.get("/carga/{carga_id}/pdf")
def download_formacao_carga_pdf(carga_id: int, db: Session = Depends(get_db)):
    pdf_content = relatorios_pdf_service.gerar_pdf_formacao_carga(db, carga_id)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=formacao_carga_{carga_id}.pdf"}
    )

@router.get("/romaneio/{carga_id}/pdf")
def download_romaneio_pdf(carga_id: int, db: Session = Depends(get_db)):
    pdf_content = relatorios_pdf_service.gerar_pdf_romaneio(db, carga_id)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=romaneio_{carga_id}.pdf"}
    )

@router.get("/resumo-produtos/{carga_id}/pdf")
def download_resumo_produtos_pdf(carga_id: int, db: Session = Depends(get_db)):
    pdf_content = relatorios_pdf_service.gerar_pdf_resumo_produtos(db, carga_id)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=resumo_produtos_{carga_id}.pdf"}
    )

@router.get("/relatorio-completo/{carga_id}/pdf")
def download_relatorio_completo_pdf(carga_id: int, db: Session = Depends(get_db)):
    pdf_content = relatorios_pdf_service.gerar_pdf_relatorio_completo(db, carga_id)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=relatorio_completo_{carga_id}.pdf"}
    )

