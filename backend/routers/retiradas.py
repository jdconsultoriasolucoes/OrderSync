from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from datetime import datetime

from database import get_db
from models.retiradas import RetiradaModel, RetiradaPedidoModel
from schemas.retiradas import (
    RetiradaCreate, RetiradaResponse,
    RetiradaPedidoCreate, RetiradaPedidoResponse,
    RetiradaPedidoDetailUpdate, RetiradaBase
)

router = APIRouter(
    prefix="/api/retiradas",
    tags=["retiradas"],
    responses={404: {"description": "Not found"}},
)

@router.post("", response_model=RetiradaResponse, status_code=status.HTTP_201_CREATED)
def create_retirada(retirada: RetiradaCreate, db: Session = Depends(get_db)):
    # Valida se já existe retirada com este número
    if retirada.numero_retirada:
        db_ret = db.query(RetiradaModel).filter(RetiradaModel.numero_retirada == retirada.numero_retirada).first()
        if db_ret:
            raise HTTPException(status_code=400, detail="Número de retirada já existe")

    # Calcula próximo número sequencial se não for fornecido
    num_ret = retirada.numero_retirada
    if not num_ret:
        last_ret = db.execute(text("""
            SELECT numero_retirada FROM tb_retiradas 
            WHERE numero_retirada ~ '^[0-9]+$' 
            ORDER BY CAST(numero_retirada AS INTEGER) DESC 
            LIMIT 1
        """)).fetchone()
        
        proximo = 1
        if last_ret and last_ret[0]:
            proximo = int(last_ret[0]) + 1
        num_ret = str(proximo)

    db_ret = RetiradaModel(
        nome_retirada=retirada.nome_retirada,
        numero_retirada=num_ret,
        data_retirada=retirada.data_retirada
    )
    db.add(db_ret)
    db.commit()
    db.refresh(db_ret)

    if retirada.pedidos:
        for p in retirada.pedidos:
            item = RetiradaPedidoModel(
                id_retirada=db_ret.id,
                numero_pedido=p.numero_pedido,
                observacoes=p.observacoes,
                retirada_tipo=p.retirada_tipo,
                retirada_nome_terceiro=p.retirada_nome_terceiro,
                retirada_veiculo_modelo=p.retirada_veiculo_modelo,
                retirada_veiculo_placa=p.retirada_veiculo_placa,
                retirada_horario=p.retirada_horario
            )
            db.add(item)
        db.commit()
        db.refresh(db_ret)

    return db_ret

@router.get("", response_model=List[RetiradaResponse])
def list_retiradas_ativas(db: Session = Depends(get_db)):
    hoje = datetime.now().date()
    retiradas = db.query(RetiradaModel).all()
    
    # Atualiza is_historico dinamicamente para retiradas passadas
    updated = False
    for r in retiradas:
        if r.data_retirada and r.data_retirada.date() < hoje and not r.is_historico:
            r.is_historico = True
            updated = True
    if updated:
        db.commit()
        
    return [r for r in retiradas if not r.is_historico]

@router.get("/historico", response_model=List[RetiradaResponse])
def list_retiradas_historico(db: Session = Depends(get_db)):
    hoje = datetime.now().date()
    retiradas = db.query(RetiradaModel).all()
    
    updated = False
    for r in retiradas:
        if r.data_retirada and r.data_retirada.date() < hoje and not r.is_historico:
            r.is_historico = True
            updated = True
    if updated:
        db.commit()
        
    return [r for r in retiradas if r.is_historico]

@router.get("/{id}", response_model=RetiradaResponse)
def get_retirada(id: int, db: Session = Depends(get_db)):
    db_ret = db.query(RetiradaModel).filter(RetiradaModel.id == id).first()
    if not db_ret:
        raise HTTPException(status_code=404, detail="Retirada não encontrada")
    return db_ret

@router.put("/{id}", response_model=RetiradaResponse)
def update_retirada(id: int, upd: RetiradaBase, db: Session = Depends(get_db)):
    db_ret = db.query(RetiradaModel).filter(RetiradaModel.id == id).first()
    if not db_ret:
        raise HTTPException(status_code=404, detail="Retirada não encontrada")
        
    if upd.nome_retirada is not None: db_ret.nome_retirada = upd.nome_retirada
    if upd.numero_retirada is not None: db_ret.numero_retirada = upd.numero_retirada
    if upd.data_retirada is not None: db_ret.data_retirada = upd.data_retirada
    
    db_ret.data_update = datetime.utcnow()
    db.commit()
    db.refresh(db_ret)
    return db_ret

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_retirada(id: int, db: Session = Depends(get_db)):
    db_ret = db.query(RetiradaModel).filter(RetiradaModel.id == id).first()
    if not db_ret:
        raise HTTPException(status_code=404, detail="Retirada não encontrada")
    db.delete(db_ret)
    db.commit()
    return None

