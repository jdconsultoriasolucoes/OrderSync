from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.cliente_v2 import ClienteModelV2
from models.pedido import PedidoModel
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import func
import re

router = APIRouter()

def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        # Tenta os formatos mais comuns de data que podem estar na base
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%d/%m/%y'):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                pass
    except Exception:
        pass
    return None

def extract_days(period_str: str) -> int:
    if not period_str:
        return 0
    # Extrai o primeiro numero encontrado na string
    numbers = re.findall(r'\d+', period_str)
    if numbers:
        return int(numbers[0])
    return 0

@router.get("/")
def get_captacao_pedidos(db: Session = Depends(get_db)):
    # 1. Obter todos os clientes
    clientes = db.query(ClienteModelV2).all()
    
    # 2. Obter a última data de pedido para cada cliente (MAX por codigo_cliente)
    # Filtramos por status para evitar considerar orçamentos ou cancelados se desejar, 
    # mas o pedido mais recente costuma ser o melhor indicador de atividade.
    ultimas_datas = db.query(
        PedidoModel.codigo_cliente,
        func.max(PedidoModel.created_at).label("ultima_data")
    ).filter(PedidoModel.status != "CANCELADO").group_by(PedidoModel.codigo_cliente).all()
    
    dict_ultimas_datas = {row.codigo_cliente: row.ultima_data for row in ultimas_datas}
    
    hoje = datetime.now()
    resultados = []
    
    for c in clientes:
        ativo = getattr(c, 'cadastro_ativo', False)
        if ativo is None:
            ativo = False
            
        codigo_cliente = c.cadastro_codigo_da_empresa or ""
        nome_cliente = c.cadastro_nome_cliente or ""
        nome_fantasia = c.cadastro_nome_fantasia or ""
        rota_geral = c.entrega_rota_principal or ""
        rota_aprox = c.entrega_rota_aproximacao or ""
        municipio = c.entrega_municipio or c.faturamento_municipio or ""
        
        # LOGICA NOVA: Busca na dict de pedidos reais
        ultima_compra_data = dict_ultimas_datas.get(codigo_cliente)
        
        # Fallback (opcional): se não tem pedido no sistema novo, tenta o campo legado se estiver preenchido
        if not ultima_compra_data and c.ultimas_compras_emissao:
            ultima_compra_data = parse_date(c.ultimas_compras_emissao)
        
        periodo_str = c.cadastro_periodo_de_compra or ""
        periodo_em_dias = extract_days(period_str)
        
        vendedor = c.elaboracao_vendedor or ""
        
        dias_sem_comprar = 0
        previsao_data = None
        status_cor = "vermelho"
        
        if ultima_compra_data:
            delta = (hoje - ultima_compra_data).days
            dias_sem_comprar = delta if delta > 0 else 0
            
            # Cor (Verde <= 60, Amarelo <= 90, Vermelho > 90)
            if dias_sem_comprar <= 60:
                status_cor = "verde"
            elif dias_sem_comprar <= 90:
                status_cor = "amarelo"
            else:
                status_cor = "vermelho"
                
            import datetime as dt
            previsao_data = ultima_compra_data + dt.timedelta(days=periodo_em_dias)
            
        else:
            status_cor = "vermelho"
            
        grupo_ordem = 3
        if ativo:
            if ultima_compra_data:
                grupo_ordem = 1
            else:
                grupo_ordem = 2
                
        sort_date = previsao_data if previsao_data else datetime.max
        
        resultados.append({
            "grupo_ordem": grupo_ordem,
            "sort_date": sort_date,
            "rota_geral": rota_geral,
            "rota_aproximacao": rota_aprox,
            "codigo_cliente": codigo_cliente,
            "cliente": nome_cliente,
            "nome_fantasia": nome_fantasia,
            "municipio": municipio,
            "data_ultima_compra": ultima_compra_data.strftime('%d/%m/%Y') if ultima_compra_data else "",
            "periodo_em_dias": periodo_em_dias,
            "data_previsao_proxima": previsao_data.strftime('%d/%m/%Y') if previsao_data else "",
            "dias_sem_comprar": dias_sem_comprar,
            "status_cor": status_cor,
            "ativo": ativo,
            "vendedor": vendedor
        })
        
    resultados.sort(key=lambda x: (x["grupo_ordem"], x["sort_date"]))
    
    # Remover campos de sorting que nao precisaremos entregar no json (opcional, mas economiza banda)
    for res in resultados:
        res.pop('grupo_ordem', None)
        res.pop('sort_date', None)
        
    return resultados
