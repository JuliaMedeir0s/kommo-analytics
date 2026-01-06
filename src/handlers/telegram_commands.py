COMMAND_MAP = {
    "/semana": "weekly",
    "/semanapassada": "last_week",
    "/ultima_semana": "last_week",
    "/mes": "current_month",
    "/mespassado": "last_month",
    "/ultimo_mes": "last_month",
    "/ano": "yearly",
    "/anopassado": "last_year",
    "/ultimo_ano": "last_year",
    
    # Exportação completa (todas categorias)
    "/exportar": "export_all",
    "/exportar_15dias": "export_all_15days",
    "/exportar_semana": "export_all_weekly",
    "/exportar_semanapassada": "export_all_last_week",
    "/exportar_mes": "export_all_monthly",
    "/exportar_mespassado": "export_all_last_month",
    "/exportar_ano": "export_all_yearly",
    "/exportar_anopassado": "export_all_last_year",
    
    # Exportação por categoria - histórico completo
    "/exportar_ganhos": "export_won",
    "/exportar_perdidos": "export_lost",
    "/exportar_perdidos_followup": "export_lost_followup",
    "/exportar_ativos": "export_active",
    
    # Exportação por categoria - últimos 15 dias
    "/exportar_ganhos_15dias": "export_won_15days",
    "/exportar_perdidos_15dias": "export_lost_15days",
    "/exportar_ativos_15dias": "export_active_15days",
    "/exportar_perdidos_followup_15dias": "export_lost_followup_15days",
    
    # Exportação por categoria - com período
    "/exportar_ganhos_semana": "export_won_weekly",
    "/exportar_ganhos_mes": "export_won_monthly",
    "/exportar_ganhos_ano": "export_won_yearly",
    "/exportar_perdidos_semana": "export_lost_weekly",
    "/exportar_perdidos_mes": "export_lost_monthly",
    "/exportar_perdidos_ano": "export_lost_yearly",
    "/exportar_ativos_semana": "export_active_weekly",
    "/exportar_ativos_mes": "export_active_monthly",
    "/exportar_ativos_ano": "export_active_yearly",
    "/exportar_perdidos_followup_semana": "export_lost_followup_weekly",
    "/exportar_perdidos_followup_mes": "export_lost_followup_monthly",
    "/exportar_perdidos_followup_ano": "export_lost_followup_yearly",
    
    "/help": "help",
    "/start": "help",
}


def normalize_command(text: str) -> str:
    return (text or "").strip().lower()


def resolve_report_type(command: str):
    cmd = normalize_command(command)
    return COMMAND_MAP.get(cmd)


def help_message() -> str:
    return (
        "🤖 *KOMMO ANALYTICS BOT*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 *RELATÓRIOS (Texto)*\n"
        "Período Atual:\n"
        "  /semana — Semana atual (Dom-Hoje)\n"
        "  /mes — Mês atual (até hoje)\n"
        "  /ano — Ano atual (até hoje)\n\n"
        "Período Anterior:\n"
        "  /semanapassada — Semana passada (Dom-Sáb)\n"
        "  /mespassado — Mês anterior (fechado)\n"
        "  /anopassado — Ano anterior (retrospectiva)\n\n"
        "📥 *EXPORTAR DADOS (Excel + CSV)*\n\n"
        "*Exportação Completa (todas as 4 categorias):*\n"
        "  /exportar_15dias — Últimos 15 dias (8 arquivos)\n"
        "  /exportar — Histórico completo\n"
        "  /exportar_semana — Semana atual\n"
        "  /exportar_semanapassada — Semana passada\n"
        "  /exportar_mes — Mês atual\n"
        "  /exportar_mespassado — Mês anterior\n"
        "  /exportar_ano — Ano atual\n"
        "  /exportar_anopassado — Ano anterior\n\n"
        "*Exportação por Categoria - Histórico Completo:*\n"
        "  /exportar_ganhos — Ganhos\n"
        "  /exportar_perdidos — Perdidos\n"
        "  /exportar_ativos — Ativos\n"
        "  /exportar_perdidos_followup — Perdidos Follow-up\n\n"
        "*Exportação por Categoria - Últimos 15 dias:*\n"
        "  /exportar_ganhos_15dias\n"
        "  /exportar_perdidos_15dias\n"
        "  /exportar_ativos_15dias\n"
        "  /exportar_perdidos_followup_15dias\n\n"
        "*Exportação por Categoria - Semana Atual:*\n"
        "  /exportar_ganhos_semana\n"
        "  /exportar_perdidos_semana\n"
        "  /exportar_ativos_semana\n"
        "  /exportar_perdidos_followup_semana\n\n"
        "*Exportação por Categoria - Mês Atual:*\n"
        "  /exportar_ganhos_mes\n"
        "  /exportar_perdidos_mes\n"
        "  /exportar_ativos_mes\n"
        "  /exportar_perdidos_followup_mes\n\n"
        "*Exportação por Categoria - Ano Atual:*\n"
        "  /exportar_ganhos_ano\n"
        "  /exportar_perdidos_ano\n"
        "  /exportar_ativos_ano\n"
        "  /exportar_perdidos_followup_ano\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ Dúvidas? Use /help\n"
    )
