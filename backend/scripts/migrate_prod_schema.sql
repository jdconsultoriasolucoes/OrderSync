-- ============================================================
-- MIGRATION SCRIPT: Dev → Prod
-- Aplicar apenas na DATABASE DE PRODUÇÃO: db_ordersync
-- 
-- SEGURO: usa IF NOT EXISTS — nunca afeta colunas que já existem
-- NÃO move dados, apenas altera estrutura.
-- ============================================================

-- 1. Nova coluna adicionada durante sessões de Dev
--    Tela: Cadastro de Clientes → campo "Periodo de Compra"
ALTER TABLE public.t_cadastro_cliente_v2
  ADD COLUMN IF NOT EXISTS cadastro_periodo_de_compra VARCHAR;

-- ============================================================
-- VERIFICAÇÃO: rode esta query para confirmar a coluna existe
-- ============================================================
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 't_cadastro_cliente_v2'
-- AND column_name = 'cadastro_periodo_de_compra';
