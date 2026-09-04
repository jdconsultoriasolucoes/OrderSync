import sys
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import psycopg2
from psycopg2.extras import DictCursor

DB_URL = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync?sslmode=require"

SUPRA_BAR = colors.Color(0.78, 0.70, 0.60)
SUPRA_TEXT = colors.Color(0.1, 0.1, 0.1)
SUPRA_BG_LIGHT = colors.Color(0.95, 0.95, 0.95)

def _br_number(value, decimals=2, suffix=""):
    if value is None: value = 0
    try: value = float(value)
    except: value = 0.0
    fmt = f"{{:,.{decimals}f}}"
    s = fmt.format(value)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s + suffix

def _draw_header(c, width, height, title, subtitle=""):
    margin_x = 0.7 * cm
    margin_y = 0.5 * cm
    available_width = width - 2 * margin_x
    top_y = height - margin_y

    faixa_h = 1.0 * cm
    faixa_y = top_y - 0.2 * cm
    c.setFillColor(SUPRA_BAR)
    c.rect(margin_x, faixa_y - faixa_h, available_width, faixa_h, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x + 0.3 * cm, faixa_y - faixa_h + 0.3 * cm, title.upper())

    c.setFont("Helvetica", 9)
    c.drawRightString(width - margin_x - 0.2*cm, faixa_y - faixa_h + 0.55 * cm, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if subtitle:
        c.drawRightString(width - margin_x - 0.2*cm, faixa_y - faixa_h + 0.15 * cm, subtitle)

    return faixa_y - faixa_h - 0.5 * cm

def gerar_entregas_pdf(conn):
    file_path = os.path.abspath(r"e:\OrderSync\tmp\real_entregas.pdf")
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    
    with conn.cursor(cursor_factory=DictCursor) as cur:
        # Pega as 3 últimas cargas de entrega finalizadas que têm pedidos
        cur.execute("""
            SELECT id, numero_carga, data_carregamento 
            FROM tb_cargas 
            WHERE is_retirada = False AND is_historico = True 
            ORDER BY id DESC LIMIT 3
        """)
        cargas = cur.fetchall()
        
        for carga in cargas:
            carga_id = carga['id']
            data_str = carga['data_carregamento'].strftime('%d/%m/%Y') if carga['data_carregamento'] else "04/09/2026"
            
            y = _draw_header(c, width, height, "Rota de Entrega - Em Bloco", f"Carga #{carga['numero_carga']} | Data: {data_str}")
            
            # Pega pedidos da carga
            cur.execute("""
                SELECT p.id_pedido, p.cliente, c.entrega_municipio, c.cadastro_nome_fantasia,
                       c.entrega_endereco, c.entrega_bairro, c.entrega_estado, c.entrega_cep,
                       c.recebimento_celular, c.recebimento_nome
                FROM tb_cargas_pedidos cp
                JOIN tb_pedidos p ON cp.numero_pedido = p.id_pedido::text
                LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
                WHERE cp.id_carga = %s
            """, (carga_id,))
            pedidos = cur.fetchall()
            
            for p in pedidos:
                if y < 8 * cm:
                    c.showPage()
                    y = _draw_header(c, width, height, "Rota de Entrega - Em Bloco", f"Carga #{carga['numero_carga']} | Data: {data_str}")
                
                c.setFont("Helvetica-Bold", 10)
                c.setFillColor(SUPRA_TEXT)
                fantasia = f" ({p['cadastro_nome_fantasia']})" if p['cadastro_nome_fantasia'] else ""
                c.drawString(1.0*cm, y, f"[Pedido #{p['id_pedido']}] - Cliente: {p['cliente']}{fantasia}")
                y -= 0.5*cm
                c.setFont("Helvetica", 8)
                endereco = f"Endereço: {p['entrega_endereco'] or ''} - {p['entrega_bairro'] or ''}, {p['entrega_municipio'] or ''}/{p['entrega_estado'] or ''} - CEP: {p['entrega_cep'] or ''}"
                c.drawString(1.0*cm, y, endereco)
                y -= 0.4*cm
                contato = f"Contato: {p['recebimento_celular'] or ''} - Falar com {p['recebimento_nome'] or ''}"
                c.drawString(1.0*cm, y, contato)
                y -= 0.5*cm
                
                # Itens do pedido
                cur.execute("""
                    SELECT i.codigo, prod.nome_produto as nome, i.quantidade, prod.unidade
                    FROM tb_pedidos_itens i
                    LEFT JOIN t_cadastro_produto_v2 prod ON prod.codigo_supra = i.codigo
                    WHERE i.id_pedido = %s
                """, (p['id_pedido'],))
                itens = cur.fetchall()
                
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

def gerar_retiradas_pdf(conn):
    file_path = os.path.abspath(r"e:\OrderSync\tmp\real_retiradas.pdf")
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    
    with conn.cursor(cursor_factory=DictCursor) as cur:
        # Pega as 3 últimas retiradas
        cur.execute("""
            SELECT id, numero_retirada, data_retirada 
            FROM tb_retiradas 
            ORDER BY id DESC LIMIT 3
        """)
        retiradas = cur.fetchall()
        
        for ret in retiradas:
            data_str = ret['data_retirada'].strftime('%d/%m/%Y') if ret['data_retirada'] else "04/09/2026"
            
            y = _draw_header(c, width, height, "Ordem de Retirada", f"Retirada #{ret['numero_retirada']} | Data: {data_str}")
            
            # Pega pedidos dessa retirada
            cur.execute("""
                SELECT p.id_pedido, p.cliente, c.entrega_endereco, c.entrega_bairro, c.entrega_municipio, c.entrega_estado, c.entrega_cep, c.recebimento_celular, c.recebimento_nome,
                       rp.retirada_nome_terceiro, rp.retirada_veiculo_placa, rp.retirada_veiculo_modelo
                FROM tb_retiradas_pedidos rp
                JOIN tb_pedidos p ON rp.numero_pedido = p.id_pedido::text
                LEFT JOIN public.t_cadastro_cliente_v2 c ON c.cadastro_codigo_da_empresa::text = p.codigo_cliente
                WHERE rp.id_retirada = %s
            """, (ret['id'],))
            pedidos = cur.fetchall()
            
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
                motorista = 'Não informado'
                placa = 'Não informada'

            c.setFont("Helvetica-Bold", 9)
            c.drawString(1.0*cm, y, "DADOS DO VEÍCULO PARA RETIRADA:")
            y -= 0.4*cm
            c.setFont("Helvetica", 9)
            c.drawString(1.0*cm, y, f"Motorista Autorizado: {motorista}")
            y -= 0.4*cm
            c.drawString(1.0*cm, y, f"Placa do Veículo: {placa}")
            y -= 0.8*cm
            
            # Pega todos os itens dos pedidos desta retirada
            cur.execute("""
                SELECT i.codigo, prod.nome_produto as nome, i.quantidade, prod.unidade
                FROM tb_retiradas_pedidos rp
                JOIN tb_pedidos_itens i ON rp.numero_pedido = i.id_pedido::text
                LEFT JOIN t_cadastro_produto_v2 prod ON prod.codigo_supra = i.codigo
                WHERE rp.id_retirada = %s
            """, (ret['id'],))
            itens = cur.fetchall()
            
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

def gerar_resumo_pdf(conn):
    file_path = os.path.abspath(r"e:\OrderSync\tmp\real_resumo.pdf")
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    
    with conn.cursor(cursor_factory=DictCursor) as cur:
        # Pega a última carga de entrega finalizada para usar como exemplo de resumo
        cur.execute("""
            SELECT id, numero_carga, data_carregamento 
            FROM tb_cargas 
            WHERE is_retirada = False AND is_historico = True 
            ORDER BY id DESC LIMIT 1
        """)
        carga = cur.fetchone()
        
        if carga:
            data_str = carga['data_carregamento'].strftime('%d/%m/%Y') if carga['data_carregamento'] else "04/09/2026"
            y = _draw_header(c, width, height, "Resumo de Produtos", f"Carga #{carga['numero_carga']} | Data: {data_str}")
            
            # Pega itens de todos os pedidos desta carga
            cur.execute("""
                SELECT i.codigo, prod.nome_produto as nome, SUM(i.quantidade) as qtd, prod.unidade
                FROM tb_cargas_pedidos cp
                JOIN tb_pedidos_itens i ON cp.numero_pedido = i.id_pedido::text
                LEFT JOIN t_cadastro_produto_v2 prod ON prod.codigo_supra = i.codigo
                WHERE cp.id_carga = %s
                GROUP BY i.codigo, prod.nome_produto, prod.unidade
                ORDER BY prod.nome_produto
            """, (carga['id'],))
            itens = cur.fetchall()
            
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(SUPRA_TEXT)
            c.drawString(1.0*cm, y, f"Total de Pedidos nesta Carga: 3")
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
            
            c.showPage()
    c.save()

if __name__ == "__main__":
    conn = psycopg2.connect(DB_URL)
    gerar_entregas_pdf(conn)
    gerar_retiradas_pdf(conn)
    gerar_resumo_pdf(conn)
    conn.close()
    print("PDFs generated with real DB data.")
