from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models.config_email_mensagem import ConfigEmailMensagem
from models.config_email_smtp import ConfigEmailSMTP
from models.cliente import ClienteModel  # seu modelo ORM real de cliente
from email.mime.application import MIMEApplication
from io import BytesIO

def get_cfg_mensagem(db: Session) -> ConfigEmailMensagem:
    cfg = (
        db.query(ConfigEmailMensagem)
        .filter(ConfigEmailMensagem.id == 1)
        .first()
    )
    if not cfg:
        raise HTTPException(
            status_code=500,
            detail="Configuração de mensagem de e-mail (config_email_mensagem.id=1) não encontrada."
        )
    return cfg


def get_cfg_smtp(db: Session) -> ConfigEmailSMTP:
    cfg = (
        db.query(ConfigEmailSMTP)
        .filter(ConfigEmailSMTP.id == 1)
        .first()
    )
    if not cfg:
        raise HTTPException(
            status_code=500,
            detail="Configuração SMTP (config_email_smtp.id=1) não encontrada."
        )
    return cfg


def gerar_pdf_pedido_bytes(pedido, itens, cliente) -> bytes:
    """
    Gera um PDF (em memória) com layout enxuto:
    - Cabeçalho com logo (opcional), título e data
    - Blocos: Cliente e Pedido
    - Tabela de itens (Código, Descrição, Qtd, Unit, Subtotal)
    - Totais (subtotal, frete, desconto, total)
    - Observações (se houver)
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.utils import ImageReader
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dependência 'reportlab' ausente: {e}")

    from io import BytesIO
    from datetime import datetime
    import os

    def brl(v: float) -> str:
        s = f"{(v or 0):,.2f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")

    def safe_float(x, default=0.0):
        try:
            return float(x or 0)
        except Exception:
            return default

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Margens e posição inicial
    x0 = 2 * cm
    xR = width - 2 * cm
    y = height - 2 * cm

    # ===== CABEÇALHO =====
    # Tenta desenhar o logo se existir (ajuste o caminho se preferir)
    possible_logos = [
        "./frontend/public/logo_ordersync.png",
        "./frontend/public/img/logo_ordersync.png",
        "./frontend/public/logo.png",
    ]
    logo_path = next((p for p in possible_logos if os.path.exists(p)), None)
    if logo_path:
        try:
            logo = ImageReader(logo_path)
            c.drawImage(logo, x0, y - 1.6*cm, width=3.2*cm, height=1.2*cm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(xR, y, f"Pedido #{getattr(pedido, 'id', '---')} - CONFIRMADO")
    y -= 0.6 * cm

    c.setFont("Helvetica", 9.5)
    c.drawRightString(xR, y, datetime.now().strftime("%d/%m/%Y %H:%M"))
    y -= 0.8 * cm

    c.setLineWidth(0.6)
    c.line(x0, y, xR, y)
    y -= 0.6 * cm

    # ===== BLOCO CLIENTE =====
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x0, y, "Cliente")
    y -= 0.5 * cm
    c.setFont("Helvetica", 10)

    cliente_nome = getattr(cliente, "nome", None) or getattr(cliente, "razao_social", None) or "---"
    cliente_cod = getattr(cliente, "codigo", None) or getattr(pedido, "codigo_cliente", None) or getattr(pedido, "cliente_codigo", None)
    cliente_email = getattr(cliente, "email", None) or getattr(cliente, "email_principal", None)

    c.drawString(x0, y, f"Nome: {cliente_nome}")
    if cliente_cod:
        c.drawRightString(xR, y, f"Código: {cliente_cod}")
    y -= 0.45 * cm
    if cliente_email:
        c.drawString(x0, y, f"E-mail: {cliente_email}")
        y -= 0.45 * cm

    y -= 0.2 * cm
    c.setLineWidth(0.3)
    c.line(x0, y, xR, y)
    y -= 0.5 * cm

    # ===== BLOCO PEDIDO =====
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x0, y, "Pedido")
    y -= 0.5 * cm
    c.setFont("Helvetica", 10)

    data_retirada = getattr(pedido, "data_retirada", None) or getattr(pedido, "data_entrega", None)
    usar_com_frete = getattr(pedido, "usar_valor_com_frete", None)
    peso_total = getattr(pedido, "peso_total_kg", None)

    if data_retirada:
        c.drawString(x0, y, f"Data de entrega/retirada: {data_retirada}")
        y -= 0.45 * cm
    if usar_com_frete is not None:
        c.drawString(x0, y, f"Usar valor com frete: {'Sim' if usar_com_frete else 'Não'}")
        y -= 0.45 * cm
    if peso_total is not None:
        c.drawString(x0, y, f"Peso total (kg): {safe_float(peso_total):g}")
        y -= 0.45 * cm

    y -= 0.2 * cm
    c.setLineWidth(0.3)
    c.line(x0, y, xR, y)
    y -= 0.6 * cm

    # ===== TABELA DE ITENS =====
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x0, y, "Itens")
    y -= 0.5 * cm

    # Cabeçalho
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x0, y, "Código")
    c.drawString(x0 + 3.0*cm, y, "Descrição")
    c.drawRightString(x0 + 12.5*cm, y, "Qtd")
    c.drawRightString(x0 + 15.0*cm, y, "Unit.")
    c.drawRightString(xR, y, "Subtotal")
    y -= 0.35 * cm
    c.setLineWidth(0.3)
    c.line(x0, y, xR, y)
    y -= 0.4 * cm

    c.setFont("Helvetica", 10)
    subtotal = 0.0

    for it in itens:
        cod = getattr(it, "produto_id", None) or getattr(it, "codigo_produto", None) or ""
        desc = getattr(it, "descricao", None) or getattr(it, "produto_nome", None) or str(cod)
        qtd = safe_float(getattr(it, "quantidade", 0))
        unit = safe_float(getattr(it, "preco_unit", 0))
        sub = qtd * unit
        subtotal += sub

        c.drawString(x0, y, str(cod)[:12])
        c.drawString(x0 + 3.0*cm, y, str(desc)[:48])
        c.drawRightString(x0 + 12.5*cm, y, f"{qtd:g}")
        c.drawRightString(x0 + 15.0*cm, y, brl(unit))
        c.drawRightString(xR, y, brl(sub))
        y -= 0.45 * cm

        # quebra de página
        if y < 4 * cm:
            c.showPage()
            width, height = A4
            x0, xR = 2*cm, width - 2*cm
            y = height - 2*cm
            c.setFont("Helvetica", 10)
            # título da continuação
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x0, y, "Itens (continuação)")
            y -= 0.6 * cm
            c.setFont("Helvetica", 10)

    # ===== TOTAIS =====
    y -= 0.2 * cm
    c.setLineWidth(0.3)
    c.line(x0, y, xR, y)
    y -= 0.6 * cm

    c.setFont("Helvetica-Bold", 10)
    frete = safe_float(getattr(pedido, "frete_total", getattr(pedido, "frete", 0)))
    desconto = safe_float(getattr(pedido, "desconto_total", getattr(pedido, "desconto", 0)))

    total_sem_frete = safe_float(getattr(pedido, "total_sem_frete", subtotal))
    total_com_frete = safe_float(getattr(pedido, "total_com_frete", subtotal + frete))
    total_pedido = safe_float(getattr(pedido, "total_pedido", total_com_frete or total_sem_frete))

    c.drawRightString(xR - 4.5*cm, y, "Subtotal:")
    c.drawRightString(xR, y, f"R$ {brl(subtotal)}")
    y -= 0.45 * cm

    if frete:
        c.drawRightString(xR - 4.5*cm, y, "Frete:")
        c.drawRightString(xR, y, f"R$ {brl(frete)}")
        y -= 0.45 * cm
    if desconto:
        c.drawRightString(xR - 4.5*cm, y, "Descontos:")
        c.drawRightString(xR, y, f"R$ {brl(desconto)}")
        y -= 0.45 * cm

    # Preferência: se houver total_pedido, ele manda; senão mostra com_frete/sem_frete
    c.setFont("Helvetica-Bold", 11)
    label_total = "Total do pedido:"
    valor_total = total_pedido if total_pedido else (total_com_frete or total_sem_frete)
    c.drawRightString(xR - 4.5*cm, y, label_total)
    c.drawRightString(xR, y, f"R$ {brl(valor_total)}")
    y -= 0.7 * cm

    # ===== OBSERVAÇÕES =====
    obs = getattr(pedido, "observacoes", None) or getattr(pedido, "observacao_cliente", None)
    if obs:
        if y < 3 * cm:
            c.showPage()
            width, height = A4
            x0, xR = 2*cm, width - 2*cm
            y = height - 2*cm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(x0, y, "Observações")
        y -= 0.5 * cm
        c.setFont("Helvetica", 10)

        # quebra em linhas de ~100 caracteres para não sair da página
        import textwrap
        for line in textwrap.wrap(str(obs), width=100):
            c.drawString(x0, y, line)
            y -= 0.45 * cm
            if y < 2.5 * cm:
                c.showPage()
                width, height = A4
                x0, xR = 2*cm, width - 2*cm
                y = height - 2*cm
                c.setFont("Helvetica", 10)

    # ===== RODAPÉ =====
    if y < 2.0 * cm:
        c.showPage()
        width, height = A4
        x0, xR = 2*cm, width - 2*cm
        y = height - 2*cm

    c.setFont("Helvetica", 8)
    c.drawString(x0, 1.7*cm, "Documento gerado automaticamente pelo OrderSync.")
    c.showPage()
    c.save()

    return buf.getvalue()


def get_email_cliente_responsavel_compras(
    db: Session,
    codigo_cliente: Optional[str]
) -> Optional[str]:
    """
    Retorna o email do responsável de compras do cliente correspondente ao código.
    Usa a própria tabela tb_cadastro_cliente via ClienteModel.
    """
    if not codigo_cliente:
        return None

    row = (
        db.query(ClienteModel.email_responsavel_compras)
        .filter(ClienteModel.codigo_da_empresa == codigo_cliente)
        .first()
    )

    if not row:
        return None

    # row é um tuple-like com só a coluna, então:
    email_cli = row[0]
    if email_cli and email_cli.strip():
        return email_cli.strip()
    return None


def montar_destinatarios(
    cfg_msg: ConfigEmailMensagem,
    email_cliente: Optional[str]
) -> List[str]:
    """
    - Sempre inclui destinatario_interno
    - Se enviar_para_cliente=True e email_cliente existe, inclui o cliente
    - Remove duplicados e vazios
    """
    to_list: List[str] = []

    # 1) internos
    internos_raw = cfg_msg.destinatario_interno.split(",")
    internos = [e.strip() for e in internos_raw if e.strip()]
    to_list.extend(internos)

    # 2) cliente, se flag ligada
    if cfg_msg.enviar_para_cliente and email_cliente:
        to_list.append(email_cliente)

    # dedup
    final_list: List[str] = []
    for addr in to_list:
        if addr not in final_list:
            final_list.append(addr)

    return final_list


def render_placeholders(
    template_str: str,
    pedido_info: dict,
    link_pdf: Optional[str]
) -> str:
    """
    Placeholder simples baseado no que você já salva em tb_pedidos:
      {{pedido_id}}
      {{cliente_nome}}
      {{total_pedido}}
      {{link_pdf}}
    """
    out = template_str or ""
    mapping = {
        "{{pedido_id}}":    str(pedido_info.get("pedido_id", "")),
        "{{cliente_nome}}": str(pedido_info.get("cliente_nome", "")),
        "{{total_pedido}}": str(pedido_info.get("total_pedido", "")),
        "{{link_pdf}}":     (link_pdf or ""),
    }
    for k, v in mapping.items():
        out = out.replace(k, v)
    return out


def enviar_email_notificacao(
    db: Session,
    pedido,
    link_pdf: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None
):
    cfg_msg = get_cfg_mensagem(db)
    cfg_smtp = get_cfg_smtp(db)

    # validação básica
    if not cfg_smtp or not cfg_smtp.remetente_email:
        raise HTTPException(status_code=500, detail="Configuração SMTP/remetente não encontrada.")
    if not cfg_msg or not cfg_msg.destinatario_interno:
        raise HTTPException(status_code=500, detail="Destinatário interno não configurado.")

    # pega e-mail do cliente se for o caso
    email_cli = obter_email_cliente(db, pedido)  # você já tem helper pra isso
    destinatarios = montar_destinatarios(cfg_msg, email_cli)
    if not destinatarios:
        raise HTTPException(status_code=500, detail="Nenhum destinatário válido para envio.")

    # subject/body com placeholders simples
    subject = str(cfg_msg.assunto_padrao or "").replace("{{pedido_id}}", str(getattr(pedido, "id", "")))
    body_html = str(cfg_msg.corpo_html or "").replace("{{pedido_id}}", str(getattr(pedido, "id", "")))

    if link_pdf:
        body_html += f"<p>PDF do pedido: <a href='{link_pdf}'>abrir</a></p>"

    # monta mensagem
    msg = MIMEMultipart("mixed")
    msg["From"] = cfg_smtp.remetente_email
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = subject

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(body_html, "html", "utf-8"))
    msg.attach(alt)

    # Anexa o PDF se vier `pdf_bytes`
    if pdf_bytes:
        filename = f"pedido_{getattr(pedido, 'id', '---')}.pdf"
        part = MIMEApplication(pdf_bytes, _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)

    # Envio SMTP (mantém sua lógica TLS/SSL)
    try:
        if cfg_smtp.usar_tls:
            server = smtplib.SMTP(cfg_smtp.smtp_host, cfg_smtp.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(cfg_smtp.smtp_host, cfg_smtp.smtp_port)

        # login e disparo
        server.login(cfg_smtp.smtp_user, cfg_smtp.smtp_senha)
        server.sendmail(cfg_smtp.remetente_email, destinatarios, msg.as_string())
        server.quit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao enviar e-mail: {e}")