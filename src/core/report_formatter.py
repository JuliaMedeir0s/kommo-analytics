from datetime import datetime
from core.analytics import AnalyticsEngine


MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


def build_weekly_message(client_name: str, stats: dict, origins: dict, conversion_pct: float, label_periodo: str) -> str:
    titulo = f"💎 Cliente: {client_name.upper()}"
    subtitulo = "📅 Relatório Semanal"
    msg = (
        f"{titulo}\n"
        f"{subtitulo}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 *Período*\n"
        f"{label_periodo}\n\n"
        f"📥 *Entrada (Leads Novos)*\n"
        f"├ Criados: *{stats['total_created']}*\n"
        f"└ ⚡ Leads Novos Fechados: *{stats['cohort_won']}*\n\n"
        f"🏆 *Resultado (Ganhos Totais)*\n"
        f"├ Vendas Fechadas: *{stats['total_closed_won']}*\n"
        f"└ 📈 Taxa de Conversão: *{conversion_pct}%*\n\n"
        f"📐 *Relação Leads/Venda*\n"
        f"└ *{stats['ratio']}* leads por 1 venda\n\n"
    )

    if origins:
        msg += "🌍 *Origens*\n"
        for idx, (origin, count) in enumerate(origins.items(), 1):
            pct = round((count / stats['total_created'] * 100), 1) if stats['total_created'] > 0 else 0
            msg += f"{idx}. {origin}: *{count}* ({pct}%)\n"
        msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n_Atualizado em análise automática_ ⚙️"
    return msg


def build_monthly_message(client_name: str, stats: dict, origins: dict, conversion_pct: float,
                          total_lost: int, leads_won: list, origin_field_id: int, label_periodo: str,
                          start_ts: int, origin_bot_field_id: int = None) -> str:
    cohort_won = stats['cohort_won']
    old_won = max(stats['total_closed_won'] - cohort_won, 0)

    created_by_origin = origins
    won_by_origin = {}
    for l in leads_won:
        if origin_bot_field_id:
            origin = AnalyticsEngine.get_preferred_origin_value(l, origin_field_id, origin_bot_field_id)
        else:
            origin = AnalyticsEngine.get_origin_value(l, origin_field_id)
        won_by_origin[origin] = won_by_origin.get(origin, 0) + 1

    mes_idx = datetime.fromtimestamp(start_ts).month
    mes_nome = MESES_PT[mes_idx - 1]
    msg = (
        f"🏆 Fechamento Mensal: {mes_nome}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 *Período*\n"
        f"{label_periodo}\n\n"
        f"📊 *Funil de Vendas*\n"
        f"├ Leads Novos: *{stats['total_created']}*\n"
        f"├ Ganhos (Do mês): *{cohort_won}*\n"
        f"└ Ganhos (Antigos): *{old_won}*\n\n"
        f"💰 *Performance Total*\n"
        f"├ Total de Vendas: *{stats['total_closed_won']}*\n"
        f"└ 📉 Leads Perdidos: *{total_lost}*\n\n"
    )

    msg += "🌍 *Performance por Origem*\n"
    for origin, created_count in created_by_origin.items():
        won_count = won_by_origin.get(origin, 0)
        pct = round((won_count / created_count * 100), 1) if created_count > 0 else 0
        msg += f"- {origin}: [Leads: *{created_count}*] | [Vendas: *{won_count}*] | [*{pct}%*]\n"
    msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n_Atualizado em análise automática_ ⚙️"
    return msg


def build_annual_message(client_name: str, stats: dict, origins: dict, leads_won: list, start_ts: int) -> str:
    vendas_por_mes = {}
    for l in leads_won:
        ts = l.get('closed_at') or l.get('updated_at')
        if ts:
            dt = datetime.fromtimestamp(int(ts))
            idx = dt.month
            key = MESES_PT[idx - 1]
            vendas_por_mes[key] = vendas_por_mes.get(key, 0) + 1
    top_meses = sorted(vendas_por_mes.items(), key=lambda x: x[1], reverse=True)

    ano = datetime.fromtimestamp(start_ts).year
    msg = (
        f"🎆 Retrospectiva Anual: {ano}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📈 *Números Globais*\n"
        f"├ Leads Totais: *{stats['total_created']}*\n"
        f"└ Vendas Totais: *{stats['total_closed_won']}*\n\n"
        f"🗓️ *Sazonalidade (Melhores Meses)*\n"
    )

    for idx, (mon, count) in enumerate(top_meses[:6], 1):
        msg += f"{idx}. {mon}: *{count}* vendas\n"
    msg += "\n"

    msg += "🌍 *Domínio de Mercado*\n"
    for origin, count in origins.items():
        pct = round((count / stats['total_created'] * 100), 1) if stats['total_created'] > 0 else 0
        msg += f"- {origin}: *{count}* ({pct}%)\n"
    msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n_Atualizado em análise automática_ ⚙️"
    return msg
