-- Migration: Auditoria Cadastral de Clientes
-- Objetivo: Criar tabela de histórico de alterações de clientes e índices associados.

CREATE TABLE IF NOT EXISTS public.historico_cliente_alteracoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id BIGINT NOT NULL,
    usuario_id BIGINT,
    usuario_nome VARCHAR(255),
    acao VARCHAR(50) NOT NULL, -- 'UPDATE', 'INSERT'
    campos_alterados JSONB,
    dados_anteriores JSONB,
    dados_novos JSONB,
    origem VARCHAR(100),
    motivo TEXT,
    criado_em TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historico_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES public.t_cadastro_cliente_v2(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_hist_cli_cliente_id ON public.historico_cliente_alteracoes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_hist_cli_criado_em ON public.historico_cliente_alteracoes(criado_em);
