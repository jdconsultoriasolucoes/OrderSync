import logging
from sqlalchemy.orm import Session
from datetime import datetime, date
from routers.captacao_pedidos import _get_captacao_data
from models.vendedor import VendedorModel
from services.captacao_pdf_service import gerar_pdf_prospeccao
from services.email_service import _get_cfg_msg, _get_cfg_smtp, _abrir_conexao
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

logger = logging.getLogger("ordersync.automation")

def enviar_relatorios_prospeccao(db: Session):
    """
    Função principal que busca os dados da semana, gera o PDF para cada vendedor e envia o e-mail.
    """
    logger.info("Iniciando rotina de envio de Relatórios de Prospecção")
    
    # 1. Pega os dados brutos de captação (todos os clientes)
    try:
        dados_captacao = _get_captacao_data(db)
    except Exception as e:
        logger.error(f"Erro ao obter dados de captação: {e}")
        return False
        
    # 2. Filtra os dados apenas para a semana atual
    import datetime as dt_mod
    hoje = dt_mod.date.today()
    start_of_week = hoje - dt_mod.timedelta(days=hoje.weekday())
    end_of_week = start_of_week + dt_mod.timedelta(days=6)
    
    vendedores_dict = {}
    
    for r in dados_captacao:
        if not r.get("ativo"):
            continue
            
        prev_raw = r.get("previsao_data_raw")
        if not prev_raw:
            continue
            
        prev_date = prev_raw.date() if isinstance(prev_raw, datetime) else prev_raw
        
        # Filtra pela semana atual ou clientes atrasados
        if start_of_week <= prev_date <= end_of_week or prev_date < start_of_week:
            vendedor_nome = r.get("vendedor", "Sem Vendedor")
            if vendedor_nome not in vendedores_dict:
                vendedores_dict[vendedor_nome] = []
                
            vendedor_item = r.copy()
            vendedor_item.pop("previsao_data_raw", None)
            vendedor_item.pop("sort_date", None)
            vendedores_dict[vendedor_nome].append(vendedor_item)
            
    # 3. Busca lista de e-mails dos vendedores no banco
    vendedores_db = db.query(VendedorModel).filter(VendedorModel.ativo == True).all()
    mapa_emails_vendedores = {v.nome: v.email for v in vendedores_db if v.email}
    
    # 4. Configuração SMTP
    try:
        cfg_smtp = _get_cfg_smtp(db)
        remetente = (getattr(cfg_smtp, "remetente_email", "") or getattr(cfg_smtp, "smtp_user", "")).strip()
    except Exception as e:
         logger.error("Configuração SMTP não encontrada/falhou. Abortando.")
         return False

    server = None
    try:
        server = _abrir_conexao(cfg_smtp)
    except Exception as e:
        logger.error(f"Falha ao conectar no SMTP: {e}")
        return False

    success_count = 0
    # 5. Para cada vendedor com dados, envia e-mail se ele tiver e-mail cadastrado
    for nome_vendedor, lista_clientes in vendedores_dict.items():
        if not lista_clientes:
            continue
            
        email_vendedor = mapa_emails_vendedores.get(nome_vendedor)
        if not email_vendedor:
            logger.warning(f"Vendedor '{nome_vendedor}' possui clientes para prospecção, mas NÃO TEM E-MAIL cadastrado.")
            continue
            
        logger.info(f"Gerando PDF para vendedor '{nome_vendedor}' ({len(lista_clientes)} clientes).")
        
        # Gera o PDF
        try:
            pdf_bytes = gerar_pdf_prospeccao(lista_clientes, nome_vendedor)
        except Exception as e:
            logger.error(f"Erro ao gerar PDF para {nome_vendedor}: {e}")
            continue
            
        # Monta E-mail
        msg = MIMEMultipart("mixed")
        msg["From"] = remetente
        msg["To"] = email_vendedor
        msg["Subject"] = f"Relatório de Prospecção Semanal - {start_of_week.strftime('%d/%m')} a {end_of_week.strftime('%d/%m')}"
        
        corpo = f"""
        <html>
        <body>
            <p>Olá <strong>{nome_vendedor}</strong>,</p>
            <p>Em anexo segue o seu <b>Relatório de Prospecção Semanal</b> contendo os clientes com previsão de compra para os próximos dias, bem como clientes em atraso.</p>
            <p>Total de clientes na lista: <b>{len(lista_clientes)}</b></p>
            <p>Por favor, verifique o arquivo PDF e organize suas rotas e contatos.</p>
            <br/>
            <p>Atenciosamente, <br/>Equipe OrderSync</p>
        </body>
        </html>
        """
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(corpo, "html", "utf-8"))
        msg.attach(alt)
        
        part = MIMEApplication(pdf_bytes, _subtype="pdf")
        filename = f"Prospeccao_Semanal_{nome_vendedor}.pdf"
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)
        
        # Envia
        try:
            server.sendmail(remetente, [email_vendedor], msg.as_string())
            logger.info(f"E-mail de prospecção enviado com sucesso para {nome_vendedor} ({email_vendedor}).")
            success_count += 1
        except Exception as e:
            logger.error(f"Falha no envio de e-mail para {nome_vendedor} ({email_vendedor}): {e}")
            
    try:
        server.quit()
    except:
        pass

    logger.info(f"Rotina de prospecção finalizada. E-mails enviados: {success_count}.")
    return True
