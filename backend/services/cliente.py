from typing import List, Optional
from sqlalchemy.orm import Session
from database import SessionLocal
from models.cliente_v2 import ClienteModelV2
from datetime import datetime

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _flat_to_nested(model: ClienteModelV2) -> dict:
    """
    Converts a flat ClienteModelV2 instance to the nested dictionary 
    expected by the frontend (ClienteCompleto).
    """
    if not model:
        return None

    return {
        "cadastrocliente": {
            "id": model.id,
            "codigo_da_empresa": model.cadastro_codigo_da_empresa,
            "ativo": model.cadastro_ativo,
            "tipo_pessoa": model.tipo_pessoa,
            "tipo_cliente": model.cadastro_tipo_cliente,
            "tipo_venda": model.cadastro_tipo_venda,
            "tipo_compra": model.cadastro_tipo_compra,
            "limite_credito": model.cadastro_limite_credito,
            "nome_cliente": model.cadastro_nome_cliente,
            "nome_fantasia": model.cadastro_nome_fantasia,
            "cnpj": model.cadastro_cnpj,
            "inscricao_estadual": model.cadastro_inscricao_estadual,
            "cpf": model.cadastro_cpf,
            "situacao": model.cadastro_situacao,
            "indicacao_cliente": model.cadastro_indicacao_cliente,
            "ramo_de_atividade": model.cadastro_ramo_de_atividade,
            "atividade_principal": model.cadastro_atividade_principal,
            "cadastro_markup": model.cadastro_markup,
        },
        "responsavel_compras": {
            "nome_responsavel": model.compras_nome_responsavel,
            "celular_responsavel": model.compras_celular_responsavel,
            "email_resposavel": model.compras_email_resposavel,
            "data_nascimento_resposavel": model.compras_data_nascimento_resposavel,
            "observacoes_responsavel": model.compras_observacoes_responsavel,
            "filial_resposavel": model.compras_filial_resposavel,
        },
        "endereco_faturamento": {
            "endereco_faturamento": model.faturamento_endereco,
            "bairro_faturamento": model.faturamento_bairro,
            "cep_faturamento": model.faturamento_cep,
            "localizacao_faturamento": model.faturamento_localizacao,
            "municipio_faturamento": model.faturamento_municipio,
            "estado_faturamento": model.faturamento_estado,
            "email_danfe_faturamento": model.faturamento_email_danfe,
        },
        "representante_legal": {
            "nome_RepresentanteLegal": model.legal_nome,
            "celular_RepresentanteLegal": model.legal_celular,
            "email_RepresentanteLegal": model.legal_email,
            "data_nascimento_RepresentanteLegal": model.legal_data_nascimento,
            "observacoes_RepresentanteLegal": model.legal_observacoes,
        },
        "endereco_entrega": {
            "endereco_EnderecoEntrega": model.entrega_endereco,
            "bairro_EnderecoEntrega": model.entrega_bairro,
            "cep_EnderecoEntrega": model.entrega_cep,
            "localizacao_EnderecoEntrega": model.entrega_localizacao,
            "municipio_EnderecoEntrega": model.entrega_municipio,
            "estado_EnderecoEntrega": model.entrega_estado,
            "rota_principal_EnderecoEntrega": model.entrega_rota_principal,
            "rota_de_aproximacao_EnderecoEntrega": model.entrega_rota_aproximacao,
            "observacao_motorista_EnderecoEntrega": model.entrega_observacao_motorista,
        },
        "responsavel_recebimento": {
            "nome_ResponsavelRecebimento": model.recebimento_nome,
            "celular_ResponsavelRecebimento": model.recebimento_celular,
            "email_ResponsavelRecebimento": model.recebimento_email,
            "data_nascimento_ResponsavelRecebimento": model.recebimento_data_nascimento,
            "observacoes_ResponsavelRecebimento": model.recebimento_observacoes,
        },
        "endereco_cobranca": {
            "endereco_EnderecoCobranca": model.cobranca_endereco,
            "bairro_EnderecoCobranca": model.cobranca_bairro,
            "cep_EnderecoCobranca": model.cobranca_cep,
            "localizacao_EnderecoCobranca": model.cobranca_localizacao,
            "municipio_EnderecoCobranca": model.cobranca_municipio,
            "estado_EnderecoCobranca": model.cobranca_estado,
        },
        "responsavel_cobranca": {
            "nome_ResponsavelCobranca": model.cobranca_resp_nome,
            "celular_ResponsavelCobranca": model.cobranca_resp_celular,
            "email_ResponsavelCobranca": model.cobranca_resp_email,
            "data_nascimento_ResponsavelCobranca": model.cobranca_resp_data_nascimento,
            "observacoes_ResponsavelCobranca": model.cobranca_resp_observacoes,
        },
        "dados_ultimas_compras": {
            "numero_danfe_Compras": model.ultimas_compras_numero_danfe,
            "emissao_Compras": model.ultimas_compras_emissao,
            "valor_total_Compras": model.ultimas_compras_valor_total,
            "valor_frete_Compras": model.ultimas_compras_valor_frete,
            "valor_frete_padrao_Compras": model.ultimas_compras_valor_frete_padrao,
            "valor_ultimo_frete_to_Compras": model.ultimas_compras_valor_ultimo_frete,
            "lista_tabela_Compras": model.ultimas_compras_lista_tabela,
            "condicoes_pagamento_Compras": model.ultimas_compras_condicoes_pagamento,
            "cliente_calcula_st_Compras": model.ultimas_compras_cliente_calcula_st,
            "prazo_medio_compra_Compras": model.ultimas_compras_prazo_medio,
            "previsao_proxima_compra_Compras": model.ultimas_compras_previsao_proxima,
        },
         "observacoes_nao_compra": {
            "observacoes_Compras": model.obs_nao_compra_observacoes,
        },
        "dados_elaboracao_cadastro": {
            "classificacao_ElaboracaoCadastro": model.elaboracao_classificacao,
            "tipo_venda_prazo_ou_vista_ElaboracaoCadastro": model.elaboracao_tipo_venda,
            "limite_credito_ElaboracaoCadastro": model.elaboracao_limite_credito,
            "data_vencimento_ElaboracaoCadastro": model.elaboracao_data_vencimento,
        },
        "grupo_economico": {
            "codigo_ElaboracaoCadastro": model.grupo_economico_codigo,
            "nome_empresarial_ElaboracaoCadastro": model.grupo_economico_nome,
        },
        "referencia_comercial": {
            "empresa_ElaboracaoCadastro": model.ref_comercial_empresa,
            "cidade_ElaboracaoCadastro": model.ref_comercial_cidade,
            "telefone_ElaboracaoCadastro": model.ref_comercial_telefone,
            "contato_ElaboracaoCadastro": model.ref_comercial_contato,
        },
        "referencia_bancaria": {
            "banco_ElaboracaoCadastro": model.ref_bancaria_banco,
            "agencia_ElaboracaoCadastro": model.ref_bancaria_agencia,
            "conta_corrente_ElaboracaoCadastro": model.ref_bancaria_conta,
        },
        "bem_imovel": {
            "imovel_ElaboracaoCadastro": model.bem_imovel_imovel,
            "localizacao_ElaboracaoCadastro": model.bem_imovel_localizacao,
            "area_ElaboracaoCadastro": model.bem_imovel_area,
            "valor_ElaboracaoCadastro": model.bem_imovel_valor,
            "hipotecado_ElaboracaoCadastro": model.bem_imovel_hipotecado,
        },
        "bem_movel": {
            "marca_ElaboracaoCadastro": model.bem_movel_marca,
            "modelo_ElaboracaoCadastro": model.bem_movel_modelo,
            "alienado_ElaboracaoCadastro": model.bem_movel_alienado,
        },
        "plantel_animal": {
            "especie_ElaboracaoCadastro": model.animal_especie,
            "numero_de_animais_ElaboracaoCadastro": model.animal_numero,
            "consumo_diario_ElaboracaoCadastro": model.animal_consumo_diario,
            "consumo_mensal_ElaboracaoCadastro": model.animal_consumo_mensal,
        },
        "supervisores": {
            "codigo_insumo_ElaboracaoCadastro": model.supervisor_codigo_insumo,
            "nome_insumos_ElaboracaoCadastro": model.supervisor_nome_insumo,
            "codigo_pet_ElaboracaoCadastro": model.supervisor_codigo_pet,
            "nome_pet_ElaboracaoCadastro": model.supervisor_nome_pet,
        },
        "comissao_dispet": {
            "insumos_ElaboracaoCadastro": model.comissao_insumos,
            "pet_ElaboracaoCadastro": model.comissao_pet,
            "observacoes_ElaboracaoCadastro": model.comissao_observacoes,
        }
    }