@router.post("/{id}/pedidos", response_model=RetiradaPedidoResponse)
def add_pedido_retirada(id: int, p: RetiradaPedidoCreate, db: Session = Depends(get_db)):
    db_ret = db.query(RetiradaModel).filter(RetiradaModel.id == id).first()
    if not db_ret:
        raise HTTPException(status_code=404, detail="Retirada não encontrada")
        
    item = RetiradaPedidoModel(
        id_retirada=id,
        numero_pedido=p.numero_pedido,
        observacoes=p.observacoes,
        retirada_tipo=p.retirada_tipo,
        retirada_nome_terceiro=p.retirada_nome_terceiro,
        retirada_veiculo_modelo=p.retirada_veiculo_modelo,
        retirada_veiculo_placa=p.retirada_veiculo_placa,
        retirada_horario=p.retirada_horario
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/pedidos/{id_pedido_retirada}", status_code=status.HTTP_204_NO_CONTENT)
def remove_pedido_retirada(id_pedido_retirada: int, db: Session = Depends(get_db)):
    item = db.query(RetiradaPedidoModel).filter(RetiradaPedidoModel.id == id_pedido_retirada).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item de retirada não encontrado")
    db.delete(item)
    db.commit()
    return None

@router.put("/pedidos/{id_pedido_retirada}", response_model=RetiradaPedidoResponse)
def update_pedido_retirada(id_pedido_retirada: int, upd: RetiradaPedidoDetailUpdate, db: Session = Depends(get_db)):
    item = db.query(RetiradaPedidoModel).filter(RetiradaPedidoModel.id == id_pedido_retirada).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item de retirada não encontrado")
        
    if upd.retirada_tipo is not None: item.retirada_tipo = upd.retirada_tipo
    if upd.retirada_nome_terceiro is not None: item.retirada_nome_terceiro = upd.retirada_nome_terceiro
    if upd.retirada_veiculo_modelo is not None: item.retirada_veiculo_modelo = upd.retirada_veiculo_modelo
    if upd.retirada_veiculo_placa is not None: item.retirada_veiculo_placa = upd.retirada_veiculo_placa
    if upd.retirada_horario is not None: item.retirada_horario = upd.retirada_horario
    if upd.observacoes is not None: item.observacoes = upd.observacoes
    
    db.commit()
    db.refresh(item)
    return item

@router.get("/{id}/pedidos-detalhes")
def get_retirada_pedidos_detalhes(id: int, db: Session = Depends(get_db)):
    db_ret = db.query(RetiradaModel).filter(RetiradaModel.id == id).first()
    if not db_ret:
        raise HTTPException(status_code=404, detail="Retirada não encontrada")
        
    sql = text("""
        SELECT 
            rp.id AS id_carga_pedido,
            rp.numero_pedido,
            NULL AS ordem_carregamento,
            p.id_pedido,
            p.codigo_cliente,
            COALESCE(c.cadastro_nome_cliente, p.cliente) AS cliente_nome,
            c.cadastro_nome_fantasia as nome_fantasia,
            p.status,
            p.fornecedor,
            'RETIRADA' as modalidade,
            CAST(COALESCE(p.peso_total_kg, 0) AS FLOAT) AS peso_total,
            CAST(COALESCE(pb.peso_bruto_total, p.peso_total_kg) AS FLOAT) AS peso_bruto_total,
            c.entrega_municipio AS municipio,
            c.entrega_rota_principal AS rota_principal,
            c.entrega_rota_aproximacao AS rota_aproximacao,
            rp.observacoes,
            rp.retirada_tipo,
            rp.retirada_nome_terceiro,
            rp.retirada_veiculo_modelo,
            rp.retirada_veiculo_placa,
            rp.retirada_horario
        FROM tb_retiradas_pedidos rp
        JOIN tb_pedidos p ON rp.numero_pedido = p.id_pedido::text
        LEFT JOIN (
             SELECT 
                 id_pedido,
                 SUM(i.quantidade * COALESCE(prod.peso_bruto, prod.peso, 0)) as peso_bruto_total
             FROM tb_pedidos_itens i
             LEFT JOIN (
                 SELECT codigo_supra, MAX(CAST(peso AS FLOAT)) as peso, MAX(CAST(peso_bruto AS FLOAT)) as peso_bruto 
                 FROM t_cadastro_produto_v2 GROUP BY codigo_supra
             ) prod ON prod.codigo_supra = i.codigo
             GROUP BY id_pedido
        ) pb ON pb.id_pedido = p.id_pedido
        LEFT JOIN t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        WHERE rp.id_retirada = :ret_id
        ORDER BY rp.id ASC
    """)
    
    rows = db.execute(sql, {"ret_id": id}).mappings().all()
    lista_final = [dict(r) for r in rows]
    
    ids_vinculados = {str(r["id_pedido"]) for r in lista_final}
    data_ref = db_ret.data_retirada.date() if db_ret.data_retirada else None
    
    if data_ref:
        sql_sugeridos = text("""
            SELECT 
                NULL AS id_carga_pedido,
                p.id_pedido::text AS numero_pedido,
                NULL AS ordem_carregamento,
                p.id_pedido,
                p.codigo_cliente,
                COALESCE(c.cadastro_nome_cliente, p.cliente) AS cliente_nome,
                c.cadastro_nome_fantasia as nome_fantasia,
                p.status,
                p.fornecedor,
                'RETIRADA' as modalidade,
                CAST(COALESCE(p.peso_total_kg, 0) AS FLOAT) AS peso_total,
                CAST(COALESCE(pb.peso_bruto_total, p.peso_total_kg) AS FLOAT) AS peso_bruto_total,
                c.entrega_municipio AS municipio,
                c.entrega_rota_principal AS rota_principal,
                c.entrega_rota_aproximacao AS rota_aproximacao,
                NULL AS observacoes,
                NULL AS retirada_tipo,
                NULL AS retirada_nome_terceiro,
                NULL AS retirada_veiculo_modelo,
                NULL AS retirada_veiculo_placa,
                NULL AS retirada_horario
            FROM tb_pedidos p
            LEFT JOIN (
                 SELECT 
                     id_pedido,
                     SUM(i.quantidade * COALESCE(prod.peso_bruto, prod.peso, 0)) as peso_bruto_total
                 FROM tb_pedidos_itens i
                 LEFT JOIN (
                     SELECT codigo_supra, MAX(CAST(peso AS FLOAT)) as peso, MAX(CAST(peso_bruto AS FLOAT)) as peso_bruto 
                     FROM t_cadastro_produto_v2 GROUP BY codigo_supra
                 ) prod ON prod.codigo_supra = i.codigo
                 GROUP BY id_pedido
            ) pb ON pb.id_pedido = p.id_pedido
            LEFT JOIN t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
            WHERE (p.usar_valor_com_frete = FALSE OR p.usar_valor_com_frete IS NULL)
              AND p.status NOT IN ('FATURADO', 'CANCELADO')
              AND p.created_at::date = :data_ref
              AND NOT EXISTS (
                  SELECT 1 FROM tb_retiradas_pedidos xrp
                  WHERE xrp.numero_pedido = p.id_pedido::text
              )
        """)
        
        rows_sugeridos = db.execute(sql_sugeridos, {"data_ref": data_ref}).mappings().all()
        for r in rows_sugeridos:
            if str(r["id_pedido"]) not in ids_vinculados:
                lista_final.append(dict(r))
                
    return lista_final


# ------------- PDF EXPORT ENDPOINTS -------------

from fastapi.responses import Response
from services import relatorios_pdf_service

@router.get("/romaneio/{retirada_id}/pdf")
def download_romaneio_retirada_pdf(retirada_id: int, db: Session = Depends(get_db)):
    pdf_content = relatorios_pdf_service.gerar_pdf_romaneio_retirada(db, retirada_id)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Lote de retirada não encontrado")
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=romaneio_retirada_{retirada_id}.pdf"}
    )

