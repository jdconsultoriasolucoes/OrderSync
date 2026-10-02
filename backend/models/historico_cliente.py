from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class HistoricoClienteAlteracoesModel(Base):
    __tablename__ = "historico_cliente_alteracoes"

    # For UUID, we can use String or PostgreSQL UUID type. We'll use UUID as text fallback
    # or the PostgreSQL type. Better to use text for portability or standard UUID.
    from sqlalchemy.dialects.postgresql import UUID
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    
    cliente_id = Column(BigInteger, ForeignKey("t_cadastro_cliente_v2.id"), nullable=False, index=True)
    usuario_id = Column(BigInteger, nullable=True) # Identifier of the user (from tb_usuarios if it existed)
    usuario_nome = Column(String(255), nullable=True)
    
    acao = Column(String(50), nullable=False) # 'UPDATE', 'INSERT'
    campos_alterados = Column(JSONB, nullable=True)
    dados_anteriores = Column(JSONB, nullable=True)
    dados_novos = Column(JSONB, nullable=True)
    
    origem = Column(String(100), nullable=True)
    motivo = Column(Text, nullable=True)
    
    criado_em = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), index=True)
