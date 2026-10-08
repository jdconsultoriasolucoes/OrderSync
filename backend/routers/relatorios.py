from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional
from datetime import datetime, timedelta, date
import re
from database import get_db
from models.cargas import CargaModel, CargaPedidoModel
from models.pedido import PedidoModel
from models.transporte import TransporteModel
from schemas.cargas import CargaCreate, CargaUpdate, CargaResponse, CargaPedidoCreate, CargaPedidoDetailUpdate
from core.deps import get_current_user
from models.usuario import UsuarioModel
from services.auditoria_service import gerar_snapshot_carga

router = APIRouter(
    prefix="/api/relatorios",
    tags=["Relatorios e Cargas"],
    responses={404: {"description": "Not found"}},
)

# ----------------- GERENCIAMENTO DE CARGAS (CABEÇALHOS) -----------------

@router.post("/cargas", response_model=CargaResponse, status_code=status.HTTP_201_CREATED)
def create_carga(carga: CargaCreate, db: Session = Depends(get_db)):
    # Verifica se já existe carga com este número (se informado manualmente)
    num_carga = carga.numero_carga.strip() if (carga.numero_carga and carga.numero_carga.strip()) else None
    if num_carga:
        db_carga = db.query(CargaModel).filter(CargaModel.numero_carga == num_carga).first()
        if db_carga:
            raise HTTPException(status_code=400, detail="Número de carga já existe")

    import uuid
    # Criação do Cabeçalho
    temp_num_carga = False
    if not num_carga:
        num_carga = f"tmp-{uuid.uuid4().hex[:8]}"
        temp_num_carga = True

    new_carga = CargaModel(
        nome_carga=carga.nome_carga,
        numero_carga=num_carga,
        id_transporte=carga.id_transporte,
        data_carregamento=carga.data_carregamento,
        is_retirada=carga.is_retirada,
        tipo_retirada=carga.tipo_retirada,
        retirada_nome_terceiro=carga.retirada_nome_terceiro,
        retirada_veiculo_temporario_placa=carga.retirada_veiculo_temporario_placa,
        retirada_veiculo_temporario_modelo=carga.retirada_veiculo_temporario_modelo
    )
    db.add(new_carga)
    db.flush()  # Aloca o ID da sequence do banco

    # Se numero_carga foi gerado temporariamente, sincroniza igual ao ID gerado
    if temp_num_carga:
        if new_carga.is_retirada:
            new_carga.numero_carga = f"R{new_carga.id}"
        else:
            new_carga.numero_carga = str(new_carga.id)

    # Se nome_carga não foi informado, utiliza o numero_carga como identificador padrão
    if not new_carga.nome_carga:
        new_carga.nome_carga = new_carga.numero_carga

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
    cargas = db.query(CargaModel).filter(
        ((CargaModel.is_historico == False) | (CargaModel.is_historico == None)) &
        ((CargaModel.is_retirada == False) | (CargaModel.is_retirada == None))
    ).order_by(CargaModel.id.desc()).offset(skip).limit(limit).all()
    return cargas

