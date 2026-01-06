import os
import sys
from dotenv import load_dotenv
from core.logger import logger
from core.config_loader import ConfigLoader
from core.analytics import AnalyticsEngine
from core.date_helper import DateHelper
from integrations.kommo_client import KommoClient
from integrations.messenger import TelegramMessenger

# Carrega variáveis de ambiente (.env)
load_dotenv()

def run_analytics_pipeline(report_type="weekly", messenger: TelegramMessenger | None = None, client_id: str | None = None):
    logger.info(f"🚀 [INÍCIO] Iniciando Engine de Analytics: Relatório {report_type.upper()}")

    # Aliases para manter compatibilidade e clareza
    aliases = {
        "annual": "last_year",
        "month": "current_month",
    }
    report_type = aliases.get(report_type, report_type)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.critical("❌ TELEGRAM_BOT_TOKEN não encontrado no arquivo .env")
        return

    messenger = messenger or TelegramMessenger(bot_token)
    
    # 2. Varredura de Clientes (Busca todos os arquivos .json na pasta /config)
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
    try:
        all_clients = [f.replace('.json', '') for f in os.listdir(config_dir) if f.endswith('.json')]
    except FileNotFoundError:
        logger.error("📂 Pasta /config não encontrada.")
        return

    if not all_clients:
        logger.warning("⚠️ Nenhum arquivo de configuração de cliente encontrado.")
        return
    
    # Se client_id foi especificado, processa apenas esse cliente
    if client_id:
        if client_id not in all_clients:
            logger.error(f"❌ Cliente {client_id} não encontrado nas configurações")
            return
        client_files = [client_id]
        logger.info(f"📌 Processando apenas o cliente: {client_id}")
    else:
        client_files = all_clients
        logger.info(f"📌 Processando todos os clientes: {len(client_files)}")

    # 3. Definição do Período de Busca baseado no tipo de relatório
    periods = DateHelper.get_timestamps_for_report(report_type)
    labels = {
        "weekly": "Semana Atual (Dom - Hoje)",
        "last_week": "Semana Passada (Dom - Sáb)",
        "monthly": "Mês Anterior (Fechado)",
        "last_month": "Mês Anterior (Fechado)",
        "current_month": "Mês Atual (Até hoje)",
        "month_to_date": "Mês Atual (Até hoje)",
        "yearly": "Ano Atual (Até hoje)",
        "year_to_date": "Ano Atual (Até hoje)",
        "last_year": "Ano Anterior (Retrospectiva)",
        "annual": "Ano Anterior (Retrospectiva)",
    }

    if not periods:
        logger.error(f"❌ Tipo de relatório desconhecido: {report_type}")
        return

    start_ts, end_ts = periods
    label_periodo = labels.get(report_type, report_type)

    # 4. Loop de Processamento por Cliente
    for client_id in client_files:
        logger.info(f"📌 Processando Cliente: {client_id}")
        
        try:
            # Carrega configurações e inicializa cliente Kommo
            config = ConfigLoader.load_client_config(client_id)
            client = KommoClient(config['kommo']['subdomain'], config['kommo']['api_token'])
            
            # Health Check (Opcional, mas recomendado)
            is_ok, conn_msg = client.health_check()
            if not is_ok:
                logger.error(f"🚫 Falha na conexão para {client_id}: {conn_msg}")
                continue

            # --- COLETA DE DADOS ---
            p_id = config['kommo']['pipeline_id']
            
            # A. Leads Criados na Pipeline Específica
            leads_in_pipe = client.get_leads(start_ts, end_ts, p_id)
            
            # B. Leads na 'Entrada' (Unsorted/Leads de Entrada)
            leads_unsorted = client.get_unsorted_leads(start_ts, end_ts)
            
            # C. Vendas Totais Ganhos (Independente de quando foram criados)
            leads_won = client.get_won_leads(start_ts, end_ts, p_id)

            # --- PROCESSAMENTO ---
            # Unifica leads de Entrada com os da Pipeline para análise de eficiência real
            all_created = leads_in_pipe + leads_unsorted
            
            stats = AnalyticsEngine.calculate_metrics(
                all_created, 
                leads_won, 
                config['kommo']['won_status_id']
            )
            
            origins = AnalyticsEngine.group_by_origin(
                all_created, 
                config['kommo']['origin_field_id']
            )

            # --- FORMATAÇÃO DA MENSAGEM ---
            report_title = f"📊 *RELATÓRIO {report_type.upper()}: {config['client_name']}*"
            
            msg = (
                f"{report_title}\n"
                f"📅 _Período: {label_periodo}_\n"
                f"--- \n"
                f"📥 *Novos Leads:* {stats['total_created']}\n"
                f"🏆 *Vendas Totais:* {stats['total_closed_won']}\n"
                f"⚡ *Conversão Imediata:* {stats['cohort_won']} (novos que já fecharam)\n\n"
                f"🎯 *O NORTE:* `{stats['ratio']}` leads p/ 1 venda\n"
                f"--- \n"
                f"🌍 *Top Origens (Novos):*\n"
            )
            
            # Adiciona as top 3 origens
            for origin, count in list(origins.items())[:3]:
                msg += f"• {origin}: {count}\n"
            
            msg += "\n📈 _Análise automatizada via Engine Python_"

            # --- ENVIO ---
            messenger.send_message(config['notifications']['telegram_chat_id'], msg)
            logger.info(f"✅ Relatório enviado com sucesso para {client_id}")

        except Exception as e:
            logger.error(f"💥 Erro crítico ao processar o cliente {client_id}: {str(e)}", exc_info=True)

    logger.info("🏁 Pipeline finalizado.")

if __name__ == "__main__":
    # Permite rodar: python src/main.py weekly | monthly | annual
    target_report = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    run_analytics_pipeline(target_report)