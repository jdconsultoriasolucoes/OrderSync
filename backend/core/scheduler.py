from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from database import SessionLocal
from services.cliente import verificar_inatividade_clientes
from services.manutencao import limpar_arquivos_temporarios
from services.prospeccao_service import enviar_relatorios_prospeccao
from models.automation_config import AutomationConfigModel
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger("ordersync.scheduler")
TZ = ZoneInfo("America/Sao_Paulo")

scheduler = BackgroundScheduler(timezone=TZ)

def check_dynamic_prospeccao():
    """
    Verifica no banco se hoje é o dia e hora configurados para o relatório.
    Roda a cada 5 minutos para precisão.
    """
    db = SessionLocal()
    try:
        cfg = db.query(AutomationConfigModel).first()
        if not cfg or not cfg.prospeccao_ativa:
            return

        agora = datetime.now(TZ)
        hoje_str = agora.strftime("%Y-%m-%d")
        
        # 1. Verifica Dia da Semana
        if agora.weekday() != cfg.prospeccao_dia_semana:
            return
            
        # 2. Verifica Horário (se já passou do horário configurado)
        if cfg.prospeccao_horario:
            hora_config = cfg.prospeccao_horario
            # Se já enviou hoje, pula
            if cfg.prospeccao_ultimo_envio == hoje_str:
                return
                
            # Se a hora atual for maior ou igual à configurada
            if agora.hour > hora_config.hour or (agora.hour == hora_config.hour and agora.minute >= hora_config.minute):
                logger.info(f"[Scheduler] Disparando relatório de prospecção configurado para {hora_config.strftime('%H:%M')}")
                enviar_relatorios_prospeccao(db)
                
                # Marca como enviado hoje
                cfg.prospeccao_ultimo_envio = hoje_str
                db.commit()
    except Exception as e:
        logger.error(f"[Scheduler] Erro na checagem de prospecção: {e}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        # 1. Inativação de Clientes: Todo dia às 00:01
        scheduler.add_job(
            verificar_inatividade_clientes,
            trigger=CronTrigger(hour=0, minute=1),
            id="inatividade_diaria",
            name="Inativação automática de clientes (00:01)",
            replace_existing=True
        )

        # 2. Manutenção de Sistema: Todo dia às 03:00
        scheduler.add_job(
            limpar_arquivos_temporarios,
            trigger=CronTrigger(hour=3, minute=0),
            id="manutencao_diaria",
            name="Limpeza de arquivos temporários (03:00)",
            replace_existing=True
        )

        # 3. Prospecção Dinâmica: Checa a cada 5 minutos
        scheduler.add_job(
            check_dynamic_prospeccao,
            trigger=IntervalTrigger(minutes=5),
            id="prospeccao_dinamica",
            name="Verificação de agendamento de prospecção (DB)",
            replace_existing=True
        )

        scheduler.start()
        logger.info("Scheduler iniciado com sucesso (Inativação 00:01 | Manutenção 03:00 | Prospecção Dinâmica)")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler parado.")
