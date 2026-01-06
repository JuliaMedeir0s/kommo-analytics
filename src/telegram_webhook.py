import os
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from core.logger import logger
from core.client_resolver import get_client_by_chat_id
from core.config_loader import ConfigLoader
from core.exports import ExportEngine
from handlers.telegram_commands import resolve_report_type, help_message, normalize_command
from integrations.messenger import TelegramMessenger
from main import run_analytics_pipeline


scheduler = AsyncIOScheduler()


def scheduled_export_all_clients():
    """Job executado a cada 15 dias: gera exportações dos últimos 15 dias e envia nos chats"""
    logger.info("🔄 [SCHEDULER] Iniciando exportação quinzenal automática (últimos 15 dias)")
    
    # Buscar todos os clientes
    # No Docker, o diretório de configs está em /app/config.
    # Subimos três níveis a partir de src/ para alcançar /app.
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
    try:
        client_files = [f.replace('.json', '') for f in os.listdir(config_dir) if f.endswith('.json')]
    except FileNotFoundError:
        logger.error("📂 Pasta /config não encontrada.")
        return
    
    # Obter messenger
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN não configurado")
        return
    
    messenger = TelegramMessenger(bot_token)
    
    # Processar cada cliente
    for client_id in client_files:
        try:
            logger.info(f"📊 Exportando dados quinzenais de {client_id}...")
            config = ConfigLoader.load_client_config(client_id)
            chat_id = config['notifications']['telegram_chat_id']
            
            # Calcular período dos últimos 15 dias
            from datetime import timedelta
            from core.date_helper import datetime
            end_date = datetime.now()
            start_date = end_date - timedelta(days=15)
            period_timestamps = (int(start_date.timestamp()), int(end_date.timestamp()))
            
            # Gerar arquivos dos últimos 15 dias
            files = ExportEngine.generate_exports(client_id, config, period_timestamps=period_timestamps)
            
            # Enviar mensagem inicial
            messenger.send_message(
                chat_id, 
                f"📦 *Exportação Quinzenal Automática*\n\n"
                f"Cliente: {config.get('client_name', client_id)}\n"
                f"Período: Últimos 15 dias\n"
                f"Aguarde o envio dos arquivos..."
            )
            
            # Enviar todos os arquivos
            for category, paths in files.items():
                messenger.send_document(
                    chat_id, 
                    paths['excel'],
                    caption=f"📊 {category.replace('_', ' ').title()} - Excel"
                )
                messenger.send_document(
                    chat_id, 
                    paths['csv'],
                    caption=f"📊 {category.replace('_', ' ').title()} - CSV"
                )
            
            messenger.send_message(chat_id, "✅ Exportação quinzenal concluída!")
            logger.info(f"✅ {client_id}: 8 arquivos enviados para o chat")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar exportação de {client_id}: {e}", exc_info=True)
    
    logger.info("🏁 [SCHEDULER] Exportação quinzenal automática finalizada")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia startup e shutdown da aplicação"""
    # Startup: iniciar scheduler
    logger.info("🚀 Iniciando scheduler (exportação automática a cada 15 dias)")
    
    # Agenda para rodar a cada 15 dias às 9h da manhã
    scheduler.add_job(
        scheduled_export_all_clients,
        CronTrigger(day='1,15', hour=9, minute=0),  # Dia 1 e 15 de cada mês às 9h
        id='export_job',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler ativo")
    
    yield
    
    # Shutdown: parar scheduler
    scheduler.shutdown()
    logger.info("🛑 Scheduler encerrado")


app = FastAPI(lifespan=lifespan)


def get_messenger() -> TelegramMessenger | None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN não configurado no ambiente")
        return None
    return TelegramMessenger(bot_token)


def _run_pipeline_async(report_type: str, messenger: TelegramMessenger, client_id: str | None = None):
    thread = threading.Thread(target=run_analytics_pipeline, args=(report_type, messenger, client_id), daemon=True)
    thread.start()


def _handle_export_command(export_type: str, chat_id: int, messenger: TelegramMessenger, client_id: str):
    """Processa comando de exportação e envia arquivos para o chat"""
    def export_and_send():
        try:
            logger.info(f"📊 Gerando exportação {export_type} para {client_id}")
            config = ConfigLoader.load_client_config(client_id)
            
            # Determina período baseado no sufixo do comando
            period_timestamps = None
            period_label = "Histórico Completo"
            
            if '_weekly' in export_type:
                from core.date_helper import DateHelper
                period_timestamps = DateHelper.get_timestamps_for_report('weekly')
                period_label = "Semana Atual"
            elif '_last_week' in export_type:
                from core.date_helper import DateHelper
                period_timestamps = DateHelper.get_timestamps_for_report('last_week')
                period_label = "Semana Passada"
            elif '_monthly' in export_type:
                from core.date_helper import DateHelper
                period_timestamps = DateHelper.get_timestamps_for_report('current_month')
                period_label = "Mês Atual"
            elif '_last_month' in export_type:
                from core.date_helper import DateHelper
                period_timestamps = DateHelper.get_timestamps_for_report('last_month')
                period_label = "Mês Anterior"
            elif '_yearly' in export_type:
                from core.date_helper import DateHelper
                period_timestamps = DateHelper.get_timestamps_for_report('yearly')
                period_label = "Ano Atual"
            elif '_last_year' in export_type:
                from core.date_helper import DateHelper
                period_timestamps = DateHelper.get_timestamps_for_report('last_year')
                period_label = "Ano Anterior"
            
            # Gerar arquivos
            files = ExportEngine.generate_exports(client_id, config, period_timestamps=period_timestamps)
            
            # Determina categorias baseado no tipo base do comando
            if 'won' in export_type:
                categories = ["ganhos"]
            elif 'lost_followup' in export_type:
                categories = ["perdidos_followup"]
            elif 'lost' in export_type:
                categories = ["perdidos"]
            elif 'active' in export_type:
                categories = ["ativos"]
            else:
                # export_all ou export sem sufixo
                categories = ["ganhos", "perdidos", "perdidos_followup", "ativos"]
            
            # Enviar arquivos para o chat
            for category in categories:
                if category in files:
                    category_files = files[category]
                    
                    # Enviar Excel
                    messenger.send_document(
                        chat_id, 
                        category_files['excel'],
                        caption=f"📊 {category.replace('_', ' ').title()} - {period_label} - Excel"
                    )
                    
                    # Enviar CSV
                    messenger.send_document(
                        chat_id, 
                        category_files['csv'],
                        caption=f"📊 {category.replace('_', ' ').title()} - {period_label} - CSV"
                    )
            
            messenger.send_message(chat_id, f"✅ Exportação concluída: {period_label}\n{len(categories)} categoria(s), {len(categories)*2} arquivo(s)")
            logger.info(f"✅ {client_id}: {len(categories)*2} arquivos enviados para o chat")
            
        except Exception as e:
            logger.error(f"❌ Erro na exportação para {client_id}: {e}", exc_info=True)
            messenger.send_message(chat_id, f"❌ Erro ao gerar exportação: {str(e)}")
    
    # Executar em thread para não bloquear o webhook
    thread = threading.Thread(target=export_and_send, daemon=True)
    thread.start()


@app.post("/telegram/webhook")
async def telegram_webhook(update: dict):
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")

    if not chat_id:
        logger.info("⚠️ [WEBHOOK] Chat ID ausente na mensagem")
        return {"ok": True}

    logger.info(f"📨 [WEBHOOK] Mensagem recebida - Chat ID: {chat_id}, Texto: {text}")

    messenger = get_messenger()
    if messenger is None:
        logger.error("❌ [WEBHOOK] TELEGRAM_BOT_TOKEN não configurado")
        return {"ok": False, "error": "Bot token ausente"}

    command = normalize_command(text)
    logger.info(f"📝 [WEBHOOK] Comando normalizado: {command}")
    
    report_type = resolve_report_type(command)
    logger.info(f"📊 [WEBHOOK] Tipo de relatório resolvido: {report_type}")

    if report_type is None or report_type == "help":
        logger.info(f"ℹ️ [WEBHOOK] Enviando help_message() para chat {chat_id}")
        messenger.send_message(chat_id, help_message())
        return {"ok": True}

    # Identifica qual cliente está fazendo a requisição
    client_id = get_client_by_chat_id(chat_id)
    logger.info(f"🔍 [WEBHOOK] Chat {chat_id} → Client ID: {client_id}")
    
    if not client_id:
        logger.warning(f"⚠️ [WEBHOOK] Chat ID {chat_id} não encontrado em nenhuma configuração de cliente")
        messenger.send_message(chat_id, "❌ Este chat não está configurado para nenhum cliente. Verifique o telegram_chat_id no arquivo de configuração.")
        return {"ok": True}

    # Se for comando de exportação, processa separadamente
    if report_type.startswith("export_"):
        logger.info(f"📦 [WEBHOOK] Processando exportação: {report_type}")
        messenger.send_message(chat_id, f"📥 Gerando exportação: {command}\nAguarde alguns segundos…")
        _handle_export_command(report_type, chat_id, messenger, client_id)
        return {"ok": True}

    # Caso contrário, é relatório normal
    logger.info(f"📋 [WEBHOOK] Processando relatório: {report_type}")
    messenger.send_message(chat_id, f"📥 Comando recebido: {command}\nGerando relatório…")
    _run_pipeline_async(report_type, messenger, client_id)

    return {"ok": True}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
