import asyncio
import logging
import os
import base64
from sqlalchemy import text
from datetime import datetime
from zoneinfo import ZoneInfo

from database import SessionLocal
from models.background_task import BackgroundTaskModel
from services.pdf_service import gerar_pdf_pedido
from services.pedido_pdf_data import carregar_pedido_pdf
from services.email_service import enviar_email_notificacao, get_email_cliente_responsavel_compras

logger = logging.getLogger("ordersync.worker")
TZ = ZoneInfo("America/Sao_Paulo")

class PedidoEmailDummyBG:
    def __init__(self, id_pedido, codigo_cliente, cliente_nome, total_pedido, cliente_email):
        self.id = id_pedido
        self.codigo_cliente = codigo_cliente
        self.cliente_nome = cliente_nome
        self.total_pedido = total_pedido
        self.cliente_email = cliente_email

async def process_email_task(db, task: BackgroundTaskModel):
    """
    Executa a pesada geração de PDF e o envio do SMTP fora do pipeline principal HTTP
    """
    id_pedido = task.referencia_id
    logger.info(f"Worker processando tarefa {task.id} para Pedido {id_pedido}")
    
    # 1. Carregar dados do pedido
    try:
        pedido_row = db.execute(text("""
            SELECT codigo_cliente, cliente, total_pedido 
            FROM tb_pedidos 
            WHERE id_pedido = :id
        """), {"id": id_pedido}).mappings().first()
        
        if not pedido_row:
            raise Exception(f"Pedido {id_pedido} não encontrado na base")
            
        c_cod = pedido_row["codigo_cliente"]
        c_nom = pedido_row["cliente"]
        p_tot = pedido_row["total_pedido"]
        
    except Exception as e:
        logger.error(f"Worker falhou ao buscar pedido {id_pedido}: {e}")
        raise e

    # 2. Gerar PDFs pesados
    try:
        pedido_pdf_dados = carregar_pedido_pdf(db, id_pedido)
        pdf_bytes_vendedor = gerar_pdf_pedido(pedido_pdf_dados, sem_validade=False)
        pdf_bytes_cliente = gerar_pdf_pedido(pedido_pdf_dados, sem_validade=True)
    except Exception as e:
        logger.error(f"Worker falhou ao gerar PDFs para pedido {id_pedido}: {e}")
        raise e
        
    # 3. Enviar E-mail
    try:
        cliente_email_addr = get_email_cliente_responsavel_compras(db, c_cod)
        pedido_email_bg = PedidoEmailDummyBG(id_pedido, c_cod, c_nom, p_tot, cliente_email_addr)
        
        enviar_email_notificacao(
            db=db,
            pedido=pedido_email_bg,
            link_pdf=None,
            pdf_bytes=pdf_bytes_vendedor,
            pdf_bytes_cliente=pdf_bytes_cliente
        )
    except Exception as e:
        logger.error(f"Worker falhou ao enviar SMTP pedido {id_pedido}: {e}")
        raise e
        
    # 4. Sucesso: Atualiza Status Link
    try:
        db.execute(text("""
            UPDATE public.tb_pedidos 
            SET link_enviado_em = NOW(), 
                link_status = 'ENVIADO', 
                atualizado_em = NOW() 
            WHERE id_pedido = :id
        """), {"id": id_pedido})
        
        # Opcional salvar o base64 para uso imediato do front se quisesse, 
        # mas como é worker, o front já pode ter o base64 inicial gerado syncronamente.
    except Exception as e:
         logger.error(f"Worker falhou ao marcar finalizado pedido {id_pedido}: {e}")
         raise e
         
    return True

