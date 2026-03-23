from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.cliente_v2 import ClienteModelV2
from datetime import datetime
from typing import Optional
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
    clientes = db.query(ClienteModelV2).all()
    
    hoje = datetime.now()
    resultados = []
    
    for c in clientes:
        ativo = getattr(c, 'cadastro_ativo', False)
        if ativo is None: # handle potential nulls
            ativo = False
            
        codigo_cliente = c.cadastro_codigo_da_empresa or ""
        nome_cliente = c.cadastro_nome_cliente or ""
        nome_fantasia = c.cadastro_nome_fantasia or ""
        rota_geral = c.entrega_rota_principal or ""
        rota_aprox = c.entrega_rota_aproximacao or ""
        municipio = c.entrega_municipio or c.faturamento_municipio or ""
        
        ultima_compra_str = c.ultimas_compras_emissao or ""
        ultima_compra_data = parse_date(ultima_compra_str)
        
        periodo_str = c.cadastro_periodo_de_compra or ""
        periodo_em_dias = extract_days(periodo_str)
        
        dias_sem_comprar = 0
        previsao_data = None
        status_cor = "vermelho" # default for inactive or no info
        
        if ultima_compra_data:
            delta = (hoje - ultima_compra_data).days
            dias_sem_comprar = delta if delta > 0 else 0
            
            # Cor
            if dias_sem_comprar <= 60:
                status_cor = "verde"
            elif dias_sem_comprar <= 90:
                status_cor = "amarelo"
            else:
                status_cor = "vermelho"
                
            import datetime as dt
            previsao_data = ultima_compra_data + dt.timedelta(days=periodo_em_dias)
            
        else:
            # Sem compras
            status_cor = "vermelho"
            
        # Classificacao Customizada para o Sort
        # 1 = Ativos com previsão mais próxima (tem ultima_compra_data)
        # 2 = Ativos sem compras (ultima_compra_data is None mas ativo=True)
        # 3 = Inativos (ativo=False)
        
        grupo_ordem = 3
        if ativo:
            if ultima_compra_data:
                grupo_ordem = 1
            else:
                grupo_ordem = 2
                
        # Data limite para sort para tratar Nones
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
            "ativo": ativo
        })
        
    # Ordenar por grupo (1, 2, 3) e depois pela previsao da data ascendente
    resultados.sort(key=lambda x: (x["grupo_ordem"], x["sort_date"]))
    
    # Remover campos de sorting que nao precisaremos entregar no json (opcional, mas economiza banda)
    for res in resultados:
        res.pop('grupo_ordem', None)
        res.pop('sort_date', None)
        
    return resultados
