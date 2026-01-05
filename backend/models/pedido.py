from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, BigInteger, Text
from database import Base
from datetime import datetime

class PedidoModel(Base):
    __tablename__ = "tb_pedidos"

    # id_pedido defined below as 'id' mapping to 'id_pedido' column
    # Alias for compatibility if needed, but codebase uses id_pedido in SQL
    # However, standard ORM uses 'id'. Let's map 'id_pedido' to 'id' if possible or just use id_pedido.
    # To avoid confusion, let's map 'id' to 'id_pedido' if logical, but SQLAlchemy prefers exact names.
    # Let's use 'id' as the property name for id_pedido column to match my router code 'PedidoModel.id'.
    id = Column("id_pedido", BigInteger, primary_key=True, index=True)

    tabela_preco_id = Column(BigInteger) # FK implicit
    tabela_preco_nome = Column(String) # Snapshot do nome da tabela
    
    # Client Data (Denormalized or Link)
    codigo_cliente = Column(String) # Stored as string in SQL queries? "a.codigo_cliente". In DB it might be varchar.
    cliente = Column(String) # Nome do cliente
    # cliente_email = Column(String) # Email do cliente (snapshot?)
    
    # Contact
    contato_nome = Column(String)
    contato_email = Column(String)
    contato_fone = Column(String)

    # Values
    total_pedido = Column(Float)
    frete_total = Column(Float)
    peso_total_kg = Column(Float)
    
    # Status
    status = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    atualizado_em = Column(DateTime, onupdate=datetime.now)
    confirmado_em = Column(DateTime)
    cancelado_em = Column(DateTime)
    cancelado_motivo = Column(String)

    # Flags
    usar_valor_com_frete = Column(Boolean)
    link_enviado_em = Column(DateTime)
    
    # Fornecedor
    fornecedor = Column(String)


    # Extra fields mentioned in services/pedidos.py
    validade_ate = Column(DateTime)
    validade_dias = Column(Integer)
    observacoes = Column(Text)
    
    link_url = Column(String)
    link_primeiro_acesso_em = Column(DateTime)
    link_status = Column(String)