async def check_automation_schedules(db):
    try:
        from models.automation_config import AutomationConfigModel
        from services.prospeccao_service import enviar_relatorios_prospeccao
        import datetime as dt_mod
        
        cfg = db.query(AutomationConfigModel).first()
        if not cfg or not cfg.prospeccao_ativa:
            return
            
        agora = datetime.now(TZ)
        hoje = agora.date()
        
        # Log detalhado apenas se estamos na mesma hora da config para evitar poluição visual excessiva
        # Mas vamos imprimir ao menos se o dia bate ou não bater
        
        dia_config = cfg.prospeccao_dia_semana
        dia_hoje = hoje.weekday() # Monday is 0
        
        if dia_hoje != dia_config:
            # Não loga aqui para não fludar o log a cada 5 segundos de um dia inteiro errado
            return
            
        if cfg.prospeccao_horario:
            hora_config = cfg.prospeccao_horario
            hora_atual = dt_mod.time(agora.hour, agora.minute, agora.second)
            
            # Log quando está perto do horário (mesmo dia e hora, mas minutos diferentes, ou mesmo minuto)
            if hora_atual.hour == hora_config.hour:
                 logger.debug(f"[SysTime] Automação: Dia OK, Hora atual SP: {hora_atual.strftime('%H:%M:%S')} vs Config: {hora_config.strftime('%H:%M:%S')}")

            # Se a hora atual for maior ou igual à hora configurada
            if hora_atual >= hora_config:
                hoje_str = hoje.strftime("%Y-%m-%d")
                if cfg.prospeccao_ultimo_envio != hoje_str:
                    logger.info(f"Disparando envio de Relatório de Prospecção agendado. Hora SP: {hora_atual.strftime('%H:%M:%S')} >= Config {hora_config.strftime('%H:%M:%S')}")
                    success = enviar_relatorios_prospeccao(db)
                    
                    # Atualiza independente de 100% success ou partial, pra não ficar em loop
                    cfg.prospeccao_ultimo_envio = hoje_str
                    db.commit()
                else:
                    pass # Já enviado hoje
            else:
                pass # Dia certo, mas a hora ainda não chegou
        
    except Exception as e:
        logger.error(f"Erro ao checar automações: {e}")

_last_inactivity_check_date = None

async def check_daily_inactivity_schedule():
    global _last_inactivity_check_date
    agora = datetime.now(TZ)
    hoje_str = agora.strftime("%Y-%m-%d")

    if _last_inactivity_check_date is None:
        # Considera como já verificado hoje, pois o main.py (startup) garante a primeira passada.
        _last_inactivity_check_date = hoje_str
        return

    if _last_inactivity_check_date != hoje_str:
        from services.cliente import verificar_inatividade_clientes
        logger.info(f"Virada de dia detectada ({hoje_str}). Tarefa Agendada [00:00] - Verificação de Clientes Inativos.")
        try:
            verificar_inatividade_clientes()
        except Exception as e:
            logger.error(f"Falha na auto-inativação pelo Worker: {e}")
        finally:
            _last_inactivity_check_date = hoje_str

async def worker_loop():
    import datetime as dt_mod
    logger.info(f"Worker assíncrono iniciado. Fuso horário do Worker (TZ): {datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')} (SP)")
    
    while True:
        try:
            with SessionLocal() as db:
                # Checa sempre as automações agendadas no início do loop, independente da fila
                await check_automation_schedules(db)
                await check_daily_inactivity_schedule()
                
                # Fetch pending top 1
                task = db.query(BackgroundTaskModel)\
                         .filter(BackgroundTaskModel.status == 'PENDENTE')\
                         .order_by(BackgroundTaskModel.criado_em.asc())\
                         .with_for_update(skip_locked=True)\
                         .first()
                         
                if task:
                    task.status = "PROCESSANDO"
                    task.tentativas += 1
                    db.commit() # Solta o lock row e marca em proc
                    
                    try:
                        if task.tipo_tarefa == "ENVIO_EMAIL_CONFIRMACAO":
                            await process_email_task(db, task)
                            
                        task.status = "CONCLUIDO"
                        task.erro_msg = None
                        
                    except Exception as e:
                        task.erro_msg = str(e)
                        if task.tentativas >= 3:
                            task.status = "ERRO"
                            logger.error(f"Task {task.id} max retries reached. Abandoning.")
                        else:
                            # Volta para pendente no prox loop (após delay no loop)
                            task.status = "PENDENTE" 
                            
                    task.atualizado_em = datetime.now(TZ)
                    db.commit()
                else:
                    # Nenhuma task para pegar, dorme antes de poolear de novo.
                    await asyncio.sleep(5)
                    continue

            # Se achou task, tenta já buscar a próxima em curto intervalo
            await asyncio.sleep(0.5)

        except BaseException as e:
            if isinstance(e, asyncio.CancelledError):
                 logger.info("Worker Interrompido (shutdown)")
                 break
                 
            logger.error(f"Worker falhou catastroficamente no DB loop: {e}")
            await asyncio.sleep(5)

def start_background_worker():
    """ Fire-and-forget setup do asyncio loop para fastapi"""
    loop = asyncio.get_event_loop()
    loop.create_task(worker_loop())
