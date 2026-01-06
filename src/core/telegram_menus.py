def main_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "Relatórios 📊", "callback_data": "menu_reports"},
                {"text": "Exportações 📥", "callback_data": "menu_exports"},
            ],
            [
                {"text": "Ajuda ✨", "callback_data": "menu_help"},
            ],
        ]
    }


def reports_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "Semana Atual", "callback_data": "cmd:/semana"},
                {"text": "Semana Passada", "callback_data": "cmd:/semanapassada"},
            ],
            [
                {"text": "Mês Atual", "callback_data": "cmd:/mes"},
                {"text": "Mês Passado", "callback_data": "cmd:/mespassado"},
            ],
            [
                {"text": "Ano Atual", "callback_data": "cmd:/ano"},
                {"text": "Ano Passado", "callback_data": "cmd:/anopassado"},
            ],
            [
                {"text": "🔙 Voltar", "callback_data": "menu_main"},
            ],
        ]
    }


def exports_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "Últimos 15 dias (8 arquivos)", "callback_data": "cmd:/exportar_15dias"},
            ],
            [
                {"text": "Exportar Semana", "callback_data": "cmd:/exportar_semana"},
                {"text": "Exportar Mês", "callback_data": "cmd:/exportar_mes"},
                {"text": "Exportar Ano", "callback_data": "cmd:/exportar_ano"},
            ],
            [
                {"text": "Ganhos 15d", "callback_data": "cmd:/exportar_ganhos_15dias"},
                {"text": "Perdidos 15d", "callback_data": "cmd:/exportar_perdidos_15dias"},
            ],
            [
                {"text": "Ativos 15d", "callback_data": "cmd:/exportar_ativos_15dias"},
                {"text": "Follow-up 15d", "callback_data": "cmd:/exportar_perdidos_followup_15dias"},
            ],
            [
                {"text": "🔙 Voltar", "callback_data": "menu_main"},
            ],
        ]
    }
