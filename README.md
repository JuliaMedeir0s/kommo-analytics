# Kommo CRM Analytics Automator

Sistema de extração e análise de dados do Kommo CRM para geração de relatórios de performance semanais, mensais e anuais.

## 🚀 Objetivo
Automatizar a coleta de eventos e leads para responder à métrica norteadora: 
**"Quantos leads são necessários para gerar uma conversão?"**

## 📊 Relatórios Gerados
- **Weekly Pulse (Quartas-feiras):** Comparativo visual da performance da semana atual vs. anterior.
- **Monthly Review (Dia 1):** Fechamento do mês anterior e análise de coorte.
- **Annual Insights (Janeiro):** Sazonalidade e melhores meses do ano anterior.

## 🛠️ Tech Stack
- **Linguagem:** Python 3.10+
- **APIs:** Kommo CRM, Telegram Bot API
- **Arquitetura:** Modular (Preparada para N clientes)

## 🔧 Configuração Inicial
1. Clone o repositório: `git clone https://github.com/seu-usuario/kommo-analytics.git`
2. Crie um ambiente virtual: `python -m venv venv`
3. Instale as dependências: `pip install -r requirements.txt`
4. Configure o arquivo `.env` com suas credenciais.

## 📈 Métricas Calculadas
- Taxa de conversão (Leads criados vs Ganhos)
- Volume por Origem
- Eficiência de funil
