import pytest
import os
from dotenv import load_dotenv
from core.config_loader import ConfigLoader
from integrations.kommo_client import KommoClient

# Carrega variáveis de ambiente do .env
load_dotenv()

# Função auxiliar para listar todos os clientes na pasta config
def get_all_clients():
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
    return [f.replace('.json', '') for f in os.listdir(config_dir) if f.endswith('.json')]

@pytest.mark.parametrize("client_id", get_all_clients())
def test_client_integrity(client_id):
    """
    Testa se o JSON de cada cliente é válido e se o Token no .env existe.
    """
    config = ConfigLoader.load_client_config(client_id)
    
    assert config['kommo']['subdomain'] is not None
    assert config['kommo']['api_token'] is not None, f"Token para {client_id} não encontrado no .env"
    assert isinstance(config['kommo']['origin_field_id'], int)

@pytest.mark.parametrize("client_id", get_all_clients())
def test_kommo_connection_per_client(client_id):
    """
    Realiza o health check real para cada cliente configurado.
    """
    config = ConfigLoader.load_client_config(client_id)
    client = KommoClient(config['kommo']['subdomain'], config['kommo']['api_token'])
    
    is_ok, message = client.health_check()
    assert is_ok is True, f"Falha na conexão para {client_id}: {message}"