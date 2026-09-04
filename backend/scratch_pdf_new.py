# This scratch file will contain the new functions to append to the service.

def gerar_pdf_romaneio_novo(db, carga_id: int) -> bytes:
    buffer = io.BytesIO()
    pagesize = A4
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize
    
    # 1. Fetch Carga
    sql_carga = text("SELECT * FROM tb_cargas WHERE id = :cid")
    carga = db.execute(sql_carga, {"cid": carga_id}).mappings().first()
    if not carga: return None

    data_str = carga['data_carregamento'].strftime('%d/%m/%Y') if carga['data_carregamento'] else "___/___/___"
    
    y = _draw_header(c, width, height, "Rota de Entrega - Em Bloco", f"Carga #{carga['numero_carga']} | Data: {data_str}")
    
    # 2. Fetch Orders
    sql_pedidos = text("""
        SELECT p.id_pedido, p.cliente, c.entrega_municipio, c.cadastro_nome_fantasia,
               c.entrega_endereco, c.entrega_bairro, c.entrega_estado, c.entrega_cep,
               c.recebimento_celular, c.recebimento_nome
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
        LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
        WHERE cp.id_carga = :cid
    """)
    pedidos = db.execute(sql_pedidos, {"cid": carga_id}).mappings().all()
    
    for p in pedidos:
        if y < 8 * cm:
            c.showPage()
            y = _draw_header(c, width, height, "Rota de Entrega - Em Bloco", f"Carga #{carga['numero_carga']} | Data: {data_str}")
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(SUPRA_TEXT)
        fantasia = f" ({p['cadastro_nome_fantasia']})" if p.get('cadastro_nome_fantasia') else ""
        c.drawString(1.0*cm, y, f"[Pedido #{p['id_pedido']}] - Cliente: {p['cliente']}{fantasia}")
        y -= 0.5*cm
        c.setFont("Helvetica", 8)
        endereco = f"Endereço: {p['entrega_endereco'] or ''} - {p['entrega_bairro'] or ''}, {p['entrega_municipio'] or ''}/{p['entrega_estado'] or ''} - CEP: {p['entrega_cep'] or ''}"
        c.drawString(1.0*cm, y, endereco)
        y -= 0.4*cm
        contato = f"Contato: {p['recebimento_celular'] or ''} - Falar com {p['recebimento_nome'] or ''}"
        c.drawString(1.0*cm, y, contato)
        y -= 0.5*cm
        
        # Fetch items
        sql_itens = text("""
            SELECT i.codigo, prod.nome_produto as nome, i.quantidade, prod.unidade
            FROM tb_pedidos_itens i
            LEFT JOIN t_cadastro_produto_v2 prod ON prod.codigo_supra = i.codigo
            WHERE i.id_pedido = :pid
        """)
        itens = db.execute(sql_itens, {"pid": p['id_pedido']}).mappings().all()
        
        data = [["Cód", "Produto", "Qtd", "Unid", "Observações"]]
        for i in itens:
            data.append([str(i['codigo']), str(i['nome'] or ''), _br_number(i['quantidade'], 0), str(i['unidade'] or ''), ""])
        
        t = Table(data, colWidths=[1.5*cm, 8.5*cm, 2*cm, 1.5*cm, 5.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), SUPRA_BAR),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 4),
            ('BACKGROUND', (0,1), (-1,-1), SUPRA_BG_LIGHT),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 7)
        ]))
        tw, th = t.wrap(width, height)
        t.drawOn(c, 1.0*cm, y - th)
        y -= (th + 0.5*cm)
        
        c.setFont("Helvetica", 8)
        c.drawString(1.0*cm, y, "Assinatura do Recebedor: _____________________________________________   Data/Hora: ___/___/___ às ___:___")
        y -= 1.0*cm
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def gerar_pdf_resumo_produtos_novo(db, carga_id: int) -> bytes:
    buffer = io.BytesIO()
    pagesize = A4
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize
    
    sql_carga = text("SELECT * FROM tb_cargas WHERE id = :cid")
    carga = db.execute(sql_carga, {"cid": carga_id}).mappings().first()
    if not carga: return None

    data_str = carga['data_carregamento'].strftime('%d/%m/%Y') if carga['data_carregamento'] else "___/___/___"
    y = _draw_header(c, width, height, "Resumo de Produtos", f"Carga #{carga['numero_carga']} | Data: {data_str}")
    
    sql_itens = text("""
        SELECT i.codigo, prod.nome_produto as nome, SUM(i.quantidade) as qtd, prod.unidade
        FROM tb_cargas_pedidos cp
        JOIN tb_pedidos_itens i ON cp.numero_pedido = i.id_pedido::text
        LEFT JOIN t_cadastro_produto_v2 prod ON prod.codigo_supra = i.codigo
        WHERE cp.id_carga = :cid
        GROUP BY i.codigo, prod.nome_produto, prod.unidade
        ORDER BY prod.nome_produto
    """)
    itens = db.execute(sql_itens, {"cid": carga_id}).mappings().all()
    
    sql_pedidos = text("SELECT count(*) as qtd FROM tb_cargas_pedidos WHERE id_carga = :cid")
    qtd_pedidos = db.execute(sql_pedidos, {"cid": carga_id}).scalar()
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(SUPRA_TEXT)
    c.drawString(1.0*cm, y, f"Total de Pedidos nesta Carga: {qtd_pedidos}")
    y -= 0.6*cm
    
    data = [["Conferido", "Cód", "Descrição do Produto", "Quantidade Total", "Unid"]]
    for i in itens:
        data.append(["[   ]", str(i['codigo']), str(i['nome'] or ''), _br_number(i['qtd'], 0), str(i['unidade'] or '')])
    
    t = Table(data, colWidths=[2.5*cm, 2*cm, 9.5*cm, 3.5*cm, 1.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SUPRA_BAR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (3,0), (3,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), SUPRA_BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8)
    ]))
    tw, th = t.wrap(width, height)
    t.drawOn(c, 1.0*cm, y - th)
    y -= (th + 1.0*cm)
    
    # Assinaturas
    c.setFont("Helvetica", 9)
    c.drawString(1.0*cm, y, "Assinatura do Conferente: _____________________________________________")
    y -= 1.0*cm
    c.drawString(1.0*cm, y, "Assinatura do Motorista: _____________________________________________")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def gerar_pdf_romaneio_retirada_lote(db, retiradas_ids: list) -> bytes:
    buffer = io.BytesIO()
    pagesize = A4
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize
    
    if not retiradas_ids: return None

    sql_ret = text("""
        SELECT id, numero_retirada, data_retirada 
        FROM tb_retiradas 
        WHERE id = ANY(:ids)
        ORDER BY id DESC
    """)
    retiradas = db.execute(sql_ret, {"ids": retiradas_ids}).mappings().all()
    
    for ret in retiradas:
        data_str = ret['data_retirada'].strftime('%d/%m/%Y') if ret['data_retirada'] else "___/___/___"
        y = _draw_header(c, width, height, "Ordem de Retirada", f"Retirada #{ret['numero_retirada']} | Data: {data_str}")
        
        sql_pedidos = text("""
            SELECT p.id_pedido, p.cliente, c.entrega_endereco, c.entrega_bairro, c.entrega_municipio, c.entrega_estado, c.entrega_cep, c.recebimento_celular, c.recebimento_nome,
                   rp.retirada_nome_terceiro, rp.retirada_veiculo_placa, rp.retirada_veiculo_modelo
            FROM tb_retiradas_pedidos rp
            JOIN tb_pedidos p ON rp.numero_pedido = p.id_pedido::text
            LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
            WHERE rp.id_retirada = :rid
        """)
        pedidos = db.execute(sql_pedidos, {"rid": ret['id']}).mappings().all()
        
        motorista = 'Não informado'
        placa = 'Não informada'
        
        if pedidos:
            p = pedidos[0]
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(SUPRA_TEXT)
            c.drawString(1.0*cm, y, f"[Pedido #{p['id_pedido']}] - Cliente/Fornecedor: {p['cliente']}")
            y -= 0.5*cm
            c.setFont("Helvetica", 8)
            endereco = f"Endereço: {p['entrega_endereco'] or ''} - {p['entrega_bairro'] or ''}, {p['entrega_municipio'] or ''}/{p['entrega_estado'] or ''} - CEP: {p['entrega_cep'] or ''}"
            c.drawString(1.0*cm, y, endereco)
            y -= 0.4*cm
            contato = f"Contato: {p['recebimento_celular'] or ''} - Falar com {p['recebimento_nome'] or ''}"
            c.drawString(1.0*cm, y, contato)
            y -= 0.8*cm
            motorista = p['retirada_nome_terceiro'] or 'Não informado'
            placa = p['retirada_veiculo_placa'] or 'Não informada'
        else:
            c.setFont("Helvetica", 10)
            c.drawString(1.0*cm, y, "Nenhum pedido associado a esta retirada.")
            y -= 0.8*cm

        c.setFont("Helvetica-Bold", 9)
        c.drawString(1.0*cm, y, "DADOS DO VEÍCULO PARA RETIRADA:")
        y -= 0.4*cm
        c.setFont("Helvetica", 9)
        c.drawString(1.0*cm, y, f"Motorista Autorizado: {motorista}")
        y -= 0.4*cm
        c.drawString(1.0*cm, y, f"Placa do Veículo: {placa}")
        y -= 0.8*cm
        
        sql_itens = text("""
            SELECT i.codigo, prod.nome_produto as nome, i.quantidade, prod.unidade
            FROM tb_retiradas_pedidos rp
            JOIN tb_pedidos_itens i ON rp.numero_pedido = i.id_pedido::text
            LEFT JOIN t_cadastro_produto_v2 prod ON prod.codigo_supra = i.codigo
            WHERE rp.id_retirada = :rid
        """)
        itens = db.execute(sql_itens, {"rid": ret['id']}).mappings().all()
        
        data = [["Cód", "Descrição do Produto", "Qtd a Retirar", "Unid", "Conferido"]]
        for i in itens:
            data.append([str(i['codigo']), str(i['nome'] or ''), _br_number(i['quantidade'], 0), str(i['unidade'] or ''), "[    ]"])
        
        if len(data) > 1:
            t = Table(data, colWidths=[2*cm, 10*cm, 2.5*cm, 1.5*cm, 3*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), SUPRA_BAR),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('ALIGN', (2,0), (2,-1), 'CENTER'),
                ('ALIGN', (4,0), (4,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('BACKGROUND', (0,1), (-1,-1), SUPRA_BG_LIGHT),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 7)
            ]))
            tw, th = t.wrap(width, height)
            t.drawOn(c, 1.0*cm, y - th)
            y -= (th + 1.0*cm)
        
        c.setFont("Helvetica", 9)
        c.drawString(1.0*cm, y, "Assinatura de quem Separou: _____________________________________________")
        y -= 1.0*cm
        c.drawString(1.0*cm, y, f"Assinatura de quem Retirou ({motorista}): ________________________________________")
        y -= 1.0*cm
        c.drawString(1.0*cm, y, "Data/Hora da Saída: ___/___/___ às ___:___")
        
        c.showPage()
        
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def gerar_pdf_resumo_produtos_retirada_lote(db, retiradas_ids: list) -> bytes:
    buffer = io.BytesIO()
    pagesize = A4
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize
    
    if not retiradas_ids: return None

    y = _draw_header(c, width, height, "Resumo de Retiradas", f"Lote de {len(retiradas_ids)} retiradas")
    
    sql_itens = text("""
        SELECT i.codigo, prod.nome_produto as nome, SUM(i.quantidade) as qtd, prod.unidade
        FROM tb_retiradas_pedidos rp
        JOIN tb_pedidos_itens i ON rp.numero_pedido = i.id_pedido::text
        LEFT JOIN t_cadastro_produto_v2 prod ON prod.codigo_supra = i.codigo
        WHERE rp.id_retirada = ANY(:ids)
        GROUP BY i.codigo, prod.nome_produto, prod.unidade
        ORDER BY prod.nome_produto
    """)
    itens = db.execute(sql_itens, {"ids": retiradas_ids}).mappings().all()
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(SUPRA_TEXT)
    c.drawString(1.0*cm, y, f"Total de Retiradas Neste Lote: {len(retiradas_ids)}")
    y -= 0.6*cm
    
    data = [["Conferido", "Cód", "Descrição do Produto", "Quantidade Total", "Unid"]]
    for i in itens:
        data.append(["[   ]", str(i['codigo']), str(i['nome'] or ''), _br_number(i['qtd'], 0), str(i['unidade'] or '')])
    
    t = Table(data, colWidths=[2.5*cm, 2*cm, 9.5*cm, 3.5*cm, 1.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SUPRA_BAR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (3,0), (3,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), SUPRA_BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8)
    ]))
    tw, th = t.wrap(width, height)
    t.drawOn(c, 1.0*cm, y - th)
    y -= (th + 1.0*cm)
    
    # Assinaturas
    c.setFont("Helvetica", 9)
    c.drawString(1.0*cm, y, "Assinatura do Conferente: _____________________________________________")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
