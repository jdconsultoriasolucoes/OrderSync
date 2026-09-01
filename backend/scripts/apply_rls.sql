-- ==========================================
-- PILAR 1: ROW-LEVEL SECURITY (RLS)
-- ==========================================
-- Este script habilita e configura as politicas de RLS (Row-Level Security)
-- no banco de dados, baseadas no id do tenant/usuario atual da sessao.

-- Habilita RLS nas tabelas sensiveis
ALTER TABLE tb_pedidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE tb_pedidos FORCE ROW LEVEL SECURITY;

ALTER TABLE tb_pedidos_itens ENABLE ROW LEVEL SECURITY;
ALTER TABLE tb_pedidos_itens FORCE ROW LEVEL SECURITY;

ALTER TABLE t_cadastro_cliente_v2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE t_cadastro_cliente_v2 FORCE ROW LEVEL SECURITY;

-- Remove politicas antigas se existirem (para permitir re-execucao)
DROP POLICY IF EXISTS tenant_isolation_policy ON tb_pedidos;
DROP POLICY IF EXISTS tenant_isolation_policy ON tb_pedidos_itens;
DROP POLICY IF EXISTS tenant_isolation_policy ON t_cadastro_cliente_v2;

-- Cria politicas para tb_pedidos
-- Assume-se que o current_user_id eh injetado na sessao (SET LOCAL app.current_user_id = '...');
-- e que a tabela tem uma coluna identificando o usuario dono, por exemplo, "vendedor" ou "user_id".
-- IMPORTANTE: Ajustar 'vendedor' para a coluna real que indica a posse do pedido.
CREATE POLICY tenant_isolation_policy ON tb_pedidos
    AS RESTRICTIVE
    FOR ALL
    USING (
        current_setting('app.current_user_id', true) IS NULL 
        OR current_setting('app.current_user_role', true) = 'admin'
        OR vendedor = current_setting('app.current_user_id', true)
    );

-- Politicas para tb_pedidos_itens
-- O ideal eh joinar com tb_pedidos ou ter o id do dono. 
CREATE POLICY tenant_isolation_policy ON tb_pedidos_itens
    AS RESTRICTIVE
    FOR ALL
    USING (
        current_setting('app.current_user_id', true) IS NULL 
        OR current_setting('app.current_user_role', true) = 'admin'
        OR pedido_id IN (
            SELECT id FROM tb_pedidos WHERE vendedor = current_setting('app.current_user_id', true)
        )
    );

-- Politicas para t_cadastro_cliente_v2
CREATE POLICY tenant_isolation_policy ON t_cadastro_cliente_v2
    AS RESTRICTIVE
    FOR ALL
    USING (
        current_setting('app.current_user_id', true) IS NULL 
        OR current_setting('app.current_user_role', true) = 'admin'
        -- Adicione aqui a logica para restringir clientes a vendedores especificos, se existir
        -- Ex: OR vendedor_id = current_setting('app.current_user_id', true)
    );

-- ==========================================
-- Fim do Script
-- ==========================================
