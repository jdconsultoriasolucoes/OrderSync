import logging
from datetime import datetime
from sqlalchemy.orm import Session
from jinja2 import Template

from database import SessionLocal
from models.usuario import UsuarioModel
from models.calendario import EventModel, CalendarModel, CalendarShareModel
from services.email_service import _abrir_conexao, _get_cfg_smtp
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("ordersync.worker")

# Template HTML simples usando Jinja2 para loop de eventos
TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eaeaea; border-radius: 8px; background-color: #fafafa; }
        .header { background-color: #2b6cb0; color: white; padding: 15px; border-radius: 8px 8px 0 0; text-align: center; }
        .content { padding: 20px; background-color: white; border-radius: 0 0 8px 8px; }
        .event-card { border-left: 4px solid; padding: 10px; margin-bottom: 15px; background-color: #f8fafc; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .event-time { font-weight: bold; color: #4a5568; font-size: 0.9em; }
        .event-title { font-size: 1.1em; margin: 5px 0; color: #1a202c; font-weight: 600; }
        .event-cal-name { font-size: 0.8em; color: #718096; }
        .btn { display: inline-block; background-color: #2b6cb0; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Bom dia, {{ user_nome }}!</h2>
            <p style="margin:0;">Aqui estão seus compromissos para hoje ({{ data_hoje }})</p>
        </div>
        <div class="content">
            {% if eventos %}
                {% for ev in eventos %}
                <div class="event-card" style="border-left-color: {{ ev.cor }};">
                    <div class="event-time">
                        {% if ev.dia_inteiro %}
                            Dia Inteiro
                        {% else %}
                            {{ ev.hora_inicio }} - {{ ev.hora_fim }}
                        {% endif %}
                    </div>
                    <div class="event-title">{{ ev.titulo }}</div>
                    <div class="event-cal-name">Agenda: {{ ev.agenda_nome }}</div>
                    {% if ev.local %}
                    <div class="event-cal-name">📍 {{ ev.local }}</div>
                    {% endif %}
                </div>
                {% endfor %}
                <div style="text-align: center;">
                    <a href="{{ link_app }}" class="btn">Acessar Meu Calendário</a>
                </div>
            {% else %}
                <p>Você não tem compromissos agendados para hoje. Tenha um excelente dia!</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

def enviar_resumo_matinal():
    """
    Função chamada pelo Scheduler todo dia às 06:00.
    Busca usuários com email_daily_digest=True e envia seus eventos do dia.
    """
    logger.info("[DailyDigest] Iniciando envio do resumo matinal...")
    db: Session = SessionLocal()
    try:
        cfg_smtp = _get_cfg_smtp(db)
        remetente = (getattr(cfg_smtp, "remetente_email", "") or getattr(cfg_smtp, "smtp_user", "")).strip()
        
        # 1. Usuários ativos que desejam e-mail
        usuarios = db.query(UsuarioModel).filter(
            UsuarioModel.ativo == True,
            UsuarioModel.email_daily_digest == True
        ).all()
        
        agora = datetime.now()
        inicio_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        fim_dia = agora.replace(hour=23, 59, 59, 999999)
        data_str = agora.strftime("%d/%m/%Y")
        
        # Link do Frontend (Fallback dev/prod)
        # O ideal é estar em variáveis de ambiente, usando placeholder temporário
        link_app = "https://ordersync-y7kg.onrender.com/public/index.html" 
        
        jinja_template = Template(TEMPLATE_HTML)
        
        with _abrir_conexao(cfg_smtp) as server:
            for user in usuarios:
                # 2. Encontrar agendas do usuário
                own_cals = db.query(CalendarModel).filter(CalendarModel.user_id == user.id).all()
                shared_cals = db.query(CalendarModel).join(CalendarShareModel).filter(
                    CalendarShareModel.shared_with_user_id == user.id
                ).all()
                
                cal_map = {c.id: c for c in own_cals + shared_cals}
                if not cal_map:
                    continue
                    
                # 3. Buscar eventos de hoje
                eventos = db.query(EventModel).filter(
                    EventModel.calendar_id.in_(cal_map.keys()),
                    EventModel.start_time >= inicio_dia,
                    EventModel.start_time <= fim_dia
                ).order_by(EventModel.start_time).all()
                
                if not eventos:
                    continue # Não envia e-mail se não houver eventos
                    
                # 4. Preparar dados para o template
                eventos_data = []
                for ev in eventos:
                    cal = cal_map[ev.calendar_id]
                    eventos_data.append({
                        "titulo": ev.title,
                        "hora_inicio": ev.start_time.strftime("%H:%M"),
                        "hora_fim": ev.end_time.strftime("%H:%M"),
                        "dia_inteiro": ev.is_all_day,
                        "agenda_nome": cal.name,
                        "cor": cal.color,
                        "local": ev.location
                    })
                    
                # 5. Renderizar HTML
                html_body = jinja_template.render(
                    user_nome=user.nome,
                    data_hoje=data_str,
                    eventos=eventos_data,
                    link_app=link_app
                )
                
                # 6. Construir Mensagem
                msg = MIMEMultipart("alternative")
                msg["From"] = remetente
                msg["To"] = user.email
                msg["Subject"] = f"Seus Compromissos de Hoje - {data_str}"
                
                msg.attach(MIMEText(html_body, "html", "utf-8"))
                
                # 7. Enviar
                try:
                    server.sendmail(remetente, [user.email], msg.as_string())
                    logger.info(f"[DailyDigest] Enviado para {user.email} com {len(eventos)} compromissos.")
                except Exception as e_send:
                    logger.error(f"[DailyDigest] Falha ao enviar para {user.email}: {e_send}")
                    
    except Exception as e:
        logger.error(f"[DailyDigest] Erro geral: {e}")
    finally:
        db.close()
        logger.info("[DailyDigest] Finalizado.")
