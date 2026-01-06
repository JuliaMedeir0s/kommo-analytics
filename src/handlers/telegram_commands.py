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
        "Comandos disponíveis:\n"
        "• /semana — Semana atual (Dom-Hoje)\n"
        "• /semanapassada — Semana passada (Dom-Sáb)\n"
        "• /mes — Mês atual (Mês até hoje)\n"
        "• /mespassado — Mês anterior (fechado)\n"
        "• /ano — Ano atual (até hoje)\n"
        "• /anopassado — Ano anterior (retrospectiva)\n"
    )
