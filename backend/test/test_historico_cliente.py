import pytest
from sqlalchemy import text
from datetime import datetime
from database import SessionLocal
from services.cliente import criar_cliente, atualizar_cliente
from models.cliente_v2 import ClienteModelV2
from models.pedido import PedidoModel
from models.historico_cliente import HistoricoClienteAlteracoesModel

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_auditoria_e_propagacao_pedidos(db_session):
    # 1. Cria cliente
    cliente_data = {
        "cadastrocliente": {
            "nome_cliente": "Cliente Teste Auditoria",
            "codigo_da_empresa": "999888",
            "cpf": "12345678901"
        },
        "_contexto_auditoria": {
            "usuario_id": 1,
            "usuario_nome": "Admin Teste",
            "origem": "teste_unitario"
        }
    }
    
    # Executa criação
    novo_cliente = criar_cliente(cliente_data)
    cliente_id = novo_cliente["cadastrocliente"]["id"]
    
    # 2. Cria pedidos para testar propagação (um aberto, um faturado)
    pedido_aberto = PedidoModel(
        codigo_cliente="999888",
        cliente="Cliente Teste Auditoria Antigo",
        status="Orçamento",
        total_pedido=100.0,
        usar_valor_com_frete=False,
        frete_total=0.0,
        peso_total_kg=10.0,
        calcula_st=False
    )
    pedido_faturado = PedidoModel(
        codigo_cliente="999888",
        cliente="Cliente Teste Auditoria Antigo",
        status="Faturado Supra",
        total_pedido=200.0,
        usar_valor_com_frete=False,
        frete_total=0.0,
        peso_total_kg=20.0,
        calcula_st=False
    )
    
    db_session.add(pedido_aberto)
    db_session.add(pedido_faturado)
    db_session.commit()
    db_session.refresh(pedido_aberto)
    db_session.refresh(pedido_faturado)
    
    id_aberto = pedido_aberto.id
    id_faturado = pedido_faturado.id

    # 3. Atualiza o cliente (simulando alteração cadastral)
    atualiza_data = {
        "cadastrocliente": {
            "id": cliente_id,
            "nome_cliente": "Cliente Teste Auditoria Novo",
            "codigo_da_empresa": "999888",
            "cpf": "12345678901"
        },
        "responsavel_compras": {
            "nome_responsavel": "Contato Novo"
        },
        "_contexto_auditoria": {
            "usuario_id": 1,
            "usuario_nome": "Admin Teste",
            "origem": "teste_unitario",
            "motivo_alteracao": "Correção de nome"
        }
    }
    
    atualizado = atualizar_cliente(cliente_id, atualiza_data)
    
    # a) Verifica registro do diff na tabela de log
    historico = db_session.query(HistoricoClienteAlteracoesModel).filter(
        HistoricoClienteAlteracoesModel.cliente_id == cliente_id,
        HistoricoClienteAlteracoesModel.acao == 'UPDATE'
    ).order_by(HistoricoClienteAlteracoesModel.criado_em.desc()).first()
    
    assert historico is not None, "Histórico de alteração não foi criado"
    assert "cadastro_nome_cliente" in historico.campos_alterados
    assert historico.dados_novos["cadastro_nome_cliente"] == "Cliente Teste Auditoria Novo"
    assert historico.origem == "teste_unitario"
    
    # b) Verifica propagação no pedido aberto
    db_session.refresh(pedido_aberto)
    assert pedido_aberto.cliente == "Cliente Teste Auditoria Novo"
    assert pedido_aberto.contato_nome == "Contato Novo"
    
    # c) Verifica preservação intacta do pedido faturado
    db_session.refresh(pedido_faturado)
    assert pedido_faturado.cliente == "Cliente Teste Auditoria Antigo", "Pedido faturado não deveria ter sido alterado!"

    # Cleanup
    db_session.execute(text("DELETE FROM tb_pedidos WHERE id_pedido IN (:id1, :id2)"), {"id1": id_aberto, "id2": id_faturado})
    db_session.execute(text("DELETE FROM historico_cliente_alteracoes WHERE cliente_id = :id"), {"id": cliente_id})
    db_session.execute(text("DELETE FROM t_cadastro_cliente_v2 WHERE id = :id"), {"id": cliente_id})
    db_session.commit()
