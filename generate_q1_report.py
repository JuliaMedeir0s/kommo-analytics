#!/usr/bin/env python3
"""
Relatório Q1 2026 — Marcela Di Lollo
Cobre: Janeiro, Fevereiro e Março de 2026

Analisa ganhos e perdas por:
  1. Origem automática  (origin_field_id configurado no JSON)
  2. Origem da secretária (secretary_origin_field_id configurado no JSON)

Uso:
  python generate_q1_report.py            → gera o relatório completo
  python generate_q1_report.py --campos   → lista campos customizados disponíveis
"""

import sys
import os
import calendar
import argparse
from datetime import datetime

# Adiciona src/ ao path para reutilizar os módulos existentes
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from dotenv import load_dotenv
load_dotenv()

from core.config_loader import ConfigLoader
from core.analytics import AnalyticsEngine
from integrations.kommo_client import KommoClient

# ─── Constantes ──────────────────────────────────────────────────────────────

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

CLIENT_ID = "marcela_di_lollo"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_month_timestamps(year: int, month: int):
    """Retorna (start_ts, end_ts) para o mês/ano indicados."""
    first = datetime(year, month, 1, 0, 0, 0)
    last_day = calendar.monthrange(year, month)[1]
    last = datetime(year, month, last_day, 23, 59, 59)
    return int(first.timestamp()), int(last.timestamp())


def fetch_all_leads(client: KommoClient, params: dict) -> list:
    """Busca leads com paginação automática."""
    return (
        client._request_get_all_pages(f"{client.base_url}/leads", params)
        .get("_embedded", {})
        .get("leads", [])
    )


