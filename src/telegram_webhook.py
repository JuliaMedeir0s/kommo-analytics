import os
import threading
from fastapi import FastAPI
from core.logger import logger
from core.client_resolver import get_client_by_chat_id
from core.config_loader import ConfigLoader
from core.exports import ExportEngine
from core.date_helper import DateHelper
from handlers.telegram_commands import resolve_report_type, help_message, normalize_command
from integrations.messenger import TelegramMessenger
from main import run_analytics_pipeline

app = FastAPI()


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
                period_timestamps = DateHelper.get_timestamps_for_report('weekly')
                period_label = "Semana Atual"
            elif '_last_week' in export_type:
                period_timestamps = DateHelper.get_timestamps_for_report('last_week')
                period_label = "Semana Passada"
            elif '_monthly' in export_type:
                period_timestamps = DateHelper.get_timestamps_for_report('current_month')
                period_label = "Mês Atual"
            elif '_last_month' in export_type:
                period_timestamps = DateHelper.get_timestamps_for_report('last_month')
                period_label = "Mês Anterior"
            elif '_yearly' in export_type:
                period_timestamps = DateHelper.get_timestamps_for_report('yearly')
                period_label = "Ano Atual"
            elif '_last_year' in export_type:
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
                        caption=f"📊 {category.replace('_', ' ').title()} - {period_label}\n📄 Formato: Excel"
                    )
                    
                    # Enviar CSV
                    messenger.send_document(
                        chat_id, 
                        category_files['csv'],
                        caption=f"📊 {category.replace('_', ' ').title()} - {period_label}\n📄 Formato: CSV"
                    )
            
            # Mensagem de sucesso com resumo
            completion_msg = (
                f"✅ *Exportação Concluída*\n\n"
                f"📅 Período: {period_label}\n"
                f"📦 Categorias: {len(categories)}\n"
                f"📄 Arquivos: {len(categories)*2} (Excel + CSV)\n\n"
                f"_Os dados estão prontos para análise!_ 📊"
            )
            messenger.send_message(chat_id, completion_msg)
            logger.info(f"✅ {client_id}: {len(categories)*2} arquivos enviados para o chat")
            
        except Exception as e:
            logger.error(f"❌ Erro na exportação para {client_id}: {e}", exc_info=True)
            error_msg = (
                f"❌ *Erro na Exportação*\n\n"
                f"Não foi possível gerar os arquivos.\n"
                f"Detalhes: `{str(e)[:100]}`\n\n"
                f"Por favor, tente novamente ou entre em contato com o suporte."
            )
            messenger.send_message(chat_id, error_msg)
    
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
        return {"ok": True}

    messenger = get_messenger()
    if messenger is None:
        return {"ok": False, "error": "Bot token ausente"}

    command = normalize_command(text)
    report_type = resolve_report_type(command)

    if report_type is None or report_type == "help":
        messenger.send_message(chat_id, help_message())
        return {"ok": True}

    # Identifica qual cliente está fazendo a requisição
    client_id = get_client_by_chat_id(chat_id)
    
    if not client_id:
        error_msg = (
            "❌ *Chat não configurado*\n\n"
            "Este chat não está associado a nenhum cliente.\n\n"
            "👉 Verifique se o `telegram_chat_id` no arquivo de configuração corresponde a este chat."
        )
        messenger.send_message(chat_id, error_msg)
        return {"ok": True}

    # Se for comando de exportação, processa separadamente
    if report_type.startswith("export_"):
        processing_msg = (
            f"📥 *Exportação iniciada*\n\n"
            f"Comando: `{command}`\n"
            f"Status: Gerando arquivos...\n\n"
            f"⏳ Aguarde alguns segundos..."
        )
        messenger.send_message(chat_id, processing_msg)
        _handle_export_command(report_type, chat_id, messenger, client_id)
        return {"ok": True}

    # Caso contrário, é relatório normal
    messenger.send_message(chat_id, f"📥 Comando recebido: {command}\nGerando relatório…")
    _run_pipeline_async(report_type, messenger, client_id)

    return {"ok": True}


@app.get("/health")
async def health_check():
    return {"status": "ok"}

