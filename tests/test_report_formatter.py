from src.core.report_formatter import (
    build_weekly_message,
    build_monthly_message,
    build_annual_message,
)


def test_build_weekly_message_ptbr():
    stats = {
        'total_created': 25,
        'cohort_won': 3,
        'total_closed_won': 5,
        'ratio': 5.0,
    }
    origins = {
        'Instagram': 10,
        'Google Ads': 8,
        'Indicação': 7,
    }
    msg = build_weekly_message('Cliente X', stats, origins, 20.0, 'Semana Atual (Dom - Hoje)')
    assert 'Relatório Semanal' in msg
    assert '📅 *Período*' in msg
    assert '📐 *Relação Leads/Venda*' in msg
    assert '🌍 *Origens (Total: 100%)*' in msg


def test_build_monthly_message_ptbr():
    stats = {
        'total_created': 40,
        'cohort_won': 6,
        'total_closed_won': 12,
        'ratio': 3.3,
    }
    origins = {'Instagram': 20, 'Google Ads': 10, 'Indicação': 10}
    leads_won = [{'closed_at': 1700000000, 'updated_at': 1700000000, 'custom_fields_values': []} for _ in range(12)]
    msg = build_monthly_message('Cliente Y', stats, origins, 30.0, 5, leads_won, 0, 'Mês Atual (Até hoje)', 1700000000)
    assert 'Fechamento Mensal' in msg
    assert '📊 *Funil de Vendas*' in msg
    assert '🌍 *Performance por Origem*' in msg


def test_build_annual_message_ptbr():
    stats = {
        'total_created': 400,
        'total_closed_won': 120,
    }
    origins = {'Instagram': 200, 'Google Ads': 120, 'Indicação': 80}
    leads_won = [{'closed_at': 1700000000, 'updated_at': 1700000000} for _ in range(10)]
    msg = build_annual_message('Cliente Z', stats, origins, leads_won, 1700000000)
    assert 'Retrospectiva Anual' in msg
    assert '🗓️ *Sazonalidade (Melhores Meses)*' in msg
    assert '🌍 *Domínio de Mercado*' in msg
