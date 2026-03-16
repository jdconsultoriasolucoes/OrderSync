-- update_pedido_status.sql
-- Rode este script diretamente pela aba SQL do Render ou DBeaver para o banco de dados.

-- 1. Desativar todos os status existentes
UPDATE public.pedido_status SET ativo = FALSE;

-- 2. Inserir ou atualizar (Reativar) os 5 oficiais do fluxo
INSERT INTO public.pedido_status (codigo, rotulo, ordem, ativo)
VALUES 
    ('ORCAMENTO', 'Orçamento', 1, TRUE),
    ('PEDIDO', 'Pedido', 2, TRUE),
    ('FATURADO_SUPRA', 'Faturado Supra', 3, TRUE),
    ('FATURADO_DISPET', 'Faturado Dispet', 4, TRUE),
    ('CANCELADO', 'Cancelado', 5, TRUE)
ON CONFLICT (codigo) DO UPDATE 
SET rotulo = EXCLUDED.rotulo, 
    ordem = EXCLUDED.ordem, 
    ativo = TRUE;