@router.get("/cargas/historico", response_model=List[CargaResponse])
def read_cargas_historico(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cargas = db.query(CargaModel).filter(
        (CargaModel.is_historico == True) &
        ((CargaModel.is_retirada == False) | (CargaModel.is_retirada == None))
    ).order_by(CargaModel.data_faturamento.desc()).offset(skip).limit(limit).all()
    return cargas

@router.get("/retiradas", response_model=List[CargaResponse])
def read_retiradas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    from datetime import date
    hoje = date.today()
    retiradas = db.query(CargaModel).filter(
        ((CargaModel.is_historico == False) | (CargaModel.is_historico == None)) &
        (CargaModel.is_retirada == True) &
        ((CargaModel.data_carregamento >= hoje) | (CargaModel.data_carregamento == None))
    ).order_by(CargaModel.id.desc()).offset(skip).limit(limit).all()
    return retiradas

@router.get("/retiradas/historico", response_model=List[CargaResponse])
def read_retiradas_historico(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    from datetime import date
    hoje = date.today()
    retiradas = db.query(CargaModel).filter(
        (CargaModel.is_retirada == True) &
        (
            (CargaModel.is_historico == True) |
            (CargaModel.data_carregamento < hoje)
        )
    ).order_by(CargaModel.data_carregamento.desc()).offset(skip).limit(limit).all()
    return retiradas

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
    
    # Validação de peso do transporte
    if "id_transporte" in update_data and update_data["id_transporte"]:
        id_transp = update_data["id_transporte"]
        transp = db.query(TransporteModel).filter(TransporteModel.id == id_transp).first()
        if transp and transp.capacidade_kg:
            # Calcula peso bruto total da carga
            q_peso = text("""
                SELECT COALESCE(SUM(i.quantidade * COALESCE(prod.peso_bruto, 0)), 0) as total_peso
                FROM tb_cargas_pedidos cp
                JOIN tb_pedidos_itens i ON cp.numero_pedido = CAST(i.id_pedido AS VARCHAR)
                LEFT JOIN (
                    SELECT codigo_supra, MAX(CAST(peso AS FLOAT)) as peso, MAX(CAST(peso_bruto AS FLOAT)) as peso_bruto 
                    FROM t_cadastro_produto_v2 GROUP BY codigo_supra
                ) prod ON prod.codigo_supra = i.codigo
                WHERE cp.id_carga = :carga_id
            """)
            peso_row = db.execute(q_peso, {"carga_id": carga_id}).mappings().first()
            peso_total = float(peso_row["total_peso"] if peso_row and peso_row["total_peso"] else 0)
            
            if peso_total > transp.capacidade_kg:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Caminhão não comporta o peso BRUTO! Capacidade: {transp.capacidade_kg} kg | Peso Bruto Carga: {peso_total:.2f} kg."
                )

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
    
    # Atualiza status do pedido para "Carga em formação"
    if pedido.numero_pedido.isdigit():
        db_pedido = db.query(PedidoModel).filter(PedidoModel.id == int(pedido.numero_pedido)).first()
        if db_pedido:
            de_status = db_pedido.status
            db_pedido.status = "Carga em formação"
            db_pedido.atualizado_em = datetime.utcnow()
            
            # Insere evento
            try:
                with db.begin_nested():
                    db.execute(text("""
                        INSERT INTO public.pedido_status_event (id, pedido_id, de_status, para_status, user_id, motivo, metadata, created_at)
                        VALUES (gen_random_uuid(), :pedido_id, :de_status, 'Carga em formação', 'sistema', 'Pedido vinculado à Carga', '{}'::jsonb, now())
                    """), {
                        "pedido_id": db_pedido.id,
                        "de_status": de_status
                    })
            except Exception:
                pass

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
    
    # Mudar status do pedido de volta para "Pedido" (se estiver em "Carga em formação")
    num_ped = db_item.numero_pedido
    if num_ped.isdigit():
        db_pedido = db.query(PedidoModel).filter(PedidoModel.id == int(num_ped)).first()
        if db_pedido and db_pedido.status == "Carga em formação":
            db_pedido.status = "Pedido"
            db_pedido.atualizado_em = datetime.utcnow()
            try:
                with db.begin_nested():
                    db.execute(text("""
                        INSERT INTO public.pedido_status_event (id, pedido_id, de_status, para_status, user_id, motivo, metadata, created_at)
                        VALUES (gen_random_uuid(), :pedido_id, 'Carga em formação', 'Pedido', 'sistema', 'Pedido removido da Carga', '{}'::jsonb, now())
                    """), {
                        "pedido_id": db_pedido.id
                    })
            except Exception:
                pass

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
            MAX(COALESCE(prod.estoque_disponivel, 0)) AS estoque_disponivel,
            MAX(COALESCE(prod.estoque_futuro, 0)) AS estoque_futuro,
            MAX(CAST(prod.peso AS FLOAT)) AS peso_unitario,
            MAX(CAST(COALESCE(prod.peso_bruto, 0) AS FLOAT)) AS peso_bruto_unitario,
            CAST(SUM(i.quantidade * COALESCE(prod.peso, 0)) AS FLOAT) AS peso_liquido_total,
            CAST(SUM(i.quantidade * COALESCE(prod.peso_bruto, 0)) AS FLOAT) AS peso_bruto_total
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        JOIN tb_pedidos_itens i ON p.id_pedido = i.id_pedido
        LEFT JOIN (
            SELECT codigo_supra, MAX(CAST(peso AS FLOAT)) as peso, MAX(CAST(peso_bruto AS FLOAT)) as peso_bruto, MAX(unidade) as unidade_medida, MAX(estoque_disponivel) as estoque_disponivel, MAX(estoque_futuro) as estoque_futuro
            FROM t_cadastro_produto_v2
            GROUP BY codigo_supra
        ) prod ON prod.codigo_supra = i.codigo
        WHERE cp.id_carga = :carga_id AND i.quantidade > 0
        GROUP BY i.codigo, i.nome
        HAVING SUM(i.quantidade) > 0
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
            p.id_pedido,
            p.codigo_cliente,
            COALESCE(c.cadastro_nome_cliente, p.cliente) AS cliente_nome,
            c.cadastro_nome_fantasia as nome_fantasia,
            p.status as status_codigo,
            p.fornecedor,
            CASE WHEN p.usar_valor_com_frete THEN 'ENTREGA' ELSE 'RETIRADA' END as modalidade,
            CAST(COALESCE(p.peso_total_kg, 0) AS FLOAT) AS peso_total,
            CAST(COALESCE(pb.peso_bruto_total, 0) AS FLOAT) AS peso_bruto_total,
            c.entrega_municipio AS municipio,
            c.entrega_rota_principal AS rota_principal,
            c.entrega_rota_aproximacao AS rota_aproximacao,
            cp.observacoes,
            cp.retirada_tipo,
            cp.retirada_nome_terceiro,
            cp.retirada_veiculo_modelo,
            cp.retirada_veiculo_placa,
            cp.retirada_horario
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        LEFT JOIN (
             SELECT 
                 id_pedido,
                 SUM(i.quantidade * COALESCE(prod.peso_bruto, 0)) as peso_bruto_total
             FROM tb_pedidos_itens i
             LEFT JOIN (
                 SELECT codigo_supra, MAX(CAST(peso AS FLOAT)) as peso, MAX(CAST(peso_bruto AS FLOAT)) as peso_bruto 
                 FROM t_cadastro_produto_v2 GROUP BY codigo_supra
             ) prod ON prod.codigo_supra = i.codigo
             GROUP BY id_pedido
        ) pb ON pb.id_pedido = p.id_pedido
        LEFT JOIN t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        WHERE cp.id_carga = :carga_id
        ORDER BY cp.ordem_carregamento ASC NULLS LAST, cp.id ASC
    """)
    
    rows = db.execute(sql, {"carga_id": carga_id}).mappings().all()
    lista_final = [dict(r) for r in rows]
    
    if db_carga.is_retirada:
        ids_vinculados = {str(r["id_pedido"]) for r in lista_final}
        data_ref = db_carga.data_carregamento.date() if db_carga.data_carregamento else None
        
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
                    p.status as status_codigo,
                    p.fornecedor,
                    'RETIRADA' as modalidade,
                    CAST(COALESCE(p.peso_total_kg, 0) AS FLOAT) AS peso_total,
                    CAST(COALESCE(pb.peso_bruto_total, 0) AS FLOAT) AS peso_bruto_total,
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
                         SUM(i.quantidade * COALESCE(prod.peso_bruto, 0)) as peso_bruto_total
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
                      SELECT 1 FROM tb_cargas_pedidos xcp
                      JOIN tb_cargas xc ON xcp.id_carga = xc.id
                      WHERE xcp.numero_pedido = p.id_pedido::text
                        AND xc.is_retirada = TRUE
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

@router.get("/romaneio-novo/{carga_id}/pdf")
def download_romaneio_pdf_novo(carga_id: int, db: Session = Depends(get_db)):
    pdf_content = relatorios_pdf_service.gerar_pdf_romaneio_novo(db, carga_id)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=romaneio_novo_{carga_id}.pdf"}
    )

@router.get("/resumo-produtos-novo/{carga_id}/pdf")
def download_resumo_produtos_pdf_novo(carga_id: int, db: Session = Depends(get_db)):
    pdf_content = relatorios_pdf_service.gerar_pdf_resumo_produtos_novo(db, carga_id)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=resumo_produtos_novo_{carga_id}.pdf"}
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

@router.post("/cargas/{carga_id}/confirmar-entrega")
def confirmar_entrega_carga(carga_id: int, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_user)):
    # 1. Busca a carga
    db_carga = db.query(CargaModel).filter(CargaModel.id == carga_id).first()
    if not db_carga:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    
    # 2. Busca todos os pedidos associados a essa carga
    carga_pedidos = db.query(CargaPedidoModel).filter(CargaPedidoModel.id_carga == carga_id).all()
    if not carga_pedidos:
        raise HTTPException(status_code=400, detail="Esta carga não possui pedidos vinculados.")

    # Importa no escopo local para evitar import circular
    from routers.pedidos import verificar_e_historico_carga
    
    pedidos_com_erro = []
    pedidos_db = []
    
    for cp in carga_pedidos:
        num_ped = cp.numero_pedido
        if not num_ped.isdigit():
            continue
        id_pedido = int(num_ped)
        
        # Lock e busca o status do pedido e código da empresa do cliente
        resultado = db.execute(
            text("""
                SELECT p.status, c.cadastro_codigo_da_empresa, p.id_pedido::text as num_pedido_vis
                FROM public.tb_pedidos p
                LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
                WHERE p.id_pedido = :id
            """),
            {"id": id_pedido}
        ).first()
        
        if not resultado:
            continue
            
        de_status, codigo_empresa, num_pedido_vis = resultado
        if not codigo_empresa or not str(codigo_empresa).strip():
            pedidos_com_erro.append(f"Pedido {num_pedido_vis} (Cliente sem código da empresa)")
        else:
            pedidos_db.append((id_pedido, de_status))
            
    if pedidos_com_erro:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível confirmar a entrega. Os seguintes pedidos possuem problemas:<br>" + "<br>".join(pedidos_com_erro)
        )
        
    # 4. Altera o status de todos os pedidos da carga para "Faturado Supra"
    for id_pedido, de_status in pedidos_db:
        # Atualiza o status do pedido e insere a data de faturamento
        db.execute(text("""
            UPDATE public.tb_pedidos
            SET status = 'FATURADO_SUPRA',
                atualizado_em = now(),
                atualizado_por = 'sistema',
                data_faturamento = now()
            WHERE id_pedido = :id_pedido
        """), {"id_pedido": id_pedido})
        
        # Insere evento no histórico
        try:
            with db.begin_nested():
                db.execute(text("""
                    INSERT INTO public.pedido_status_event (id, pedido_id, de_status, para_status, user_id, motivo, metadata, created_at)
                    VALUES (gen_random_uuid(), :pedido_id, :de_status, 'FATURADO_SUPRA', 'sistema', 'Entrega de carga confirmada em lote', '{}'::jsonb, now())
                """), {
                    "pedido_id": id_pedido,
                    "de_status": de_status
                })
        except Exception:
            pass
            
    # 5. Move a carga para o histórico
    db_carga.is_historico = True
    db_carga.data_faturamento = datetime.now()
    db_carga.data_carregamento = datetime.now()
    
    # Gerar snapshot de auditoria
    gerar_snapshot_carga(db, carga_id, db_carga, carga_pedidos, current_user.email)
    
    db.commit()
    return {"status": "success", "message": "Entrega confirmada com sucesso!"}


# ----------------- RELATÓRIO DE VENDAS POR CLIENTE -----------------

@router.get("/vendas_cliente/filtros")
def get_vendas_cliente_filtros(db: Session = Depends(get_db)):
    """
    Retorna os valores únicos disponíveis para popular os filtros do frontend:
    - Filiais (fornecedor em tb_pedidos)
    - Municípios (entrega_municipio em t_cadastro_cliente_v2)
    - Status do pedido (status em tb_pedidos)
    - Grupos (marca em t_cadastro_produto_v2)
    """
    # 1. Filiais/Fornecedores de Pedidos
    filiais_query = text("SELECT DISTINCT fornecedor FROM public.tb_pedidos WHERE fornecedor IS NOT NULL AND fornecedor != '' ORDER BY fornecedor")
    filiais = db.execute(filiais_query).scalars().all()
    
    # 2. Municípios com compras realizadas
    municipios_query = text("""
        SELECT DISTINCT c.entrega_municipio 
        FROM public.tb_pedidos p
        JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        WHERE c.entrega_municipio IS NOT NULL AND c.entrega_municipio != ''
        ORDER BY c.entrega_municipio
    """)
    municipios = db.execute(municipios_query).scalars().all()
    
    # 3. Status de Pedidos
    status_query = text("SELECT DISTINCT status FROM public.tb_pedidos WHERE status IS NOT NULL AND status != '' AND UPPER(status) NOT LIKE '%CANCEL%' ORDER BY status")
    status = db.execute(status_query).scalars().all()
    
    # 4. Grupos (marcas) de Produtos
    grupos_query = text("SELECT DISTINCT marca FROM public.t_cadastro_produto_v2 WHERE marca IS NOT NULL AND marca != '' ORDER BY marca")
    grupos = db.execute(grupos_query).scalars().all()
    
    return {
        "filiais": filiais,
        "municipios": municipios,
        "status": status,
        "grupos": grupos
    }


@router.get("/vendas_cliente")
def get_vendas_cliente(
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    faturamento_inicio: Optional[str] = Query(None),
    faturamento_fim: Optional[str] = Query(None),
    filiais: Optional[List[str]] = Query(None),
    categoria: Optional[str] = Query(None), # "INSUMOS" ou "PET"
    status_list: Optional[List[str]] = Query(None),
    municipios: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retorna a listagem consolidada de vendas por cliente com base nos filtros informados.
    """
    # Normalização de parâmetros para chamadas diretas em Python/testes
    if not isinstance(data_inicio, str): data_inicio = None
    if not isinstance(data_fim, str): data_fim = None
    if not isinstance(faturamento_inicio, str): faturamento_inicio = None
    if not isinstance(faturamento_fim, str): faturamento_fim = None
    if not isinstance(filiais, list): filiais = None
    if not isinstance(categoria, str): categoria = None
    if not isinstance(status_list, list): status_list = None
    if not isinstance(municipios, list): municipios = None

    query_str = """
        SELECT
            p.id_pedido                             AS numero_pedido,
            MAX(p.pedido_supra)                     AS pedido_supra,
            MAX(p.nota_fiscal)                      AS danfe,
            to_char(MAX(p.data_faturamento), 'YYYY-MM-DD') AS data_faturamento,
            MAX(p.codigo_cliente)                   AS codigo_cliente,
            MAX(COALESCE(c.cadastro_nome_cliente, p.cliente)) AS cliente,
            MAX(COALESCE(c.cadastro_nome_fantasia, 'Sem Nome Fantasia')) AS nome_fantasia,
            MAX(COALESCE(c.entrega_municipio, 'Sem Município')) AS municipio,
            CAST(SUM(COALESCE(pr.peso, 0) * i.quantidade) AS FLOAT) AS peso_liquido,
            CAST(SUM(
                CASE
                    WHEN p.usar_valor_com_frete = true THEN 0
                    ELSE COALESCE(i.subtotal_sem_f, 0)
                END
            ) AS FLOAT) AS valor_sem_frete,
            CAST(SUM(
                CASE
                    WHEN p.usar_valor_com_frete = true THEN COALESCE(i.subtotal_com_f, 0)
                    ELSE 0
                END
            ) AS FLOAT) AS valor_com_frete
        FROM public.tb_pedidos_itens i
        JOIN public.tb_pedidos p ON p.id_pedido = i.id_pedido
        LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        LEFT JOIN public.t_cadastro_produto_v2 pr ON pr.codigo_supra = i.codigo
        WHERE i.quantidade > 0 AND UPPER(p.status) NOT LIKE '%CANCEL%'
    """
    
    params = {}
    
    if data_inicio:
        query_str += " AND p.created_at::date >= CAST(:data_inicio AS DATE)"
        params["data_inicio"] = data_inicio
        
    if data_fim:
        query_str += " AND p.created_at::date <= CAST(:data_fim AS DATE)"
        params["data_fim"] = data_fim
        
    if faturamento_inicio:
        query_str += " AND p.data_faturamento::date >= CAST(:faturamento_inicio AS DATE)"
        params["faturamento_inicio"] = faturamento_inicio
        
    if faturamento_fim:
        query_str += " AND p.data_faturamento::date <= CAST(:faturamento_fim AS DATE)"
        params["faturamento_fim"] = faturamento_fim
        
    if filiais:
        query_str += " AND p.fornecedor = ANY(:filiais)"
        params["filiais"] = filiais
        
    if categoria:
        query_str += " AND UPPER(pr.tipo) = :categoria"
        params["categoria"] = categoria.upper()
        
    if status_list:
        query_str += " AND p.status = ANY(:status_list)"
        params["status_list"] = status_list
        
    if municipios:
        query_str += " AND c.entrega_municipio = ANY(:municipios)"
        params["municipios"] = municipios
        
    query_str += " GROUP BY p.id_pedido ORDER BY p.id_pedido DESC"
    
    rows = db.execute(text(query_str), params).mappings().all()
    
    return [dict(r) for r in rows]


@router.get("/vendas_produtos")
def get_vendas_produtos(
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    faturamento_inicio: Optional[str] = Query(None),
    faturamento_fim: Optional[str] = Query(None),
    filiais: Optional[List[str]] = Query(None),
    categoria: Optional[str] = Query(None), # "INSUMOS" ou "PET"
    status_list: Optional[List[str]] = Query(None),
    municipios: Optional[List[str]] = Query(None),
    grupos: Optional[List[str]] = Query(None), # marcas em t_cadastro_produto_v2
    db: Session = Depends(get_db)
):
    """
    Retorna a listagem consolidada de vendas agrupada por produto com base nos filtros informados.
    """
    # Normalização de parâmetros para chamadas diretas em Python/testes
    if not isinstance(data_inicio, str): data_inicio = None
    if not isinstance(data_fim, str): data_fim = None
    if not isinstance(faturamento_inicio, str): faturamento_inicio = None
    if not isinstance(faturamento_fim, str): faturamento_fim = None
    if not isinstance(filiais, list): filiais = None
    if not isinstance(categoria, str): categoria = None
    if not isinstance(status_list, list): status_list = None
    if not isinstance(municipios, list): municipios = None
    if not isinstance(grupos, list): grupos = None

    query_str = """
        SELECT
            i.codigo                                AS codigo_produto,
            MAX(i.nome)                            AS produto,
            MAX(i.embalagem)                       AS embalagem,
            CAST(MAX(COALESCE(pr.peso, 0)) AS FLOAT) AS peso_liquido_unitario,
            CAST(SUM(i.quantidade) AS FLOAT)        AS quantidade,
            CAST(SUM(COALESCE(pr.peso, 0) * i.quantidade) AS FLOAT) AS peso_liquido_acumulado,
            CAST(SUM(
                CASE
                    WHEN p.usar_valor_com_frete = true THEN 0
                    ELSE COALESCE(i.subtotal_sem_f, 0)
                END
            ) AS FLOAT) AS valor_sem_frete,
            CAST(SUM(
                CASE
                    WHEN p.usar_valor_com_frete = true THEN COALESCE(i.subtotal_com_f, 0)
                    ELSE 0
                END
            ) AS FLOAT) AS valor_com_frete
        FROM public.tb_pedidos_itens i
        JOIN public.tb_pedidos p ON p.id_pedido = i.id_pedido
        LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        LEFT JOIN public.t_cadastro_produto_v2 pr ON pr.codigo_supra = i.codigo
        WHERE i.quantidade > 0 AND UPPER(p.status) NOT LIKE '%CANCEL%'
    """
    
    params = {}
    
    if data_inicio:
        query_str += " AND p.created_at::date >= CAST(:data_inicio AS DATE)"
        params["data_inicio"] = data_inicio
        
    if data_fim:
        query_str += " AND p.created_at::date <= CAST(:data_fim AS DATE)"
        params["data_fim"] = data_fim
        
    if faturamento_inicio:
        query_str += " AND p.data_faturamento::date >= CAST(:faturamento_inicio AS DATE)"
        params["faturamento_inicio"] = faturamento_inicio
        
    if faturamento_fim:
        query_str += " AND p.data_faturamento::date <= CAST(:faturamento_fim AS DATE)"
        params["faturamento_fim"] = faturamento_fim
        
    if filiais:
        query_str += " AND p.fornecedor = ANY(:filiais)"
        params["filiais"] = filiais
        
    if categoria:
        query_str += " AND UPPER(pr.tipo) = :categoria"
        params["categoria"] = categoria.upper()
        
    if status_list:
        query_str += " AND p.status = ANY(:status_list)"
        params["status_list"] = status_list
        
    if municipios:
        query_str += " AND c.entrega_municipio = ANY(:municipios)"
        params["municipios"] = municipios
        
    if grupos:
        query_str += " AND pr.marca = ANY(:grupos)"
        params["grupos"] = grupos
        
    query_str += " GROUP BY i.codigo ORDER BY peso_liquido_acumulado DESC"
    
    rows = db.execute(text(query_str), params).mappings().all()
    
    return [dict(r) for r in rows]


@router.get("/validacao_pedidos")
def get_validacao_pedidos(
    faturamento_inicio: Optional[str] = Query(None),
    faturamento_fim: Optional[str] = Query(None),
    filiais: Optional[List[str]] = Query(None),
    categoria: Optional[str] = Query(None), # "INSUMOS" ou "PET"
    tipo_entrega: Optional[str] = Query(None), # "ENTREGA" ou "RETIRADA" ou "AMBOS"
    db: Session = Depends(get_db)
):
    """
    Retorna os dados para o relatório de Validação de Pedidos.
    Filtros: Filial, Categoria, Período Faturamento, Entrega/Retirada
    Campos: Data Faturamento, Codigo Cliente, Cliente, Pedido Supra, Nota Fiscal, 
            Peso Liquido, Valor Nota, Valor Pedido, Diferença.
    """
    if not isinstance(faturamento_inicio, str): faturamento_inicio = None
    if not isinstance(faturamento_fim, str): faturamento_fim = None
    if not isinstance(filiais, list): filiais = None
    if not isinstance(categoria, str): categoria = None
    if not isinstance(tipo_entrega, str): tipo_entrega = None

    query_str = """
        SELECT
            p.id_pedido                             AS numero_pedido,
            to_char(MAX(p.data_faturamento), 'YYYY-MM-DD') AS data_faturamento,
            MAX(p.codigo_cliente)                   AS codigo_cliente,
            MAX(COALESCE(c.cadastro_nome_cliente, p.cliente)) AS cliente,
            MAX(p.pedido_supra)                     AS pedido_supra,
            MAX(p.nota_fiscal)                      AS nota_fiscal,
            CAST(SUM(COALESCE(pr.peso, 0) * i.quantidade) AS FLOAT) AS peso_liquido,
            CAST(MAX(p.valor_nota) AS FLOAT)        AS valor_nota_fiscal,
            CAST(MAX(p.total_pedido) AS FLOAT)      AS valor_pedido,
            CAST(COALESCE(MAX(p.valor_nota), 0) - COALESCE(MAX(p.total_pedido), 0) AS FLOAT) AS diferenca_valores
        FROM public.tb_pedidos_itens i
        JOIN public.tb_pedidos p ON p.id_pedido = i.id_pedido
        LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        LEFT JOIN public.t_cadastro_produto_v2 pr ON pr.codigo_supra = i.codigo
        WHERE i.quantidade > 0 AND UPPER(p.status) NOT LIKE '%CANCEL%' AND p.status IN ('FATURADO_SUPRA', 'Faturado Supra')
    """
    
    params = {}
    
    if faturamento_inicio:
        query_str += " AND p.data_faturamento::date >= CAST(:faturamento_inicio AS DATE)"
        params["faturamento_inicio"] = faturamento_inicio
        
    if faturamento_fim:
        query_str += " AND p.data_faturamento::date <= CAST(:faturamento_fim AS DATE)"
        params["faturamento_fim"] = faturamento_fim
        
    if filiais:
        query_str += " AND p.fornecedor = ANY(:filiais)"
        params["filiais"] = filiais
        
    if categoria:
        query_str += " AND UPPER(pr.tipo) = :categoria"
        params["categoria"] = categoria.upper()
        
    if tipo_entrega:
        if tipo_entrega.upper() == "ENTREGA":
            query_str += " AND p.usar_valor_com_frete = true"
        elif tipo_entrega.upper() == "RETIRADA" or tipo_entrega.upper() == "RETIRA":
            query_str += " AND (p.usar_valor_com_frete = false OR p.usar_valor_com_frete IS NULL)"
            
    query_str += " GROUP BY p.id_pedido ORDER BY MAX(p.nota_fiscal) ASC NULLS LAST"
    
    rows = db.execute(text(query_str), params).mappings().all()
    
    return [dict(r) for r in rows]



@router.get("/gerencial")
def get_relatorio_gerencial(
    codigo_cliente: Optional[str] = Query(None),
    cnpj_cpf: Optional[str] = Query(None),
    nome_cliente: Optional[str] = Query(None),
    municipio: Optional[str] = Query(None),
    vendedor: Optional[str] = Query(None),
    data_compra_inicio: Optional[str] = Query(None),
    data_compra_fim: Optional[str] = Query(None),
    observacao: Optional[str] = Query(None),
    status_cadastro: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query_str = """
        SELECT 
            COALESCE(NULLIF(c.cadastro_cnpj, ''), c.cadastro_cpf) AS documento,
            c.cadastro_nome_cliente AS nome_cliente,
            c.cadastro_atividade_principal AS atividade_principal,
            COALESCE(c.faturamento_municipio, c.entrega_municipio) AS municipio,
            c.elaboracao_vendedor AS vendedor,
            MAX(p.created_at) AS data_ultima_compra,
            c.outras_observacoes AS observacao
        FROM public.t_cadastro_cliente_v2 c
        LEFT JOIN public.tb_pedidos p ON p.codigo_cliente = c.cadastro_codigo_da_empresa::text
        WHERE 1=1
    """
    params = {}
    
    if codigo_cliente:
        query_str += " AND c.cadastro_codigo_da_empresa::text ILIKE :codigo_cliente"
        params["codigo_cliente"] = f"%{codigo_cliente}%"
        
    if cnpj_cpf:
        query_str += " AND (c.cadastro_cnpj ILIKE :cnpj_cpf OR c.cadastro_cpf ILIKE :cnpj_cpf)"
        params["cnpj_cpf"] = f"%{cnpj_cpf}%"
    
    if nome_cliente:
        query_str += " AND c.cadastro_nome_cliente ILIKE :nome_cliente"
        params["nome_cliente"] = f"%{nome_cliente}%"
        
    if municipio:
        query_str += " AND COALESCE(c.faturamento_municipio, c.entrega_municipio) = :municipio"
        params["municipio"] = municipio
        
    if vendedor:
        query_str += " AND c.elaboracao_vendedor = :vendedor"
        params["vendedor"] = vendedor
        
    if observacao:
        query_str += " AND c.outras_observacoes ILIKE :observacao"
        params["observacao"] = f"%{observacao}%"
        
    if status_cadastro:
        query_str += " AND c.cadastro_status_cadastro = :status_cadastro"
        params["status_cadastro"] = status_cadastro
        
    query_str += " GROUP BY c.id"
    
    having_clauses = []
    if data_compra_inicio:
        having_clauses.append("MAX(p.created_at)::date >= CAST(:data_compra_inicio AS DATE)")
        params["data_compra_inicio"] = data_compra_inicio
        
    if data_compra_fim:
        having_clauses.append("MAX(p.created_at)::date <= CAST(:data_compra_fim AS DATE)")
        params["data_compra_fim"] = data_compra_fim
        
    if having_clauses:
        query_str += " HAVING " + " AND ".join(having_clauses)
        
    query_str += " ORDER BY c.cadastro_nome_cliente ASC"
    
    rows = db.execute(text(query_str), params).mappings().all()
    
    return [dict(r) for r in rows]

@router.get("/gerencial/filtros")
def get_filtros_gerencial(db: Session = Depends(get_db)):
    # 1. Municípios de Clientes
    q_mun = text("""
        SELECT DISTINCT COALESCE(faturamento_municipio, entrega_municipio) 
        FROM public.t_cadastro_cliente_v2 
        WHERE COALESCE(faturamento_municipio, entrega_municipio) IS NOT NULL 
          AND TRIM(COALESCE(faturamento_municipio, entrega_municipio)) != '' 
        ORDER BY 1
    """)
    
    # 2. Vendedores - Buscar do Catálogo (tb_vendedores) e complementar com clientes
    vendedores = []
    try:
        q_vend_cat = text("SELECT DISTINCT nome FROM public.tb_vendedores WHERE nome IS NOT NULL AND TRIM(nome) != '' ORDER BY 1")
        vendedores = [r[0].strip() for r in db.execute(q_vend_cat).all() if r[0] and r[0].strip()]
    except Exception:
        pass
    if not vendedores:
        try:
            q_vend = text("SELECT DISTINCT elaboracao_vendedor FROM public.t_cadastro_cliente_v2 WHERE elaboracao_vendedor IS NOT NULL AND TRIM(elaboracao_vendedor) != '' ORDER BY 1")
            vendedores = [r[0].strip() for r in db.execute(q_vend).all() if r[0] and r[0].strip()]
        except Exception:
            pass
            
    # 3. Filiais - Buscar do Catálogo (tb_filiais)
    filiais = []
    try:
        q_fil = text("SELECT DISTINCT filial FROM public.tb_filiais WHERE filial IS NOT NULL AND TRIM(filial) != '' ORDER BY 1")
        filiais = [r[0].strip() for r in db.execute(q_fil).all() if r[0] and r[0].strip()]
    except Exception:
        pass
    if not filiais:
        try:
            q_fil_prod = text("SELECT DISTINCT fornecedor FROM public.t_cadastro_produto_v2 WHERE fornecedor IS NOT NULL AND TRIM(fornecedor) != '' ORDER BY 1")
            filiais = [r[0].strip() for r in db.execute(q_fil_prod).all() if r[0] and r[0].strip()]
        except Exception:
            pass

    # 4. Rotas - Buscar do Catálogo (tb_municipio_rota)
    rotas_geral_set = set()
    try:
        q_rotas_cat = text("SELECT DISTINCT rota FROM public.tb_municipio_rota WHERE rota IS NOT NULL ORDER BY rota")
        for r in db.execute(q_rotas_cat).all():
            if r[0] is not None and str(r[0]).strip():
                rotas_geral_set.add(str(r[0]).strip())
    except Exception:
        pass
        
    def rota_sort_key(val):
        try:
            return (0, int(val))
        except ValueError:
            return (1, str(val))
            
    rotas_geral = sorted(list(rotas_geral_set), key=rota_sort_key)
    rotas_aproximacao = []  # Campo de rota aproximação ainda não existe no catálogo
    
    # 5. Status do Cadastro
    q_status = text("SELECT DISTINCT cadastro_status_cadastro FROM public.t_cadastro_cliente_v2 WHERE cadastro_status_cadastro IS NOT NULL AND TRIM(cadastro_status_cadastro) != '' ORDER BY 1")
    
    municipios = [r[0].strip() for r in db.execute(q_mun).all() if r[0] and r[0].strip()]
    status_cadastro = [r[0].strip() for r in db.execute(q_status).all() if r[0] and r[0].strip()]
    
    # 6. Mapeamento de Rota -> Municípios do Catálogo (tb_municipio_rota)
    rotas_municipios = {}
    try:
        q_mr = text("SELECT rota, municipio FROM public.tb_municipio_rota WHERE rota IS NOT NULL AND municipio IS NOT NULL ORDER BY rota, municipio")
        for r in db.execute(q_mr).all():
            r_rota = str(r[0]).strip()
            r_mun_raw = str(r[1]).strip()
            if not r_rota or not r_mun_raw:
                continue
            r_num = r_rota.upper().replace('ROTA', '').strip()
            if r_num not in rotas_municipios:
                rotas_municipios[r_num] = []
            
            # Adiciona município limpo (sem UF) e formato original
            r_mun_clean = re.sub(r'\s*\([A-Za-z]{2}\)', '', r_mun_raw).strip()
            if r_mun_clean and r_mun_clean not in rotas_municipios[r_num]:
                rotas_municipios[r_num].append(r_mun_clean)
            if r_mun_raw not in rotas_municipios[r_num]:
                rotas_municipios[r_num].append(r_mun_raw)
    except Exception:
        pass

    return {
        "municipios": municipios,
        "vendedores": vendedores,
        "filiais": filiais,
        "rotas": rotas_geral,
        "rotas_geral": rotas_geral,
        "rotas_aproximacao": rotas_aproximacao,
        "status_cadastro": status_cadastro,
        "rotas_municipios": rotas_municipios
    }

@router.get("/gerencial2")
def get_relatorio_gerencial2(
    codigo_cliente: Optional[str] = Query(None),
    cnpj_cpf: Optional[str] = Query(None),
    nome_cliente: Optional[str] = Query(None),
    vendedor: Optional[str] = Query(None),
    meses: int = Query(12),
    db: Session = Depends(get_db)
):
    # Using PostgreSQL syntax: DATE_TRUNC and TO_CHAR
    query_str = f"""
        SELECT 
            c.cadastro_codigo_da_empresa AS codigo_cliente,
            c.cadastro_nome_cliente AS cliente,
            TO_CHAR(DATE_TRUNC('month', p.created_at), 'YYYY-MM') AS mes_ano,
            SUM(COALESCE(pb.peso_liquido, 0)) AS peso,
            SUM(p.total_pedido) AS valor
        FROM public.tb_pedidos p
        JOIN public.t_cadastro_cliente_v2 c ON p.codigo_cliente = c.cadastro_codigo_da_empresa
        LEFT JOIN (
            SELECT i.id_pedido, SUM(i.quantidade * COALESCE(CAST(pr.peso AS FLOAT), 0)) as peso_liquido
            FROM public.tb_pedidos_itens i
            LEFT JOIN public.t_cadastro_produto_v2 pr ON pr.codigo_supra = i.codigo
            GROUP BY i.id_pedido
        ) pb ON pb.id_pedido = p.id_pedido
        WHERE p.created_at >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '{meses - 1} months'
          AND p.status != 'Cancelado'
    """
    
    params = {}
    
    if codigo_cliente:
        query_str += " AND c.cadastro_codigo_da_empresa::text ILIKE :codigo_cliente"
        params["codigo_cliente"] = f"%{codigo_cliente}%"
        
    if cnpj_cpf:
        query_str += " AND (c.cadastro_cnpj ILIKE :cnpj_cpf OR c.cadastro_cpf ILIKE :cnpj_cpf)"
        params["cnpj_cpf"] = f"%{cnpj_cpf}%"
        
    if nome_cliente:
        query_str += " AND c.cadastro_nome_cliente ILIKE :nome_cliente"
        params["nome_cliente"] = f"%{nome_cliente}%"
        
    if vendedor:
        query_str += " AND c.elaboracao_vendedor = :vendedor"
        params["vendedor"] = vendedor
        
    query_str += """
        GROUP BY 1, 2, 3
        ORDER BY c.cadastro_nome_cliente, mes_ano
    """
    
    rows = db.execute(text(query_str), params).mappings().all()
    
    data = {}
    for r in rows:
        cod = r["codigo_cliente"]
        # Ensure cod is string and not None, fallback to id if needed but we joined on codigo_da_empresa
        if not cod:
            continue
        if cod not in data:
            data[cod] = {
                "codigo_cliente": cod,
                "cliente": r["cliente"],
                "meses": {}
            }
        data[cod]["meses"][r["mes_ano"]] = {
            "peso": float(r["peso"] or 0),
            "valor": float(r["valor"] or 0)
        }
        
    return list(data.values())

def _parse_date(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day)
    s = str(val).strip().replace('Z', '')
    if not s or s.upper() in ('NULL', '\\N', 'NONE', 'NAN'):
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(s[:19] if ' ' in fmt else s[:10], fmt)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    return None

@router.get('/gerencial3')
def get_relatorio_gerencial3(
    codigo_cliente: Optional[str] = Query(None),
    cnpj_cpf: Optional[str] = Query(None),
    nome_cliente: Optional[str] = Query(None),
    vendedor: Optional[str] = Query(None),
    filial: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    municipio: Optional[str] = Query(None),
    rota_geral: Optional[str] = Query(None),
    rota_principal: Optional[str] = Query(None),
    rota_aproximacao: Optional[str] = Query(None),
    status_cadastro: Optional[str] = Query(None),
    tipo_entrega: Optional[str] = Query(None),
    meses: int = Query(12),
    db: Session = Depends(get_db)
):
    query_str = '''
        SELECT 
            c.id AS cliente_id,
            c.cadastro_codigo_da_empresa AS codigo_cliente,
            c.cadastro_nome_cliente AS cliente,
            c.cadastro_periodo_de_compra AS periodo_de_compra,
            c.ultimas_compras_previsao_proxima AS previsao_proxima_compra_cad,
            c.ultimas_compras_emissao AS ultimas_compras_emissao,
            vendas.mes_ano,
            COALESCE(vendas.peso, 0) AS peso,
            COALESCE(vendas.valor, 0) AS valor,
            vendas.data_ultima_compra_mes,
            ult_pedido.max_data_pedido
        FROM public.t_cadastro_cliente_v2 c
        LEFT JOIN (
            SELECT 
                TRIM(p.codigo_cliente::text) AS cod_cli,
                TO_CHAR(DATE_TRUNC('month', p.created_at), 'YYYY-MM') AS mes_ano,
                CAST(SUM(COALESCE(pr.peso, 0) * i.quantidade) AS FLOAT) AS peso,
                CAST(SUM(
                    CASE
                        WHEN p.usar_valor_com_frete = true THEN COALESCE(i.subtotal_com_f, 0)
                        ELSE COALESCE(i.subtotal_sem_f, 0)
                    END
                ) AS FLOAT) AS valor,
                MAX(p.created_at) AS data_ultima_compra_mes
            FROM public.tb_pedidos_itens i
            JOIN public.tb_pedidos p ON p.id_pedido = i.id_pedido
            LEFT JOIN public.t_cadastro_produto_v2 pr ON pr.codigo_supra = i.codigo
            WHERE p.created_at >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '{meses_str} months'
              AND UPPER(p.status) NOT LIKE '%CANCEL%'
              AND i.quantidade > 0
              {itens_filtro}
            GROUP BY TRIM(p.codigo_cliente::text), TO_CHAR(DATE_TRUNC('month', p.created_at), 'YYYY-MM')
        ) vendas ON NULLIF(TRIM(c.cadastro_codigo_da_empresa::text), '') IS NOT NULL 
                AND vendas.cod_cli = TRIM(c.cadastro_codigo_da_empresa::text)
        LEFT JOIN (
            SELECT 
                TRIM(p.codigo_cliente::text) AS cod_cli,
                MAX(p.created_at) AS max_data_pedido
            FROM public.tb_pedidos p
            WHERE UPPER(p.status) NOT LIKE '%CANCEL%'
            GROUP BY TRIM(p.codigo_cliente::text)
        ) ult_pedido ON NULLIF(TRIM(c.cadastro_codigo_da_empresa::text), '') IS NOT NULL
                    AND ult_pedido.cod_cli = TRIM(c.cadastro_codigo_da_empresa::text)
        WHERE 1=1
    '''
    
    itens_filtro = ""
    params = {}
    
    if codigo_cliente:
        query_str += " AND c.cadastro_codigo_da_empresa::text ILIKE :codigo_cliente"
        params['codigo_cliente'] = f"%{codigo_cliente}%"
        
    if cnpj_cpf:
        query_str += " AND (c.cadastro_cnpj ILIKE :cnpj_cpf OR c.cadastro_cpf ILIKE :cnpj_cpf)"
        params['cnpj_cpf'] = f"%{cnpj_cpf}%"
        
    if nome_cliente:
        query_str += " AND c.cadastro_nome_cliente ILIKE :nome_cliente"
        params['nome_cliente'] = f"%{nome_cliente}%"
        
    if vendedor:
        query_str += " AND (c.elaboracao_vendedor ILIKE :vendedor OR c.elaboracao_vendedor = :vendedor_exact)"
        params['vendedor'] = f"%{vendedor}%"
        params['vendedor_exact'] = vendedor

    if filial:
        query_str += " AND (c.compras_filial_resposavel ILIKE :filial OR EXISTS (SELECT 1 FROM public.tb_pedidos pf WHERE pf.codigo_cliente::text = c.cadastro_codigo_da_empresa::text AND pf.fornecedor ILIKE :filial))"
        itens_filtro += " AND p.fornecedor ILIKE :filial"
        params['filial'] = f"%{filial}%"
        
    if categoria:
        itens_filtro += " AND (UPPER(pr.tipo) = :categoria OR UPPER(COALESCE(pr.tipo, '')) LIKE :categoria_like)"
        params['categoria'] = categoria.upper()
        params['categoria_like'] = f"%{categoria.upper()}%"

    if municipio:
        query_str += " AND UPPER(TRIM(COALESCE(c.faturamento_municipio, c.entrega_municipio))) = UPPER(TRIM(:municipio))"
        params['municipio'] = municipio

    rota_geral_val = str(rota_principal or rota_geral or '').strip()
    if rota_geral_val:
        rota_num = rota_geral_val.upper().replace('ROTA', '').strip()
        query_str += """ AND (
            TRIM(c.entrega_rota_principal::text) = :rota_geral_val
            OR TRIM(c.entrega_rota_principal::text) = :rota_num
            OR TRIM(c.entrega_rota_principal::text) ILIKE :rota_prefixo
            OR EXISTS (
                SELECT 1 FROM public.tb_municipio_rota mr 
                WHERE mr.rota::text = :rota_num 
                  AND UPPER(REGEXP_REPLACE(mr.municipio, '\\s*\\([A-Z]{2}\\)', '')) = UPPER(TRIM(COALESCE(c.entrega_municipio, c.faturamento_municipio, '')))
            )
        )"""
        params['rota_geral_val'] = rota_geral_val
        params['rota_num'] = rota_num
        params['rota_prefixo'] = f"{rota_num} - %"

    if rota_aproximacao:
        rota_aprox_val = str(rota_aproximacao).strip()
        rota_aprox_num = rota_aprox_val.upper().replace('ROTA', '').strip()
        query_str += """ AND (
            TRIM(c.entrega_rota_aproximacao::text) = :rota_aprox_val
            OR TRIM(c.entrega_rota_aproximacao::text) = :rota_aprox_num
            OR TRIM(c.entrega_rota_aproximacao::text) ILIKE :rota_aprox_prefixo
        )"""
        params['rota_aprox_val'] = rota_aprox_val
        params['rota_aprox_num'] = rota_aprox_num
        params['rota_aprox_prefixo'] = f"{rota_aprox_num} - %"

    if status_cadastro:
        query_str += " AND c.cadastro_status_cadastro = :status_cadastro"
        params['status_cadastro'] = status_cadastro
        
    if tipo_entrega:
        query_str += " AND c.entrega_tipo_entrega ILIKE :tipo_entrega"
        params['tipo_entrega'] = f"%{tipo_entrega}%"
        
    query_str = query_str.replace('{itens_filtro}', itens_filtro)
    query_str = query_str.replace('{meses_str}', str(max(1, meses - 1)))
    query_str += " ORDER BY c.cadastro_nome_cliente, vendas.mes_ano"
    
    rows = db.execute(text(query_str), params).mappings().all()
    
    data = {}
    for r in rows:
        cid = r['cliente_id']
        cod = (r['codigo_cliente'] or '').strip()
        key = f"CLI_{cid}"
        
        if key not in data:
            data[key] = {
                'codigo_cliente': cod,
                'cliente': r['cliente'] or '',
                'periodo_de_compra': r['periodo_de_compra'] or '',
                'previsao_proxima_compra': None,
                'data_ultima_compra_geral': None,
                'meses': {}
            }
            
            dt_ped = _parse_date(r['max_data_pedido'])
            dt_emissao = _parse_date(r['ultimas_compras_emissao'])
            
            dt_ult = None
            if dt_ped and dt_emissao:
                dt_ult = max(dt_ped, dt_emissao)
            elif dt_ped:
                dt_ult = dt_ped
            elif dt_emissao:
                dt_ult = dt_emissao
                
            if dt_ult:
                data[key]['data_ultima_compra_geral'] = dt_ult.strftime('%Y-%m-%d')
                
            dias = 0
            if r['periodo_de_compra']:
                nums = re.findall(r'\d+', str(r['periodo_de_compra']))
                if nums:
                    dias = int(nums[0])
                    
            if dt_ult and dias > 0:
                data[key]['previsao_proxima_compra'] = (dt_ult + timedelta(days=dias)).strftime('%Y-%m-%d')
            else:
                dt_prev_fallback = _parse_date(r['previsao_proxima_compra_cad'])
                if dt_prev_fallback:
                    data[key]['previsao_proxima_compra'] = dt_prev_fallback.strftime('%Y-%m-%d')
                    
        m_ano = r['mes_ano']
        if m_ano:
            data[key]['meses'][m_ano] = {
                'peso': float(r['peso'] or 0),
                'valor': float(r['valor'] or 0)
            }
            
    items = list(data.values())
    
    # 1. Ordenação secundária por nome do cliente ASC
    items.sort(key=lambda x: (x.get('cliente') or '').upper())
    
    # 2. Ordenação primária por previsão de compra DESC (datas futuras primeiro, sem previsão por último)
    items.sort(
        key=lambda x: (
            1 if (x.get('previsao_proxima_compra') and str(x['previsao_proxima_compra']).strip()) else 0,
            str(x.get('previsao_proxima_compra') or '').strip()[:10]
        ),
        reverse=True
    )
    
    return items