def _nested_to_flat(data: dict) -> ClienteModelV2:
    """
    Converts the nested dictionary from frontend (ClienteCompleto) 
    to a flat ClienteModelV2 instance for the database.
    """
    c = data.get("cadastrocliente", {})
    rc = data.get("responsavel_compras", {})
    ef = data.get("endereco_faturamento", {})
    rl = data.get("representante_legal", {})
    ee = data.get("endereco_entrega", {})
    rr = data.get("responsavel_recebimento", {})
    ec = data.get("endereco_cobranca", {})
    r_cob = data.get("responsavel_cobranca", {})
    uc = data.get("dados_ultimas_compras", {})
    onc = data.get("observacoes_nao_compra", {})
    dec = data.get("dados_elaboracao_cadastro", {})
    ge = data.get("grupo_economico", {})
    rcom = data.get("referencia_comercial", {})
    rb = data.get("referencia_bancaria", {})
    bi = data.get("bem_imovel", {})
    bm = data.get("bem_movel", {})
    pa = data.get("plantel_animal", {})
    sup = data.get("supervisores", {})
    cd = data.get("comissao_dispet", {})

    model = ClienteModelV2()
    
    # ID
    if c.get("id"):
        model.id = c.get("id")
    # If not present, we do NOT set model.id, so it remains unset/default (Sequence trigger)

    # 1. Cadastro
    model.cadastro_codigo_da_empresa = c.get("codigo_da_empresa")
    model.cadastro_ativo = c.get("ativo")
    model.tipo_pessoa = c.get("tipo_pessoa")
    model.cadastro_markup = c.get("cadastro_markup")
    model.cadastro_tipo_cliente = c.get("tipo_cliente")
    model.cadastro_tipo_venda = c.get("tipo_venda")
    model.cadastro_tipo_compra = c.get("tipo_compra")
    model.cadastro_limite_credito = c.get("limite_credito")
    model.cadastro_nome_cliente = c.get("nome_cliente")
    model.cadastro_nome_fantasia = c.get("nome_fantasia")
    model.cadastro_cnpj = c.get("cnpj")
    model.cadastro_inscricao_estadual = c.get("inscricao_estadual")
    model.cadastro_cpf = c.get("cpf")
    model.cadastro_situacao = c.get("situacao")
    model.cadastro_indicacao_cliente = c.get("indicacao_cliente")
    model.cadastro_ramo_de_atividade = c.get("ramo_de_atividade")
    model.cadastro_atividade_principal = c.get("atividade_principal")

    # 2. Responsavel Compras
    model.compras_nome_responsavel = rc.get("nome_responsavel")
    model.compras_celular_responsavel = rc.get("celular_responsavel")
    model.compras_email_resposavel = rc.get("email_resposavel")
    model.compras_data_nascimento_resposavel = rc.get("data_nascimento_resposavel")
    model.compras_observacoes_responsavel = rc.get("observacoes_responsavel")
    model.compras_filial_resposavel = rc.get("filial_resposavel")

    # 3. Faturamento
    model.faturamento_endereco = ef.get("endereco_faturamento")
    model.faturamento_bairro = ef.get("bairro_faturamento")
    model.faturamento_cep = ef.get("cep_faturamento")
    model.faturamento_localizacao = ef.get("localizacao_faturamento")
    model.faturamento_municipio = ef.get("municipio_faturamento")
    model.faturamento_estado = ef.get("estado_faturamento")
    model.faturamento_email_danfe = ef.get("email_danfe_faturamento")

    # 4. Representante Legal
    model.legal_nome = rl.get("nome_RepresentanteLegal")
    model.legal_celular = rl.get("celular_RepresentanteLegal")
    model.legal_email = rl.get("email_RepresentanteLegal")
    model.legal_data_nascimento = rl.get("data_nascimento_RepresentanteLegal")
    model.legal_observacoes = rl.get("observacoes_RepresentanteLegal")

    # 5. Entrega
    model.entrega_endereco = ee.get("endereco_EnderecoEntrega")
    model.entrega_bairro = ee.get("bairro_EnderecoEntrega")
    model.entrega_cep = ee.get("cep_EnderecoEntrega")
    model.entrega_localizacao = ee.get("localizacao_EnderecoEntrega")
    model.entrega_municipio = ee.get("municipio_EnderecoEntrega")
    model.entrega_estado = ee.get("estado_EnderecoEntrega")
    model.entrega_rota_principal = ee.get("rota_principal_EnderecoEntrega")
    model.entrega_rota_aproximacao = ee.get("rota_de_aproximacao_EnderecoEntrega")
    model.entrega_observacao_motorista = ee.get("observacao_motorista_EnderecoEntrega")

    # 6. Recebimento
    model.recebimento_nome = rr.get("nome_ResponsavelRecebimento")
    model.recebimento_celular = rr.get("celular_ResponsavelRecebimento")
    model.recebimento_email = rr.get("email_ResponsavelRecebimento")
    model.recebimento_data_nascimento = rr.get("data_nascimento_ResponsavelRecebimento")
    model.recebimento_observacoes = rr.get("observacoes_ResponsavelRecebimento")

    # 7. Cobranca
    model.cobranca_endereco = ec.get("endereco_EnderecoCobranca")
    model.cobranca_bairro = ec.get("bairro_EnderecoCobranca")
    model.cobranca_cep = ec.get("cep_EnderecoCobranca")
    model.cobranca_localizacao = ec.get("localizacao_EnderecoCobranca")
    model.cobranca_municipio = ec.get("municipio_EnderecoCobranca")
    model.cobranca_estado = ec.get("estado_EnderecoCobranca")

    # 8. Resp Cobranca
    model.cobranca_resp_nome = r_cob.get("nome_ResponsavelCobranca")
    model.cobranca_resp_celular = r_cob.get("celular_ResponsavelCobranca")
    model.cobranca_resp_email = r_cob.get("email_ResponsavelCobranca")
    model.cobranca_resp_data_nascimento = r_cob.get("data_nascimento_ResponsavelCobranca")
    model.cobranca_resp_observacoes = r_cob.get("observacoes_ResponsavelCobranca")

    # 9. Ultimas Compras
    model.ultimas_compras_numero_danfe = uc.get("numero_danfe_Compras")
    model.ultimas_compras_emissao = uc.get("emissao_Compras")
    model.ultimas_compras_valor_total = uc.get("valor_total_Compras")
    model.ultimas_compras_valor_frete = uc.get("valor_frete_Compras")
    model.ultimas_compras_valor_frete_padrao = uc.get("valor_frete_padrao_Compras")
    model.ultimas_compras_valor_ultimo_frete = uc.get("valor_ultimo_frete_to_Compras")
    model.ultimas_compras_lista_tabela = uc.get("lista_tabela_Compras")
    model.ultimas_compras_condicoes_pagamento = uc.get("condicoes_pagamento_Compras")
    model.ultimas_compras_cliente_calcula_st = uc.get("cliente_calcula_st_Compras")
    model.ultimas_compras_prazo_medio = uc.get("prazo_medio_compra_Compras")
    model.ultimas_compras_previsao_proxima = uc.get("previsao_proxima_compra_Compras")

    # 10. Obs Nao Compra
    model.obs_nao_compra_observacoes = onc.get("observacoes_Compras")

    # 11. Elaboracao
    model.elaboracao_classificacao = dec.get("classificacao_ElaboracaoCadastro")
    model.elaboracao_tipo_venda = dec.get("tipo_venda_prazo_ou_vista_ElaboracaoCadastro")
    model.elaboracao_limite_credito = dec.get("limite_credito_ElaboracaoCadastro")
    model.elaboracao_data_vencimento = dec.get("data_vencimento_ElaboracaoCadastro")

    # 12. Grupo
    model.grupo_economico_codigo = ge.get("codigo_ElaboracaoCadastro")
    model.grupo_economico_nome = ge.get("nome_empresarial_ElaboracaoCadastro")
    
    # 13. Ref Comercial
    model.ref_comercial_empresa = rcom.get("empresa_ElaboracaoCadastro")
    model.ref_comercial_cidade = rcom.get("cidade_ElaboracaoCadastro")
    model.ref_comercial_telefone = rcom.get("telefone_ElaboracaoCadastro")
    model.ref_comercial_contato = rcom.get("contato_ElaboracaoCadastro")

    # 14. Ref Bancaria
    model.ref_bancaria_banco = rb.get("banco_ElaboracaoCadastro")
    model.ref_bancaria_agencia = rb.get("agencia_ElaboracaoCadastro")
    model.ref_bancaria_conta = rb.get("conta_corrente_ElaboracaoCadastro")

    # 15. Bem Imovel
    model.bem_imovel_imovel = bi.get("imovel_ElaboracaoCadastro")
    model.bem_imovel_localizacao = bi.get("localizacao_ElaboracaoCadastro")
    model.bem_imovel_area = bi.get("area_ElaboracaoCadastro")
    model.bem_imovel_valor = bi.get("valor_ElaboracaoCadastro")
    model.bem_imovel_hipotecado = bi.get("hipotecado_ElaboracaoCadastro")

    # 16. Bem Movel
    model.bem_movel_marca = bm.get("marca_ElaboracaoCadastro")
    model.bem_movel_modelo = bm.get("modelo_ElaboracaoCadastro")
    model.bem_movel_alienado = bm.get("alienado_ElaboracaoCadastro")

    # 17. Animal
    model.animal_especie = pa.get("especie_ElaboracaoCadastro")
    model.animal_numero = pa.get("numero_de_animais_ElaboracaoCadastro")
    model.animal_consumo_diario = pa.get("consumo_diario_ElaboracaoCadastro")
    model.animal_consumo_mensal = pa.get("consumo_mensal_ElaboracaoCadastro")

    # 18. Supervisor
    model.supervisor_codigo_insumo = sup.get("codigo_insumo_ElaboracaoCadastro")
    model.supervisor_nome_insumo = sup.get("nome_insumos_ElaboracaoCadastro")
    model.supervisor_codigo_pet = sup.get("codigo_pet_ElaboracaoCadastro")
    model.supervisor_nome_pet = sup.get("nome_pet_ElaboracaoCadastro")

    # 19. Comissao
    model.comissao_insumos = cd.get("insumos_ElaboracaoCadastro")
    model.comissao_pet = cd.get("pet_ElaboracaoCadastro")
    model.comissao_observacoes = cd.get("observacoes_ElaboracaoCadastro")

    # Meta
    model.data_atualizacao = datetime.now()
    model.data_criacao = datetime.now() # We are creating a new object effectively
    
    return model


