#!/usr/bin/env python3
"""
Descobre automaticamente a configuração de um cliente no Kommo via API.
Valida token e extrai subdomain, pipelines, status_ids e field_ids.

Uso:
  python discover_kommo_config.py clinica_apuana
  python discover_kommo_config.py eliney_faria
"""

import sys
import os
import json
from os.path import dirname, abspath

sys.path.insert(0, os.path.join(dirname(abspath(__file__)), "src"))

from dotenv import load_dotenv
load_dotenv()

from core.config_loader import ConfigLoader
from integrations.kommo_client import KommoClient


def discover_config(client_id: str):
    """Descobre e exibe a configuração de um cliente."""
    
    # Carrega token do .env
    env_var_name = f"{client_id.upper()}_TOKEN"
    token = os.getenv(env_var_name)
    
    if not token:
        print(f"❌ Token {env_var_name} não encontrado no .env")
        return None
    
    # Extrai o subdomain do token (campo base_domain no JWT)
    import base64
    try:
        # JWT tem 3 partes: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            print("❌ Token inválido")
            return None
        
        # Decode payload (adiciona padding se necessário)
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)
        
        base_domain = data.get('base_domain', 'kommo.com')
        account_id = data.get('account_id')
        api_domain = data.get('api_domain')
        
        print(f"\n📊 Token Decode:")
        print(f"  Base Domain: {base_domain}")
        print(f"  Account ID: {account_id}")
        print(f"  API Domain: {api_domain}")
        print()
    except Exception as e:
        print(f"❌ Erro ao decodificar token: {e}")
        return None
    
    # Tenta descobrir o subdomain via account endpoint
    # Teste com subdomain genérico
    test_subdomains = [
        "clinicaapuana",
        "clinic-apuana", 
        "apuana",
        "clincapuana",
    ]
    
    subdomain = None
    account_name = None
    
    for test_subdomain in test_subdomains:
        try:
            client = KommoClient(test_subdomain, token)
            is_ok, msg = client.health_check()
            if is_ok:
                subdomain = test_subdomain
                account_name = msg.split(":")[-1].strip() if ":" in msg else msg
                print(f"✅ Subdomain encontrado: {subdomain}")
                print(f"   Conta: {account_name}")
                break
        except:
            pass
    
    if not subdomain:
        print("❌ Não consegui descobrir o subdomain. Tente uma das alternativas:")
        for sd in test_subdomains:
            print(f"   - {sd}")
        return None
    
    # Agora que temos o subdomain e client válido
    client = KommoClient(subdomain, token)
    
    # 1. Listar pipelines
    print(f"\n📋 Descobrindo pipelines...")
    try:
        response = client._request_get(f"{client.base_url}/leads/pipelines", {})
        pipelines = response.get("_embedded", {}).get("pipelines", [])
        if pipelines:
            print(f"   Pipelines encontradas:")
            for p in pipelines:
                pid = p.get("id")
                pname = p.get("name")
                print(f"     - ID: {pid:>15} | Nome: {pname}")
        else:
            print("   Nenhuma pipeline encontrada")
    except Exception as e:
        print(f"   ❌ Erro ao listar pipelines: {e}")
        pipelines = []
    
    # 2. Listar custom fields
    print(f"\n🏷️ Descobrindo custom fields...")
    try:
        data = client.get_lead_custom_fields()
        fields = data.get("_embedded", {}).get("custom_fields", [])
        origin_fields = [f for f in fields if "origem" in f.get("name", "").lower()]
        if origin_fields:
            print(f"   Campos de origem encontrados:")
            for f in origin_fields:
                fid = f.get("id")
                fname = f.get("name")
                ftype = f.get("type")
                print(f"     - ID: {fid:>15} | Nome: {fname:<40} | Tipo: {ftype}")
        else:
            print("   Nenhum campo de origem encontrado")
    except Exception as e:
        print(f"   ❌ Erro ao listar campos: {e}")
    
    # 3. Tentar puxar leads para descobrir status IDs
    print(f"\n📊 Descobrindo status IDs...")
    try:
        if pipelines:
            pipeline_id = pipelines[0].get("id")
            leads = client.get_leads(pipeline_id=pipeline_id)
            if leads:
                statuses = set()
                for lead in leads[:50]:  # Check primeiros 50
                    status_id = lead.get("status_id")
                    if status_id:
                        statuses.add(status_id)
                if statuses:
                    print(f"   Status IDs encontrados nos leads: {sorted(statuses)}")
                    print(f"   (Geralmente: 142=Ganho, 143=Perdido)")
            else:
                print("   Nenhum lead encontrado para descobrir status IDs")
        else:
            print("   Sem pipelines para descobrir status IDs")
    except Exception as e:
        print(f"   ❌ Erro ao descobrir status IDs: {e}")
    
    # Gera template de config
    print(f"\n✅ Template de config para {client_id}:")
    print(f"""
{{
    "client_name": "Clínica Apuana",
    "kommo": {{
        "subdomain": "{subdomain}",
        "origin_field_id": 0,  # PREENCHER: ID do campo de origem automática
        "secretary_origin_field_id": 0,  # PREENCHER (opcional): ID do campo de origem manual
        "won_status_id": 142,
        "lost_status_id": 143,
        "pipeline_id": {pipelines[0].get('id') if pipelines else 0},
        "pipeline_followup_id": []
    }},
    "notifications": {{
        "telegram_chat_id": "SEU_CHAT_ID",
        "clickup_list_id": "SEU_LIST_ID"
    }},
    "settings": {{
        "report_day": "Wednesday",
        "timezone": "America/Sao_Paulo"
    }}
}}
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python discover_kommo_config.py <client_id>")
        print("Exemplo: python discover_kommo_config.py clinica_apuana")
        sys.exit(1)
    
    client_id = sys.argv[1]
    discover_config(client_id)
