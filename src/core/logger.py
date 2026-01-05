import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    # Cria a pasta de logs se não existir
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger = logging.getLogger("KommoAnalytics")
    logger.setLevel(logging.INFO)

    # Formato da mensagem: Data - Nome - Nível - Mensagem
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Handler 1: Console (Saída colorida/rápida)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Handler 2: Arquivo (Persistência)
    # RotatingFileHandler evita que o arquivo cresça infinitamente (max 5MB, mantém 5 backups)
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=5*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)

    # Adiciona os handlers ao logger
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger

# Instância única para ser importada
logger = setup_logger()