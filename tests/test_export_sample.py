"""
Script de teste para verificar como os dados das exportações estão retornando
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Carregar variáveis de ambiente ANTES de importar
from dotenv import load_dotenv
load_dotenv()

import json
from datetime import datetime, timedelta
from core.config_loader import ConfigLoader
from core.exports import ExportEngine

# Carrega configuração de um cliente
client_id = "marcela_di_lollo"  # Altere para o cliente que quiser testar
config = ConfigLoader.load_client_config(client_id)

print(f"🔍 Testando exportação para {client_id}...")
print(f"Pipeline ID: {config['kommo']['pipeline_id']}")
print(f"Status Ganho: {config['kommo']['won_status_id']}")
print(f"Status Perdido: {config['kommo']['lost_status_id']}")
print()

# Calcula período de 15 dias
end_date = datetime.now()
start_date = end_date - timedelta(days=15)
period_timestamps = (int(start_date.timestamp()), int(end_date.timestamp()))

print(f"📅 Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
print()

# Gera exportações com filtro de 15 dias
result = ExportEngine.generate_exports(
    client_id=client_id,
    config=config,
    period_timestamps=period_timestamps,
    output_dir="./exports_test"
)

print("\n📊 Arquivos gerados:")
for category, files in result.items():
    print(f"\n{category.upper()}:")
    print(f"  Excel: {files['excel']}")
    print(f"  CSV: {files['csv']}")

print("\n✅ Verifique os arquivos na pasta exports_test/ para ver os dados retornados")
