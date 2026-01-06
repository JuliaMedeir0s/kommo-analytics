import os
import json
from core.logger import logger


def get_client_by_chat_id(chat_id: int | str) -> str | None:
    """
    Busca qual cliente está associado a um chat_id específico.
    Retorna o client_id (nome do arquivo sem .json) ou None se não encontrar.
    """
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
    
    try:
        for filename in os.listdir(config_dir):
            if not filename.endswith('.json'):
                continue
                
            filepath = os.path.join(config_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            configured_chat_id = config.get('notifications', {}).get('telegram_chat_id')
            
            # Compara como string para evitar problemas de tipo
            if str(configured_chat_id) == str(chat_id):
                return filename.replace('.json', '')
                
    except Exception as e:
        logger.error(f"Erro ao buscar cliente por chat_id {chat_id}: {e}")
        
    return None
