-- ============================================================
-- Script: repair_tabela_preco_nome.sql
-- Objetivo: Popular o campo tabela_preco_nome em pedidos onde
--           o campo está NULL mas tabela_preco_id tem valor.
-- Gerado em: 2026-03-19
-- ============================================================

-- 1. Diagnóstico: quantos pedidos estão com tabela_preco_nome NULL
SELECT 
    COUNT(*) FILTER (WHERE tabela_preco_nome IS NULL AND tabela_preco_id IS NOT NULL) AS pedidos_sem_nome_com_id,
    COUNT(*) FILTER (WHERE tabela_preco_nome IS NULL AND tabela_preco_id IS NULL)     AS pedidos_sem_nome_sem_id,
    COUNT(*) FILTER (WHERE tabela_preco_nome IS NOT NULL)                             AS pedidos_com_nome,
    COUNT(*)                                                                          AS total
FROM public.tb_pedidos;

-- 2. Diagnóstico para o pedido 507 especificamente
SELECT 
    a.id_pedido,
    a.tabela_preco_id,
    a.tabela_preco_nome                               AS nome_na_tabela_pedidos,
    b.nome_tabela                                     AS nome_na_tabela_preco,
    COALESCE(a.tabela_preco_nome, b.nome_tabela)      AS nome_coalesce
FROM public.tb_pedidos a
LEFT JOIN public.tb_tabela_preco b ON a.tabela_preco_id = b.id_tabela
WHERE a.id_pedido = 507;

-- 3. Repair: atualiza tabela_preco_nome nos pedidos que têm tabela_preco_id
--    mas tabela_preco_nome está NULL (sem tocar nos que já têm nome).
-- IMPORTANTE: Rodar somente após confirmar o diagnóstico acima.
UPDATE public.tb_pedidos a
SET tabela_preco_nome = b.nome_tabela
FROM public.tb_tabela_preco b
WHERE a.tabela_preco_id = b.id_tabela
  AND (a.tabela_preco_nome IS NULL OR a.tabela_preco_nome = '');

-- 4. Validação pós-repair: deve mostrar 0 na coluna pedidos_sem_nome_com_id
SELECT 
    COUNT(*) FILTER (WHERE tabela_preco_nome IS NULL AND tabela_preco_id IS NOT NULL) AS pedidos_sem_nome_com_id,
    COUNT(*) FILTER (WHERE tabela_preco_nome IS NOT NULL)                             AS pedidos_com_nome,
    COUNT(*)                                                                          AS total
FROM public.tb_pedidos;
