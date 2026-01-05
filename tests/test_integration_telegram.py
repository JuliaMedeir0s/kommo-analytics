import pytest
import os
from dotenv import load_dotenv
from core.config_loader import ConfigLoader
from integrations.messenger import TelegramMessenger

# Carrega variáveis de ambiente do .env
load_dotenv()

# Função auxiliar para listar todos os clientes na pasta config
def get_all_clients():
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
    return [f.replace('.json', '') for f in os.listdir(config_dir) if f.endswith('.json')]


def test_telegram_health_check():
    """
    Verifica se o bot do Telegram está ativo
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    assert bot_token is not None, "TELEGRAM_BOT_TOKEN não encontrado no .env"
    
    messenger = TelegramMessenger(bot_token)
    is_ok = messenger.health_check()
    assert is_ok is True, "Falha na conexão com o Telegram"


@pytest.mark.parametrize("client_id", get_all_clients())
def test_telegram_send_message_per_client(client_id):
    """
    Testa o envio de mensagem para cada cliente configurado no Telegram
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    assert bot_token is not None, "TELEGRAM_BOT_TOKEN não encontrado no .env"
    
    messenger = TelegramMessenger(bot_token)
    
    # Carregar configuração do cliente
    config = ConfigLoader.load_client_config(client_id)
    chat_id = config['notifications']['telegram_chat_id']
    client_name = config.get('client_name', client_id)
    
    # Enviar mensagem de teste para este cliente
    response = messenger.send_message(
        chat_id, 
        f"✅ *Teste de Integração - {client_name}*\nMensagem enviada com sucesso!"
    )
    
    # Verificar se a resposta contém sucesso
    assert 'ok' in response
    assert response['ok'] is True, f"Erro ao enviar mensagem para {client_id}: {response.get('description', 'Desconhecido')}"

