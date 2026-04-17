import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Dict, Any
from copy import deepcopy

from models.cliente_v2 import ClienteModelV2
from models.catalogo_referencias import CidadeSupervisorModel, MunicipioRotaModel, ReferenciasModel
from models.profile_config import ProfileConfigModel

logger = logging.getLogger("ordersync.services.sync_service")

def _normalize_string(s: str) -> str:
    """Helper simples para normalização primária (remoção de espaços) para evitar falhas silenciosas"""
    return s.strip() if s else ""

def safe_int_str(val) -> str:
    if val is None:
        return ""
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return ""
        return str(int(val))
    except (ValueError, TypeError):
        return str(val) if val else ""

def sync_cidade_supervisor(db: Session, municipio: str, data: CidadeSupervisorModel):
    """
    Quando o catálogo for atualizado, propague para os clientes daquela cidade.
    O match é feito na coluna faturamento_municipio.
    """
    if not municipio:
        return

    logger.info(f"Sincronizando CidadeSupervisor para o municipio: {municipio}")
    # Como o banco pode ter variações de case, usamos ilike
    query = db.query(ClienteModelV2).filter(ClienteModelV2.faturamento_municipio.ilike(municipio))
    
    rows_updated = query.update({
        ClienteModelV2.elaboracao_gerente_insumos: data.gerente_insumos or "",
        ClienteModelV2.elaboracao_gerente_pet: data.gerente_pet or "",
        ClienteModelV2.supervisor_codigo_insumo: safe_int_str(data.numero_supervisor_insumos),
        ClienteModelV2.supervisor_nome_insumo: data.nome_supervisor_insumos or "",
        ClienteModelV2.supervisor_codigo_pet: safe_int_str(data.numero_supervisor_pet),
        ClienteModelV2.supervisor_nome_pet: data.nome_supervisor_pet or ""
    }, synchronize_session=False)

    db.commit()
    logger.info(f"{rows_updated} registros de cliente atualizados (CidadeSupervisor).")

def sync_municipio_rota(db: Session, municipio: str, rota: str):
    """
    Atualiza a rota_principal na aba de Entrega dos clientes do município.
    """
    if not municipio:
        return
        
    logger.info(f"Sincronizando Rota para o município: {municipio}")
    query = db.query(ClienteModelV2).filter(ClienteModelV2.faturamento_municipio.ilike(municipio))
    
    rows_updated = query.update({
        ClienteModelV2.entrega_rota_principal: str(rota) if rota else ""
    }, synchronize_session=False)

    db.commit()
    logger.info(f"{rows_updated} registros de cliente atualizados (Rota).")

def sync_referencia_comercial(db: Session, empresa: str, ref_data: ReferenciasModel):
    """
    Atualiza telefone, cidade e contato no JSONB de Referências Comerciais de TODOS os clientes
    que possuam essa 'empresa' cadastrada no array jsonb de referencias_comerciais.
    """
    if not empresa:
        return
        
    logger.info(f"Sincronizando Referências Comerciais para a empresa: {empresa}")
    
    # Busca clientes que contenham essa empresa no array jsonb
    # No SQLAlchemy JSONB .contains() busca se o array root possui pelo menos esse sub-objeto
    clientes = db.query(ClienteModelV2).filter(
        ClienteModelV2.referencias_comerciais.contains([{"empresa_ElaboracaoCadastro": empresa}])
    ).all()
    
    updated_count = 0
    for cliente in clientes:
        # Cópia profunda para notificar SQLAlchemy da mudança no JSONB
        refs = deepcopy(cliente.referencias_comerciais)
        if not refs:
            continue
            
        modified = False
        for ref in refs:
            if ref.get("empresa_ElaboracaoCadastro") == empresa:
                ref["cidade_ElaboracaoCadastro"] = ref_data.cidade or ""
                ref["telefone_ElaboracaoCadastro"] = ref_data.telefone or ""
                ref["contato_ElaboracaoCadastro"] = ref_data.contato or ""
                modified = True
                
        if modified:
            cliente.referencias_comerciais = refs
            updated_count += 1
            
    db.commit()
    logger.info(f"{updated_count} clientes atualizados (Referências Comerciais).")

def sync_supervisores_base(db: Session, supervisor: Any):
    """
    Sincroniza quando a tabela MESTRA (tb_supervisores) for alterada.
    Se o nome/código do supervisor mudar, atualizamos todos os clientes que referenciam o CÓDIGO desse supervisor.
    """
    if not supervisor.codigo:
        logger.warning("Sincronização de supervisor ignorada: Código ausente.")
        return
        
    # Tentamos ser o mais resilientes possível no match do código
    try:
        cod_int = int(float(supervisor.codigo))
        cod_str_clean = str(cod_int)
    except:
        cod_str_clean = str(supervisor.codigo).strip()

    logger.info(f"Sincronizando Supervisor Base (Código: {cod_str_clean}) -> Novo Nome: {supervisor.supervisores}")
    
    # Busca clientes que tenham esse código exato, com .0 ou com espaços
    # Usamos or_ para cobrir variações comuns de exportação de Excel/CSV
    filter_cond = or_(
        func.trim(ClienteModelV2.supervisor_codigo_insumo) == cod_str_clean,
        func.trim(ClienteModelV2.supervisor_codigo_insumo) == f"{cod_str_clean}.0"
    )
    
    rows_insumo = db.query(ClienteModelV2).filter(filter_cond).update({
        ClienteModelV2.supervisor_nome_insumo: supervisor.supervisores or "",
        ClienteModelV2.supervisor_codigo_insumo: cod_str_clean  # Auto-correção para inteiro
    }, synchronize_session=False)
    
    filter_cond_pet = or_(
        func.trim(ClienteModelV2.supervisor_codigo_pet) == cod_str_clean,
        func.trim(ClienteModelV2.supervisor_codigo_pet) == f"{cod_str_clean}.0"
    )

    rows_pet = db.query(ClienteModelV2).filter(filter_cond_pet).update({
        ClienteModelV2.supervisor_nome_pet: supervisor.supervisores or "",
        ClienteModelV2.supervisor_codigo_pet: cod_str_clean  # Auto-correção para inteiro
    }, synchronize_session=False)

    db.commit()
    logger.info(f"Supervisor Base Sincronizado para {cod_str_clean}: {rows_insumo} insumos e {rows_pet} pet afetados.")

def sync_canal_venda(db: Session, canal: Any):
    """
    Sincroniza os canais de venda quando seus nomes base mudarem, se houver impacto direto.
    """
    pass # Espaço reservado, atualmente Canais não salvam ID relacional no cliente, apenas texto solto.

def sync_profile_comissao(db: Session):
    """
    Atualiza as strings de Comissão (Pet e Insumos) de TODOS os clientes no banco com base no Profile atual.
    """
    logger.info("Sincronizando Comissões de Perfil em Cascata...")
    config = db.query(ProfileConfigModel).first()
    
    if not config:
        logger.warning("Perfil Config não existe. Sincronização cancelada.")
        return
        
    text = ""
    if config.razao_social: 
        text += config.razao_social.upper()
    if config.codigo_representante:
        text += (" - CÓDIGO " if text else "CÓDIGO ") + config.codigo_representante
        
    rows_updated = db.query(ClienteModelV2).update({
        ClienteModelV2.comissao_insumos: text,
        ClienteModelV2.comissao_pet: text
    }, synchronize_session=False)

    db.commit()
    logger.info(f"{rows_updated} registros de cliente atualizados (Comissão Global).")