@router.get("/resumo-produtos/{retirada_id}/pdf")
def download_resumo_produtos_retirada_pdf(retirada_id: int, db: Session = Depends(get_db)):
    pdf_content = relatorios_pdf_service.gerar_pdf_resumo_produtos_retirada(db, retirada_id)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Lote de retirada não encontrado")
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=resumo_produtos_retirada_{retirada_id}.pdf"}
    )

@router.get("/romaneio-lote/pdf")
def download_romaneio_retirada_lote_pdf(ids: str, db: Session = Depends(get_db)):
    id_list = [int(i.strip()) for i in ids.split(',') if i.strip().isdigit()]
    pdf_content = relatorios_pdf_service.gerar_pdf_romaneio_retirada_lote(db, id_list)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Nenhuma retirada encontrada")
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=romaneio_retiradas_lote.pdf"}
    )

@router.get("/resumo-lote/pdf")
def download_resumo_retirada_lote_pdf(ids: str, db: Session = Depends(get_db)):
    id_list = [int(i.strip()) for i in ids.split(',') if i.strip().isdigit()]
    pdf_content = relatorios_pdf_service.gerar_pdf_resumo_produtos_retirada_lote(db, id_list)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Nenhuma retirada encontrada")
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=resumo_retiradas_lote.pdf"}
    )


