-- Script para atualizar campos específicos de produtos PET
-- Origem: t_produto_supra | Destino: t_cadastro_produto_v2
-- Colunas: ncm, peso_liquido, peso_bruto, nome_produto, familia, filhos

UPDATE t_cadastro_produto_v2 v2
SET 
    ncm = s.ncm,
    peso_liquido = s.peso_liquido,
    peso_bruto = s.peso_bruto,
    nome_produto = s.nome_produto,
    familia = s.familia,
    -- 'filhos' é text na origem e integer no destino, tentamos converter.
    -- Se houver valores não numéricos, isso pode falhar.
    filhos = CASE 
        WHEN s.filhos ~ '^\d+$' THEN s.filhos::integer 
        ELSE NULL 
    END
FROM t_produto_supra s
WHERE v2.codigo_supra = s.codigo_supra
  AND s.tipo = 'PET';
