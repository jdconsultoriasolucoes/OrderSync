import os

content = """
@router.get('/gerencial3')
def get_relatorio_gerencial3(
    codigo_cliente: Optional[str] = Query(None),
    cnpj_cpf: Optional[str] = Query(None),
    nome_cliente: Optional[str] = Query(None),
    vendedor: Optional[str] = Query(None),
    filial: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    municipio: Optional[str] = Query(None),
    rota_geral: Optional[str] = Query(None),
    rota_aproximacao: Optional[str] = Query(None),
    status_cadastro: Optional[str] = Query(None),
    tipo_entrega: Optional[str] = Query(None),
    meses: int = Query(12),
    db: Session = Depends(get_db)
):
    query_str = '''
        SELECT 
            c.cadastro_codigo_da_empresa AS codigo_cliente,
            c.cadastro_nome_cliente AS cliente,
            c.ultimas_compras_previsao_proxima AS previsao_proxima_compra,
            TO_CHAR(DATE_TRUNC('month', p.created_at), 'YYYY-MM') AS mes_ano,
            SUM(COALESCE(pb.peso_liquido, 0)) AS peso,
            SUM(p.total_pedido) AS valor,
            MAX(p.created_at) AS data_ultima_compra_mes
        FROM public.tb_pedidos p
        JOIN public.t_cadastro_cliente_v2 c ON p.codigo_cliente = c.cadastro_codigo_da_empresa
        LEFT JOIN (
            SELECT i.id_pedido, SUM(i.quantidade * COALESCE(CAST(pr.peso AS FLOAT), 0)) as peso_liquido
            FROM public.tb_pedidos_itens i
            LEFT JOIN public.t_cadastro_produto_v2 pr ON pr.codigo_supra = i.codigo
            GROUP BY i.id_pedido
        ) pb ON pb.id_pedido = p.id_pedido
        LEFT JOIN public.tb_tabela_preco tb_preco ON p.tabela_preco_id = tb_preco.id_tabela
        WHERE p.created_at >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '{meses_str} months'
          AND p.status != 'Cancelado'
    '''
    
    params = {}
    
    if codigo_cliente:
        query_str += " AND c.cadastro_codigo_da_empresa::text ILIKE :codigo_cliente"
        params['codigo_cliente'] = f"%{codigo_cliente}%"
        
    if cnpj_cpf:
        query_str += " AND (c.cadastro_cnpj ILIKE :cnpj_cpf OR c.cadastro_cpf ILIKE :cnpj_cpf)"
        params['cnpj_cpf'] = f"%{cnpj_cpf}%"
        
    if nome_cliente:
        query_str += " AND c.cadastro_nome_cliente ILIKE :nome_cliente"
        params['nome_cliente'] = f"%{nome_cliente}%"
        
    if vendedor:
        query_str += " AND c.elaboracao_vendedor = :vendedor"
        params['vendedor'] = vendedor

    if filial:
        query_str += " AND p.fornecedor = :filial"
        params['filial'] = filial
        
    if categoria:
        if categoria.upper() == 'INSUMOS':
            query_str += " AND tb_preco.nome_tabela ILIKE '%INSUMOS%'"
        elif categoria.upper() == 'PET':
            query_str += " AND tb_preco.nome_tabela ILIKE '%PET%'"

    if municipio:
        query_str += " AND COALESCE(c.faturamento_municipio, c.entrega_municipio) = :municipio"
        params['municipio'] = municipio

    if rota_geral:
        query_str += " AND c.entrega_rota_principal ILIKE :rota_geral"
        params['rota_geral'] = f"%{rota_geral}%"

    if rota_aproximacao:
        query_str += " AND c.entrega_rota_aproximacao ILIKE :rota_aproximacao"
        params['rota_aproximacao'] = f"%{rota_aproximacao}%"

    if status_cadastro:
        query_str += " AND c.cadastro_status_cadastro = :status_cadastro"
        params['status_cadastro'] = status_cadastro
        
    if tipo_entrega:
        query_str += " AND c.faturamento_tipo_entrega = :tipo_entrega"
        params['tipo_entrega'] = tipo_entrega
        
    query_str += '''
        GROUP BY 1, 2, 3, 4
        ORDER BY c.cadastro_nome_cliente, mes_ano
    '''
    
    query_str = query_str.replace('{meses_str}', str(meses - 1))
    
    rows = db.execute(text(query_str), params).mappings().all()
    
    data = {}
    for r in rows:
        cod = r['codigo_cliente']
        if not cod:
            continue
        if cod not in data:
            data[cod] = {
                'codigo_cliente': cod,
                'cliente': r['cliente'],
                'previsao_proxima_compra': r['previsao_proxima_compra'],
                'data_ultima_compra_geral': None,
                'meses': {}
            }
        data[cod]['meses'][r['mes_ano']] = {
            'peso': float(r['peso'] or 0),
            'valor': float(r['valor'] or 0)
        }
        dt_mes = r['data_ultima_compra_mes']
        if dt_mes:
            # Need to compare datetime correctly
            current_max = data[cod]['data_ultima_compra_geral']
            if not current_max or dt_mes > current_max:
                data[cod]['data_ultima_compra_geral'] = dt_mes
                
    return list(data.values())
"""

with open("e:/OrderSync/backend/routers/relatorios.py", "a", encoding="utf-8") as f:
    f.write(content)
