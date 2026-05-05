#!/usr/bin/env python3
"""
Relatório mensal para clientes Kommo — mês anterior ao atual.

Uso:
  python generate_april_report.py
  python generate_april_report.py --client eliney_faria
  python generate_april_report.py --client daniel_dourado
  python generate_april_report.py --client marcela_di_lollo --campos
  python generate_april_report.py --client eliney_faria --md-output relatorio_custom.md
"""

import argparse
import os
import sys
from datetime import datetime, timedelta

# Adiciona src/ ao path para reutilizar os módulos existentes
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from dotenv import load_dotenv

load_dotenv()

from core.analytics import AnalyticsEngine
from core.config_loader import ConfigLoader
from integrations.kommo_client import KommoClient


MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def month_timestamps_to_epoch(start_dt: datetime, end_dt: datetime):
    return int(start_dt.timestamp()), int(end_dt.timestamp())


def get_month_timestamps(year: int, month: int):
    first_day = datetime(year, month, 1, 0, 0, 0)
    if month == 12:
        last_day = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
    else:
        last_day = datetime(year, month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
    return month_timestamps_to_epoch(first_day, last_day)


def fetch_all_leads(client: KommoClient, params: dict) -> list:
    return (
        client._request_get_all_pages(f"{client.base_url}/leads", params)
        .get("_embedded", {})
        .get("leads", [])
    )


def fetch_all_leads_for_pipelines(client: KommoClient, pipeline_ids: list, params_base: dict) -> list:
    """
    Busca leads para múltiplas pipelines e retorna lista única (deduplicada por id).
    """
    all_leads = []
    seen = set()
    for p in pipeline_ids:
        params = params_base.copy()
        params["filter[pipeline_id][0]"] = p
        leads = fetch_all_leads(client, params)
        for lead in leads:
            lid = lead.get("id")
            if lid and lid not in seen:
                seen.add(lid)
                all_leads.append(lead)
    return all_leads


def origin_breakdown(leads: list, field_id: int) -> dict:
    counts: dict = {}
    for lead in leads:
        val = AnalyticsEngine.get_origin_value(lead, field_id)
        counts[val] = counts.get(val, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def markdown_origin_table(created_by_origin: dict, won_by_origin: dict, total_created: int) -> list:
    lines = [
        "| Origem | Leads | % Leads | Ganhos | Conv% |",
        "|---|---:|---:|---:|---:|",
    ]
    for origin, created in created_by_origin.items():
        won = won_by_origin.get(origin, 0)
        pct_leads = round(created / total_created * 100, 1) if total_created else 0.0
        conv = round(won / created * 100, 1) if created else 0.0
        lines.append(f"| {origin} | {created} | {pct_leads:.1f}% | {won} | {conv:.1f}% |")
    return lines


def discover_fields(client: KommoClient):
    print("\n📋 CAMPOS CUSTOMIZADOS DOS LEADS:")
    print("─" * 70)
    data = client.get_lead_custom_fields()
    fields = data.get("_embedded", {}).get("custom_fields", [])
    if not fields:
        print("  Nenhum campo encontrado (verifique o token/subdomínio).")
        return
    for f in sorted(fields, key=lambda x: x.get("name", "")):
        fid = f.get("id", "?")
        fname = f.get("name", "Sem nome")
        ftype = f.get("type", "?")
        print(f"  ID: {fid:>10}  |  {fname:<35}  |  Tipo: {ftype}")
    print("─" * 70)
    print(
        "\n➡️  Identifique o campo preenchido pela secretária e adicione em\n"
        "   config/marcela_di_lollo.json:\n"
        '   "secretary_origin_field_id": <ID>\n'
    )


def print_origin_table(title: str, created_by_origin: dict, won_by_origin: dict, total_created: int):
    print(f"\n  {title}")
    print(f"  {'Origem':<32} {'Leads':>6}  {'% Leads':>7}  {'Ganhos':>7}  {'Conv%':>6}")
    print(f"  {'─'*32} {'─'*6}  {'─'*7}  {'─'*7}  {'─'*6}")
    for origin, created in created_by_origin.items():
        won = won_by_origin.get(origin, 0)
        pct_leads = round(created / total_created * 100, 1) if total_created else 0.0
        conv = round(won / created * 100, 1) if created else 0.0
        print(f"  {origin:<32} {created:>6}  {pct_leads:>6.1f}%  {won:>7}  {conv:>5.1f}%")


def collect_month_report(client: KommoClient, config: dict, year: int, month: int) -> dict:
    origin_field_id = config["kommo"]["origin_field_id"]
    origin_bot_field_id = config["kommo"].get("origin_bot_field_id")
    secretary_field_id = config["kommo"].get("secretary_origin_field_id")
    pipeline_id = config["kommo"]["pipeline_id"]
    pipeline_followups = config["kommo"].get("pipeline_followup_id") or []
    pipeline_ids = [pipeline_id] + pipeline_followups
    won_status_id = config["kommo"]["won_status_id"]
    lost_status_id = config["kommo"]["lost_status_id"]

    start_ts, end_ts = get_month_timestamps(year, month)
    leads_created = fetch_all_leads_for_pipelines(
        client,
        pipeline_ids,
        {
            "filter[created_at][from]": start_ts,
            "filter[created_at][to]": end_ts,
        },
    )
    leads_won = fetch_all_leads_for_pipelines(
        client,
        pipeline_ids,
        {
            "filter[status][0]": won_status_id,
            "filter[closed_at][from]": start_ts,
            "filter[closed_at][to]": end_ts,
        },
    )
    leads_lost = fetch_all_leads_for_pipelines(
        client,
        pipeline_ids,
        {
            "filter[status][0]": lost_status_id,
            "filter[closed_at][from]": start_ts,
            "filter[closed_at][to]": end_ts,
        },
    )

    manual_created = origin_breakdown(leads_created, origin_field_id)
    manual_won = {}
    for lead in leads_won:
        val = AnalyticsEngine.get_origin_value(lead, origin_field_id)
        manual_won[val] = manual_won.get(val, 0) + 1

    bot_created = None
    bot_won = None
    if origin_bot_field_id:
        bot_created = origin_breakdown(leads_created, origin_bot_field_id)
        bot_won = {}
        for lead in leads_won:
            val = AnalyticsEngine.get_origin_value(lead, origin_bot_field_id)
            bot_won[val] = bot_won.get(val, 0) + 1

    sec_created = None
    sec_won = None
    if secretary_field_id:
        sec_created = origin_breakdown(leads_created, secretary_field_id)
        sec_won = {}
        for lead in leads_won:
            val = AnalyticsEngine.get_origin_value(lead, secretary_field_id)
            sec_won[val] = sec_won.get(val, 0) + 1

    n_created = len(leads_created)
    n_won = len(leads_won)
    n_lost = len(leads_lost)
    conv = round(n_won / n_created * 100, 1) if n_created else 0.0

    return {
        "year": year,
        "month": month,
        "month_name": MESES_PT[month - 1],
        "n_created": n_created,
        "n_won": n_won,
        "n_lost": n_lost,
        "conv": conv,
        "manual_created": manual_created,
        "manual_won": manual_won,
        "bot_created": bot_created,
        "bot_won": bot_won,
        "sec_created": sec_created,
        "sec_won": sec_won,
    }


def main():
    parser = argparse.ArgumentParser(description="Relatório mensal — Clientes Kommo")
    parser.add_argument(
        "--client",
        default="marcela_di_lollo",
        help="ID do cliente (ex: marcela_di_lollo, eliney_faria, daniel_dourado, mateus_bretas)",
    )
    parser.add_argument(
        "--campos",
        action="store_true",
        help="Lista os campos customizados disponíveis no Kommo e encerra",
    )
    parser.add_argument(
        "--md-output",
        default=None,
        help="Caminho do arquivo .md de saída",
    )
    parser.add_argument(
        "--year-to-date",
        action="store_true",
        help="Gera um relatório acumulado do ano com um bloco por mês",
    )
    args = parser.parse_args()

    config = ConfigLoader.load_client_config(args.client)
    client = KommoClient(config["kommo"]["subdomain"], config["kommo"]["api_token"])

    is_ok, msg = client.health_check()
    if not is_ok:
        print(f"\n❌ Falha na conexão com Kommo: {msg}")
        sys.exit(1)

    if args.campos:
        discover_fields(client)
        return

    now = datetime.now()
    first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day_previous_month = first_day_this_month - timedelta(seconds=1)
    first_day_previous_month = last_day_previous_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_ts, end_ts = month_timestamps_to_epoch(first_day_previous_month, last_day_previous_month)
    mes_nome = MESES_PT[first_day_previous_month.month - 1]
    ano = first_day_previous_month.year

    print()
    print("=" * 65)
    print(f"  RELATÓRIO MENSAL — {config['client_name'].upper()}")
    print(f"  {mes_nome} de {ano}")
    print("=" * 65)

    if args.year_to_date:
        end_month = max(now.month - 1, 1)
        monthly_reports = [collect_month_report(client, config, ano, month) for month in range(1, end_month + 1)]
        total_created = sum(report["n_created"] for report in monthly_reports)
        total_won = sum(report["n_won"] for report in monthly_reports)
        total_lost = sum(report["n_lost"] for report in monthly_reports)
        conv = round(total_won / total_created * 100, 1) if total_created else 0.0

        print(f"\n{'─' * 65}")
        print(f"  📅 JANEIRO A {MESES_PT[end_month - 1].upper()} {ano}")
        print(f"{'─' * 65}")
        print(f"  📥  Leads criados  : {total_created}")
        print(f"  ✅  Ganhos         : {total_won}")
        print(f"  ❌  Perdidos       : {total_lost}")
        print(f"  📈  Conversão      : {conv:.1f}%")

        md_lines = [
            f"# Relatório YTD {ano} — {config['client_name']}",
            "",
            f"Período: **Janeiro a {MESES_PT[end_month - 1]} de {ano}**",
            "",
            "## Visão geral",
            "",
            "| Métrica | Valor |",
            "|---|---:|",
            f"| Leads criados | {total_created} |",
            f"| Ganhos | {total_won} |",
            f"| Perdidos | {total_lost} |",
            f"| Conversão | {conv:.1f}% |",
            "",
        ]

        for report in monthly_reports:
            print(f"\n  {report['month_name'].upper()} {ano}")
            print(f"  {'─' * 65}")
            print(f"  📥  Leads criados  : {report['n_created']}")
            print(f"  ✅  Ganhos         : {report['n_won']}")
            print(f"  ❌  Perdidos       : {report['n_lost']}")
            print(f"  📈  Conversão      : {report['conv']:.1f}%")
            print_origin_table("📝 Origem (manual)", report['manual_created'], report['manual_won'], report['n_created'])
            if report['bot_created'] is not None and report['bot_won'] is not None:
                print_origin_table("🤖 Origem (automática)", report['bot_created'], report['bot_won'], report['n_created'])
            if report['sec_created'] is not None and report['sec_won'] is not None:
                print_origin_table("📝 Origem (secretária)", report['sec_created'], report['sec_won'], report['n_created'])

            md_lines.extend([
                f"## {report['month_name']} {ano}",
                "",
                "| Métrica | Valor |",
                "|---|---:|",
                f"| Leads criados | {report['n_created']} |",
                f"| Ganhos | {report['n_won']} |",
                f"| Perdidos | {report['n_lost']} |",
                f"| Conversão | {report['conv']:.1f}% |",
                "",
                "### Origem (manual)",
                "",
                *markdown_origin_table(report['manual_created'], report['manual_won'], report['n_created']),
                "",
            ])

            if report['bot_created'] is not None and report['bot_won'] is not None:
                md_lines.extend([
                    "### Origem (automática)",
                    "",
                    *markdown_origin_table(report['bot_created'], report['bot_won'], report['n_created']),
                    "",
                ])

            if report['sec_created'] is not None and report['sec_won'] is not None:
                md_lines.extend([
                    "### Origem (secretária)",
                    "",
                    *markdown_origin_table(report['sec_created'], report['sec_won'], report['n_created']),
                    "",
                ])

        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        md_lines.extend([
            f"_Relatório gerado em {timestamp}_",
            "",
        ])

        output_path = args.md_output or f"relatorio_ytd_{args.client}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        print(f"📝 Arquivo Markdown gerado: {output_path}")
        return

    month_report = collect_month_report(client, config, ano, first_day_previous_month.month)

    print(f"\n{'─' * 65}")
    print(f"  📅 {mes_nome.upper()} {ano}")
    print(f"{'─' * 65}")
    print(f"  📥  Leads criados  : {month_report['n_created']}")
    print(f"  ✅  Ganhos         : {month_report['n_won']}")
    print(f"  ❌  Perdidos       : {month_report['n_lost']}")
    print(f"  📈  Conversão      : {month_report['conv']:.1f}%")

    print_origin_table("📝 Origem (manual)", month_report['manual_created'], month_report['manual_won'], month_report['n_created'])

    if month_report['bot_created'] is not None and month_report['bot_won'] is not None:
        print_origin_table("🤖 Origem (automática)", month_report['bot_created'], month_report['bot_won'], month_report['n_created'])

    if month_report['sec_created'] is not None and month_report['sec_won'] is not None:
        print_origin_table("📝 Origem (secretária)", month_report['sec_created'], month_report['sec_won'], month_report['n_created'])

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    md_lines = [
        f"# Relatório {mes_nome} {ano} — {config['client_name']}",
        "",
        f"Período: **{mes_nome} de {ano}**",
        "",
        "## Visão geral",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| Leads criados | {month_report['n_created']} |",
        f"| Ganhos | {month_report['n_won']} |",
        f"| Perdidos | {month_report['n_lost']} |",
        f"| Conversão | {month_report['conv']:.1f}% |",
        "",
        "### Origem (manual)",
        "",
        *markdown_origin_table(month_report['manual_created'], month_report['manual_won'], month_report['n_created']),
        "",
    ]

    if month_report['bot_created'] is not None and month_report['bot_won'] is not None:
        md_lines.extend([
            "### Origem (automática)",
            "",
            *markdown_origin_table(month_report['bot_created'], month_report['bot_won'], month_report['n_created']),
            "",
        ])

    if month_report['sec_created'] is not None and month_report['sec_won'] is not None:
        md_lines.extend([
            "### Origem (secretária)",
            "",
            *markdown_origin_table(month_report['sec_created'], month_report['sec_won'], month_report['n_created']),
            "",
        ])

    md_lines.extend([
        f"_Relatório gerado em {timestamp}_",
        "",
    ])

    output_path = args.md_output or f"relatorio_{mes_nome.lower()}_{args.client}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"📝 Arquivo Markdown gerado: {output_path}")


if __name__ == "__main__":
    main()