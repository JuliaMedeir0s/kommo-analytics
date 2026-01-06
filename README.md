## Relatórios e Comandos

### Comandos de Relatório (texto)
- `/semana`: Semana atual (Dom-Hoje)
- `/semanapassada`: Semana passada (Dom-Sáb)
- `/mes`: Mês atual (até hoje)
- `/mespassado`: Mês anterior (fechado)
- `/ano`: Ano atual (até hoje)
- `/anopassado`: Ano anterior (retrospectiva)

### Comandos de Exportação (Excel + CSV)
- `/exportar_15dias`: Todas as categorias dos últimos 15 dias (8 arquivos)
- `/exportar`: Histórico completo (todas categorias)
- `/exportar_semana`, `/exportar_semanapassada`, `/exportar_mes`, `/exportar_mespassado`, `/exportar_ano`, `/exportar_anopassado`
- Por categoria: `ganhos`, `perdidos`, `ativos`, `perdidos_followup` com sufixos `_15dias`, `_semana`, `_mes`, `_ano`

### Layouts dos Relatórios

#### Relatório Semanal
Foco: Ritmo e Eficiência.
- Entrada (Leads Novos): Criados, Leads Novos Fechados
- Resultado (Ganhos Totais): Vendas Fechadas, Taxa de Conversão
- Relação Leads/Venda: Ratio (leads por 1 venda)
- Origens: Lista completa com percentual

#### Relatório Mensal
Foco: Saúde do Funil e ROI.
- Funil de Vendas: Leads Novos, Ganhos (do mês), Ganhos (antigos)
- Performance Total: Total de Vendas, Leads Perdidos
- Performance por Origem: [Leads] | [Vendas] | [%]

#### Relatório Anual
Foco: Sazonalidade e Direcionamento de Verba.
- Números Globais: Leads Totais, Vendas Totais
- Sazonalidade: melhores meses por vendas
- Domínio de Mercado: origens acumuladas no ano

### Testes
Os testes cobrem integrações e o formatter de relatórios:
- `tests/test_integration_telegram.py`: envio e saúde do bot
- `tests/test_integration_kommo.py`: conexão e integridade por cliente
- `tests/test_report_formatter.py`: verificação de seções e termos em Português

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

## 🤖 Comandos do Bot (Telegram)

### Relatórios Automáticos:
- /semana — Semana atual (Dom-Hoje)
- /semanapassada — Semana passada (Dom-Sáb)
- /mes — Mês atual (mês até hoje)
- /mespassado — Mês anterior (fechado)
- /ano — Ano atual (até hoje)
- /anopassado — Ano anterior (retrospectiva)

### Exportação Completa (todas categorias):
- /exportar — Histórico completo (8 arquivos)
- /exportar_semana — Semana atual
- /exportar_mes — Mês atual
- /exportar_ano — Ano atual

### Exportação por Categoria:
Combine categoria + período opcional:
- **Categorias:** ganhos, perdidos, ativos, perdidos_followup
- **Períodos:** (nenhum) = histórico, _semana, _mes, _ano

Exemplos:
- /exportar_ganhos — Todos ganhos (histórico)
- /exportar_ganhos_semana — Ganhos da semana atual
- /exportar_perdidos_mes — Perdidos do mês atual
- /exportar_ativos_ano — Ativos do ano atual

### Outros:
- /help — Lista os comandos

## 🌐 Webhook FastAPI
Um endpoint simples recebe o `update` do Telegram e dispara o pipeline em segundo plano.

1. Configure o `.env` com `TELEGRAM_BOT_TOKEN` e os tokens de cada cliente (`<CLIENTE>_TOKEN`).
2. Instale dependências: `pip install -r requirements.txt`
3. Rode o servidor: `uvicorn telegram_webhook:app --host 0.0.0.0 --port 8000`
4. Aponte o webhook do bot para `https://<sua-url>/telegram/webhook`.
5. Teste o healthcheck: `GET /health` retorna `{ "status": "ok" }`.

O pipeline continua enviando os relatórios para os chats definidos em cada config JSON.

## 🚢 Docker (Local)

### Opção 1: Docker Compose (Recomendado)
```bash
# Build e rodar em um comando
docker-compose up --build

# Rodar em background (detached)
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

### Opção 2: Docker manual
1. Build da imagem: `docker build -t kommo-analytics .`
2. Rodar com variáveis do `.env`: `docker run -p 8000:8000 --env-file .env kommo-analytics`
3. Se quiser editar configs sem rebuild, monte a pasta local: `docker run -p 8000:8000 --env-file .env -v $(pwd)/config:/app/config kommo-analytics`

### Testes e webhook:
4. Teste local: `curl http://localhost:8000/health` (deve retornar `{"status":"ok"}`)
5. Use ngrok para expor temporariamente: `ngrok http 8000`
6. Registre o webhook no Telegram: `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://sua-url/telegram/webhook`

Arquivos úteis: [docker-compose.yml](docker-compose.yml), [Dockerfile](Dockerfile) e [.dockerignore](.dockerignore).

## ☁️ Deploy no Render (Gratuito)
O Render fornece URL HTTPS pública automaticamente, ideal para webhook do Telegram.

### Passo a passo:
1. **Crie conta no Render:** https://render.com
2. **Novo Web Service:**
   - Dashboard → "New +" → "Web Service"
   - Conecte seu repositório GitHub
   - Nome: `kommo-analytics` 
3. **Configurações:**
   - **Environment:** Docker
   - **Region:** escolha a mais próxima
   - **Branch:** main
   - **Dockerfile Path:** `Dockerfile` 
   - **Plan:** Free
4. **Variáveis de ambiente:**
   - Clique em "Advanced" ou vá em "Environment" depois do deploy
   - Adicione cada variável do `.env`:
     - `TELEGRAM_BOT_TOKEN`
     - `DANIEL_DOURADO_TOKEN`
     - `ELINEY_FARIA_TOKEN`
     - `MARCELA_DI_LOLLO_TOKEN`
     - `MATEUS_BRETAS_TOKEN`
5. **Deploy:**
   - Clique em "Create Web Service"
   - Aguarde o build (leva ~2-5min na primeira vez)
   - Quando finalizar, copie a URL: `https://kommo-analytics-xxxx.onrender.com`
6. **Registre o webhook:**
   - Abra no browser (substitua `<TOKEN>` e `<URL>`):
   ```
   https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://kommo-analytics-xxxx.onrender.com/telegram/webhook
   ```
   - Deve retornar: `{"ok":true, "result":true, "description":"Webhook was set"}`
7. **Teste:**
   - Health: `https://kommo-analytics-xxxx.onrender.com/health`
   - Envie `/semana` ou `/help` no bot do Telegram

### ⚠️ Limitações do plano gratuito:
- Serviço "dorme" após 15min de inatividade
- Primeira requisição após dormir demora ~30s para acordar
- Para o webhook do Telegram, funciona bem (o bot aguarda a resposta)

### 🔄 Atualizações automáticas:
- Todo push na branch `main` triggera novo deploy automaticamente
- Render faz rebuild e redeploy em ~2-3min
