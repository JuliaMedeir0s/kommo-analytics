import os
import threading
from fastapi import FastAPI
from core.logger import logger
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


def _run_pipeline_async(report_type: str, messenger: TelegramMessenger):
    thread = threading.Thread(target=run_analytics_pipeline, args=(report_type, messenger), daemon=True)
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

    messenger.send_message(chat_id, f"📥 Comando recebido: {command}\nGerando relatório…")
    _run_pipeline_async(report_type, messenger)

    return {"ok": True}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