def listar_clientes() -> List[dict]:
    db = SessionLocal()
    try:
        clientes = db.query(ClienteModelV2).all()
        return [_flat_to_nested(c) for c in clientes]
    finally:
        db.close()

def obter_cliente(cliente_id: int) -> dict:
    db = SessionLocal()
    try:
        cliente = db.query(ClienteModelV2).filter(ClienteModelV2.id == cliente_id).first()
        if cliente:
            return _flat_to_nested(cliente)
        return None
    finally:
        db.close()

def criar_cliente(cliente_data: dict) -> dict:
    db = SessionLocal()
    try:
        novo_cliente = _nested_to_flat(cliente_data)
        
        novo_cliente.data_criacao = datetime.now()
        db.add(novo_cliente)
        db.commit()
        db.refresh(novo_cliente)
        return _flat_to_nested(novo_cliente)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def atualizar_cliente(cliente_id: int, cliente_data: dict) -> dict:
    db = SessionLocal()
    try:
        cliente = db.query(ClienteModelV2).filter(ClienteModelV2.id == cliente_id).first()
        if not cliente:
            return None
        
        # Create a transient object with new data
        novos_dados = _nested_to_flat(cliente_data)
        
        # Update attributes on the persistent object
        for col in ClienteModelV2.__table__.columns:
            key = col.name
            if key == 'id' or key == 'data_criacao':
                continue
            
            new_val = getattr(novos_dados, key)
            if new_val is not None:
                setattr(cliente, key, new_val)
        
        cliente.data_atualizacao = datetime.now()
        db.commit()
        db.refresh(cliente)
        return _flat_to_nested(cliente)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def deletar_cliente(cliente_id: int) -> bool:
    db = SessionLocal()
    try:
        cliente = db.query(ClienteModelV2).filter(ClienteModelV2.id == cliente_id).first()
        if cliente:
            db.delete(cliente)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
