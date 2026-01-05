import json
import os
from dotenv import load_dotenv

class ConfigLoader:
    @staticmethod
    def load_client_config(client_filename):
        # Passar o caminho absoluto - config está na raiz do projeto
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_path, 'config', f"{client_filename}.json")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Busca o token no .env baseado no nome do arquivo
        env_var_name = f"{client_filename.upper()}_TOKEN"
        config['kommo']['api_token'] = os.getenv(env_var_name)

        return config