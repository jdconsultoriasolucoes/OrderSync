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

def _get_captacao_data(db: Session):
    # 1. Obter todos os clientes
    clientes = db.query(ClienteModelV2).all()
    
    # 2. Obter a última data de pedido para cada cliente
    ultimas_datas = db.query(
        PedidoModel.codigo_cliente,
        func.max(PedidoModel.created_at).label("ultima_data")
    ).filter(PedidoModel.status != "CANCELADO").group_by(PedidoModel.codigo_cliente).all()
    
    dict_ultimas_datas = {row.codigo_cliente: row.ultima_data for row in ultimas_datas}
    
    hoje = datetime.now()
    resultados = []
    
    import datetime as dt_mod
    
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
        
        ultima_compra_data = dict_ultimas_datas.get(codigo_cliente)
        
        if not ultima_compra_data and c.ultimas_compras_emissao:
            ultima_compra_data = parse_date(c.ultimas_compras_emissao)
        
        periodo_str = c.cadastro_periodo_de_compra or ""
        periodo_em_dias = extract_days(periodo_str)
        
        vendedor = c.elaboracao_vendedor or "Sem Vendedor"
        
        dias_sem_comprar = 0
        previsao_data = None
        status_cor = "cinza" # Default se sem config ou sem compra
        
        if ultima_compra_data:
            if isinstance(ultima_compra_data, str):
                ultima_compra_data = parse_date(ultima_compra_data)
            
            if ultima_compra_data:
                uc_date = ultima_compra_data.date() if isinstance(ultima_compra_data, datetime) else ultima_compra_data
                hoje_date = hoje.date()
                
                delta = (hoje_date - uc_date).days
                dias_sem_comprar = delta if delta > 0 else 0
                
                if periodo_em_dias > 0:
                    if dias_sem_comprar <= 60:
                        status_cor = "verde"
                    elif dias_sem_comprar <= 90:
                        status_cor = "amarelo"
                    else:
                        status_cor = "vermelho"
                    previsao_data = uc_date + dt_mod.timedelta(days=periodo_em_dias)
                else:
                    status_cor = "cinza" # Sem periodo configurado
            
        if not ultima_compra_data:
            status_cor = "cinza"
            
        grupo_ordem = 3
        if ativo:
            if ultima_compra_data:
                grupo_ordem = 1
            else:
                grupo_ordem = 2
                
        # Only use date for sorting to avoid mix of date and datetime
        sort_val = previsao_data if previsao_data else dt_mod.date(9999, 12, 31)
        if isinstance(sort_val, datetime):
            sort_val = sort_val.date()
        
        resultados.append({
            "grupo_ordem": grupo_ordem,
            "sort_date": sort_val,
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
            "vendedor": vendedor,
            "previsao_data_raw": previsao_data # Mantido para filtro
        })
        
    resultados.sort(key=lambda x: (x["grupo_ordem"], x["sort_date"]))
    return resultados

@router.get("/")
def get_captacao_pedidos(db: Session = Depends(get_db)):
    try:
        resultados = _get_captacao_data(db)
        # Remove raw field
        for r in resultados:
            r.pop("previsao_data_raw", None)
        return resultados
    except Exception as e:
        print(f"Erro detalhado captacao: {str(e)}")
        raise e

@router.get("/previsao-semanal")
def get_previsao_semanal(db: Session = Depends(get_db)):
    try:
        resultados = _get_captacao_data(db)
        
        import datetime as dt_mod
        hoje = dt_mod.date.today()
        # Encontra a segunda-feira da semana atual (0 = Monday, 6 = Sunday)
        start_of_week = hoje - dt_mod.timedelta(days=hoje.weekday())
        end_of_week = start_of_week + dt_mod.timedelta(days=6)
        
        vendedores_dict = {}
        
        for r in resultados:
            if not r["ativo"]:
                continue
                
            prev_raw = r.get("previsao_data_raw")
            if not prev_raw:
                continue
                
            prev_date = prev_raw.date() if isinstance(prev_raw, datetime) else prev_raw
            
            # Checa se a previsão cai na semana atual OU se o cliente está atrasado (previsão no passado) e deveria comprar logo
            # Se for estritamente a semana atual: 
            if start_of_week <= prev_date <= end_of_week:
                vendedor = r["vendedor"]
                if vendedor not in vendedores_dict:
                    vendedores_dict[vendedor] = []
                
                vendedor_item = r.copy()
                vendedor_item.pop("previsao_data_raw", None)
                vendedor_item.pop("sort_date", None)
                vendedores_dict[vendedor].append(vendedor_item)
                
        # Converte para uma lista mais amigável
        agrupado = [
            {
                "vendedor": v,
                "clientes": sorted(clientes, key=lambda c: c["cliente"])
            }
            for v, clientes in vendedores_dict.items()
        ]
        
        # Ordena por nome do vendedor
        agrupado.sort(key=lambda x: x["vendedor"])
        
        return {
            "semana_inicio": start_of_week.strftime('%d/%m/%Y'),
            "semana_fim": end_of_week.strftime('%d/%m/%Y'),
            "dados": agrupado
        }
        
    except Exception as e:
        print(f"Erro detalhado previsao semanal: {str(e)}")
        raise e
