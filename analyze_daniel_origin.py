#!/usr/bin/env python3
"""
Análise de leads por origem para Daniel Dourado em Abril 2026.
Mostra quantos leads chegaram de cada origem SEM considerar conversão.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from dotenv import load_dotenv
load_dotenv()

from core.config_loader import ConfigLoader
from core.analytics import AnalyticsEngine
from integrations.kommo_client import KommoClient


def get_month_timestamps(year: int, month: int):
    from datetime import timedelta
    first_day = datetime(year, month, 1, 0, 0, 0)
    if month == 12:
        last_day = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
    else:
        last_day = datetime(year, month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
    return int(first_day.timestamp()), int(last_day.timestamp())


def fetch_all_leads(client: KommoClient, params: dict) -> list:
    return (
        client._request_get_all_pages(f"{client.base_url}/leads", params)
        .get("_embedded", {})
        .get("leads", [])
    )


config = ConfigLoader.load_client_config("daniel_dourado")
client = KommoClient(config["kommo"]["subdomain"], config["kommo"]["api_token"])

is_ok, msg = client.health_check()
if not is_ok:
    print(f"❌ Falha na conexão: {msg}")
    sys.exit(1)

origin_field_id = config["kommo"]["origin_field_id"]
pipeline_id = config["kommo"]["pipeline_id"]
pipeline_followups = config["kommo"].get("pipeline_followup_id") or []
pipeline_ids = [pipeline_id] + pipeline_followups

start_ts, end_ts = get_month_timestamps(2026, 4)

# Busca todos os leads criados em abril
leads_created = []
for p in pipeline_ids:
    params = {
        "filter[created_at][from]": start_ts,
        "filter[created_at][to]": end_ts,
        "filter[pipeline_id][0]": p,
    }
    leads_created.extend(fetch_all_leads(client, params))

# Remove duplicatas por ID
seen = set()
unique_leads = []
for lead in leads_created:
    lid = lead.get("id")
    if lid and lid not in seen:
        seen.add(lid)
        unique_leads.append(lead)

# Agrupa por origem
by_origin = {}
for lead in unique_leads:
    origin = AnalyticsEngine.get_origin_value(lead, origin_field_id)
    by_origin[origin] = by_origin.get(origin, 0) + 1

# Ordena por quantidade (desc)
sorted_origins = sorted(by_origin.items(), key=lambda x: x[1], reverse=True)

print()
print("=" * 70)
print("  ANÁLISE DE LEADS POR ORIGEM — DANIEL DOURADO — ABRIL 2026")
print("=" * 70)
print()
print(f"  {'Origem':<40} {'Leads':>10}  {'%':>6}")
print(f"  {'─'*40} {'─'*10}  {'─'*6}")

total = len(unique_leads)
for origin, count in sorted_origins:
    pct = round(count / total * 100, 1) if total else 0.0
    print(f"  {origin:<40} {count:>10}  {pct:>5.1f}%")

print(f"  {'─'*40} {'─'*10}  {'─'*6}")
print(f"  {'TOTAL':<40} {total:>10}  {'100.0%':>6}")
print()
print("=" * 70)
print()