def origin_breakdown(leads: list, field_id: int) -> dict:
    """Agrupa leads por valor do campo `field_id`. Retorna dict ordenado por volume."""
    counts: dict = {}
    for lead in leads:
        val = AnalyticsEngine.get_origin_value(lead, field_id)
        counts[val] = counts.get(val, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def print_origin_table(title: str, created_by_origin: dict, won_by_origin: dict, total_created: int):
    """Imprime tabela de origem com colunas: Leads | % Leads | Ganhos | Conv%."""
    print(f"\n  {title}")
    print(f"  {'Origem':<32} {'Leads':>6}  {'% Leads':>7}  {'Ganhos':>7}  {'Conv%':>6}")
    print(f"  {'─'*32} {'─'*6}  {'─'*7}  {'─'*7}  {'─'*6}")
    for origin, created in created_by_origin.items():
        won = won_by_origin.get(origin, 0)
        pct_leads = round(created / total_created * 100, 1) if total_created else 0.0
        conv = round(won / created * 100, 1) if created else 0.0
        print(f"  {origin:<32} {created:>6}  {pct_leads:>6.1f}%  {won:>7}  {conv:>5.1f}%")


def print_origin_table_q1(title: str, origins_q1: dict, total_created_q1: int):
    """Imprime tabela de origem consolidada do Q1."""
    print(f"\n  {title}")
    print(f"  {'Origem':<32} {'Leads':>6}  {'% Leads':>7}  {'Ganhos':>7}  {'Conv%':>6}")
    print(f"  {'─'*32} {'─'*6}  {'─'*7}  {'─'*7}  {'─'*6}")
    sorted_items = sorted(origins_q1.items(), key=lambda x: x[1][0], reverse=True)
    for origin, (c, w) in sorted_items:
        pct_o = round(c / total_created_q1 * 100, 1) if total_created_q1 else 0.0
        conv_o = round(w / c * 100, 1) if c else 0.0
        print(f"  {origin:<32} {c:>6}  {pct_o:>6.1f}%  {w:>7}  {conv_o:>5.1f}%")


def markdown_origin_table(created_by_origin: dict, won_by_origin: dict, total_created: int) -> list:
    """Retorna linhas Markdown para tabela de origem mensal."""
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


def markdown_origin_table_q1(origins_q1: dict, total_created_q1: int) -> list:
    """Retorna linhas Markdown para tabela de origem consolidada Q1."""
    lines = [
        "| Origem | Leads | % Leads | Ganhos | Conv% |",
        "|---|---:|---:|---:|---:|",
    ]
    sorted_items = sorted(origins_q1.items(), key=lambda x: x[1][0], reverse=True)
    for origin, (created, won) in sorted_items:
        pct = round(created / total_created_q1 * 100, 1) if total_created_q1 else 0.0
        conv = round(won / created * 100, 1) if created else 0.0
        lines.append(f"| {origin} | {created} | {pct:.1f}% | {won} | {conv:.1f}% |")
    return lines


def discover_fields(client: KommoClient):
    """Lista todos os campos customizados dos leads para identificar o campo da secretária."""
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


# ─── Acumulador de origens Q1 ─────────────────────────────────────────────────

def accumulate_origins(dest: dict, created_origins: dict, won_origins: dict):
    """Acumula [leads_criados, ganhos] por origem no dict `dest` (in-place)."""
    for origin, count in created_origins.items():
        if origin not in dest:
            dest[origin] = [0, 0]
        dest[origin][0] += count
    for origin, count in won_origins.items():
        if origin not in dest:
            dest[origin] = [0, 0]
        dest[origin][1] += count


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Relatório Q1 2026 — Marcela Di Lollo")
    parser.add_argument(
        "--campos",
        action="store_true",
        help="Lista os campos customizados disponíveis no Kommo e encerra",
    )
    parser.add_argument(
        "--md-output",
        default="relatorio_q1_marcela_di_lollo.md",
        help="Caminho do arquivo .md de saída (padrão: relatorio_q1_marcela_di_lollo.md)",
    )
    args = parser.parse_args()

    # Carrega config e inicializa cliente
    config = ConfigLoader.load_client_config(CLIENT_ID)
    client = KommoClient(config["kommo"]["subdomain"], config["kommo"]["api_token"])

    # Verifica conexão
    is_ok, msg = client.health_check()
    if not is_ok:
        print(f"\n❌ Falha na conexão com Kommo: {msg}")
        sys.exit(1)

    # Modo descoberta de campos
    if args.campos:
        discover_fields(client)
        return

    origin_field_id = config["kommo"]["origin_field_id"]          # origem automática
    secretary_field_id = config["kommo"].get("secretary_origin_field_id")  # secretária
    pipeline_id = config["kommo"]["pipeline_id"]
    won_status_id = config["kommo"]["won_status_id"]
    lost_status_id = config["kommo"]["lost_status_id"]

    # Aviso se campo da secretária não configurado
    if not secretary_field_id:
        print(
            "\n⚠️  O campo 'secretary_origin_field_id' não está configurado em\n"
            "   config/marcela_di_lollo.json.\n\n"
            "   Execute  python generate_q1_report.py --campos  para listar\n"
            "   os campos disponíveis e identificar o campo correto.\n"
        )
        print("   Continuando relatório apenas com a origem automática...\n")

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    print()
    print("=" * 65)
    print(f"  RELATÓRIO Q1 2026 — {config['client_name'].upper()}")
    print(f"  Janeiro, Fevereiro e Março de 2026")
    print("=" * 65)

    # Totais acumulados
    total_created_q1 = 0
    total_won_q1 = 0
    total_lost_q1 = 0
    q1_origins_auto: dict = {}
    q1_origins_sec: dict = {}
    monthly_rows: list = []
    md_sections: list = []

    # ── Loop por mês ─────────────────────────────────────────────────────────
    for month in (1, 2, 3):
        start_ts, end_ts = get_month_timestamps(2026, month)
        mes = MESES_PT[month - 1]

        # Leads criados no mês (na pipeline principal)
        leads_created = fetch_all_leads(
            client,
            {
                "filter[created_at][from]": start_ts,
                "filter[created_at][to]": end_ts,
                "filter[pipeline_id][0]": pipeline_id,
            },
        )

        # Leads fechados como GANHO no mês
        leads_won = fetch_all_leads(
            client,
            {
                "filter[pipeline_id][0]": pipeline_id,
                "filter[status][0]": won_status_id,
                "filter[closed_at][from]": start_ts,
                "filter[closed_at][to]": end_ts,
            },
        )

        # Leads fechados como PERDIDO no mês
        leads_lost = fetch_all_leads(
            client,
            {
                "filter[pipeline_id][0]": pipeline_id,
                "filter[status][0]": lost_status_id,
                "filter[closed_at][from]": start_ts,
                "filter[closed_at][to]": end_ts,
            },
        )

        n_created = len(leads_created)
        n_won = len(leads_won)
        n_lost = len(leads_lost)
        conv = round(n_won / n_created * 100, 1) if n_created else 0.0

        total_created_q1 += n_created
        total_won_q1 += n_won
        total_lost_q1 += n_lost

        # ── Cabeçalho do mês ─────────────────────────────────────────────────
        print(f"\n{'─' * 65}")
        print(f"  📅 {mes.upper()} 2026")
        print(f"{'─' * 65}")
        print(f"  📥  Leads criados  : {n_created}")
        print(f"  ✅  Ganhos         : {n_won}")
        print(f"  ❌  Perdidos       : {n_lost}")
        print(f"  📈  Conversão      : {conv:.1f}%")

        # ── Origem automática ─────────────────────────────────────────────────
        auto_created = origin_breakdown(leads_created, origin_field_id)
        auto_won = {}
        for lead in leads_won:
            val = AnalyticsEngine.get_origin_value(lead, origin_field_id)
            auto_won[val] = auto_won.get(val, 0) + 1

        print_origin_table("🌍 Origem (automática)", auto_created, auto_won, n_created)
        accumulate_origins(q1_origins_auto, auto_created, auto_won)

        sec_created = None
        sec_won = None

        # ── Origem secretária ─────────────────────────────────────────────────
        if secretary_field_id:
            sec_created = origin_breakdown(leads_created, secretary_field_id)
            sec_won = {}
            for lead in leads_won:
                val = AnalyticsEngine.get_origin_value(lead, secretary_field_id)
                sec_won[val] = sec_won.get(val, 0) + 1

            print_origin_table("📝 Origem (secretária)", sec_created, sec_won, n_created)
            accumulate_origins(q1_origins_sec, sec_created, sec_won)

        monthly_rows.append({
            "mes": mes,
            "created": n_created,
            "won": n_won,
            "lost": n_lost,
            "conv": conv,
        })

        month_md = [
            f"## {mes} 2026",
            "",
            "| Métrica | Valor |",
            "|---|---:|",
            f"| Leads criados | {n_created} |",
            f"| Ganhos | {n_won} |",
            f"| Perdidos | {n_lost} |",
            f"| Conversão | {conv:.1f}% |",
            "",
            "### Origem (automática)",
            "",
            *markdown_origin_table(auto_created, auto_won, n_created),
            "",
        ]
        if secretary_field_id and sec_created is not None and sec_won is not None:
            month_md.extend([
                "### Origem (secretária)",
                "",
                *markdown_origin_table(sec_created, sec_won, n_created),
                "",
            ])
        md_sections.extend(month_md)

    # ── Resumo Q1 ─────────────────────────────────────────────────────────────
    conv_q1 = round(total_won_q1 / total_created_q1 * 100, 1) if total_created_q1 else 0.0

    print(f"\n{'=' * 65}")
    print(f"  📊 RESUMO Q1 2026 — JANEIRO + FEVEREIRO + MARÇO")
    print(f"{'=' * 65}")
    print(f"  📥  Total Leads    : {total_created_q1}")
    print(f"  ✅  Total Ganhos   : {total_won_q1}")
    print(f"  ❌  Total Perdidos : {total_lost_q1}")
    print(f"  📈  Conversão Q1   : {conv_q1:.1f}%")

    print_origin_table_q1("🌍 ORIGEM AUTOMÁTICA — Q1", q1_origins_auto, total_created_q1)

    if secretary_field_id:
        print_origin_table_q1("📝 ORIGEM SECRETÁRIA — Q1", q1_origins_sec, total_created_q1)

    print(f"\n{'=' * 65}")
    print(f"  ✅  Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'=' * 65}\n")

    # ── Geração do relatório em Markdown ────────────────────────────────────
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
    md_lines = [
        "# Relatório Q1 2026 — Marcela Di Lollo",
        "",
        "Período: **Janeiro, Fevereiro e Março de 2026**",
        "",
        "## Visão geral",
        "",
        "| Mês | Leads criados | Ganhos | Perdidos | Conversão |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in monthly_rows:
        md_lines.append(
            f"| {row['mes']} | {row['created']} | {row['won']} | {row['lost']} | {row['conv']:.1f}% |"
        )

    md_lines.extend([
        f"| **Q1 Total** | **{total_created_q1}** | **{total_won_q1}** | **{total_lost_q1}** | **{conv_q1:.1f}%** |",
        "",
        *md_sections,
        "## Consolidado Q1 — Origem automática",
        "",
        *markdown_origin_table_q1(q1_origins_auto, total_created_q1),
        "",
    ])

    if secretary_field_id:
        md_lines.extend([
            "## Consolidado Q1 — Origem secretária",
            "",
            *markdown_origin_table_q1(q1_origins_sec, total_created_q1),
            "",
        ])

    md_lines.extend([
        f"_Relatório gerado em {timestamp}_",
        "",
    ])

    with open(args.md_output, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"📝 Arquivo Markdown gerado: {args.md_output}")


if __name__ == "__main__":
    main()
