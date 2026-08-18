# CLAUDE.md

Este arquivo orienta o Claude Code ao trabalhar neste repositório. O contexto completo de produto está em `PRD.md` — leia-o antes de iniciar qualquer implementação.

## Quem sou eu (contexto do autor)

Desenvolvedor profissional de Salesforce (Apex, LWC, OmniStudio/Vlocity) e desenvolvedor Python por conta própria. **Não é** a primeira vez programando — não preciso de explicações de conceitos básicos de programação, apenas de contexto específico de Pix/Asaas/PWA, que são áreas novas para mim. Prefiro nomes de variáveis, funções e comentários de código **em português**, seguindo o padrão que já uso nas minhas conversas.

## Stack definida (não sugerir alternativas sem justificativa forte)

- **Frontend**: TypeScript + Vite (vanilla, sem framework). PWA com `manifest.json` + service worker.
- **Backend**: FastAPI (Python 3.11+).
- **Banco de dados**: SQLite (via SQLAlchemy ou `sqlite3` puro — decidir pela simplicidade, este projeto é pequeno).
- **Gateway de pagamento**: Asaas — usar **Pix Automático** (autorização de recorrência), não cobrança avulsa mês a mês.
- **Notificação**: Meta WhatsApp Cloud API diretamente (**não usar Twilio** nem outro BSP intermediário — decisão já tomada por causa do markup por mensagem).

## Estrutura de pastas esperada

```
/backend
  /app
    main.py                # instancia FastAPI, inclui routers
    models.py               # modelos SQLAlchemy (Participante, Pagamento)
    database.py              # engine + sessão SQLite
    schemas.py                # Pydantic models (request/response)
    /routers
      participante.py         # GET /api/participante/{slug}/...
      admin.py                  # GET/POST /api/admin/...
      webhooks.py                # POST /webhooks/asaas
    /services
      asaas_client.py            # wrapper de chamadas à API Asaas
      whatsapp_client.py          # wrapper de chamadas à Meta Cloud API
  requirements.txt
  .env.example                    # variáveis de ambiente sem valores reais

/frontend
  /src
    main.ts
    /pages
      participante.ts
      admin.ts
    /components
      qrcode-pix.ts               # exibição de QR + botão copiar
    manifest.json
    sw.ts                          # service worker
  index.html
  vite.config.ts
  package.json

PRD.md
CLAUDE.md
README.md
```

## Regras de implementação

- **Nunca commitar segredos**: API key da Asaas, token de acesso do webhook, token do WhatsApp Cloud API — tudo via variáveis de ambiente (`.env`, fora do git). Sempre manter um `.env.example` atualizado com as chaves necessárias, sem valores reais.
- **Validação de webhook é inegociável**: qualquer implementação de `/webhooks/asaas` deve validar o header `asaas-access-token` antes de processar o payload. Não implementar a rota sem essa validação, mesmo em rascunho.
- **Sandbox primeiro**: toda integração nova com a Asaas deve ser testável apontando para o ambiente sandbox via variável de ambiente (`ASAAS_ENV=sandbox|production`), nunca hardcoded para produção.
- **Idempotência no webhook**: usar `asaas_payment_id` como chave para evitar processar o mesmo evento duas vezes (ex: checar se o status já é "pago" antes de disparar notificação de novo).
- **Sem framework no frontend**: resistir à tentação de sugerir React/Vue/Svelte — a decisão de vanilla TS + Vite já foi tomada deliberadamente para este escopo pequeno.
- **Sem localStorage/sessionStorage sensível**: não guardar tokens ou dados de pagamento no `localStorage` do navegador.
- **Commits e branches**: seguir Git Flow (o autor já usa esse padrão profissionalmente) — branches `feature/`, `fix/`, commits com mensagens claras em português.

## O que já foi decidido e não deve ser reaberto sem pedido explícito

- Asaas como gateway (não Efí, Mercado Pago ou outro) para esta fase.
- Pix Automático (não cobrança avulsa mensal).
- CPF na conta Asaas por enquanto (migração para CNPJ/MEI é decisão futura, fora deste MVP).
- Meta Cloud API para WhatsApp (não Twilio).
- SQLite (não Postgres) nesta fase.
- Vanilla TypeScript (não framework) no frontend.

## Comandos úteis (preencher conforme o projeto evoluir)

```bash
# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install
npm run dev
npm run build
```

## Variáveis de ambiente esperadas (`.env.example`)

```
ASAAS_API_KEY=
ASAAS_ENV=sandbox
ASAAS_WEBHOOK_TOKEN=
WHATSAPP_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ADMIN_NUMBER=
ADMIN_PASSWORD_HASH=
DATABASE_URL=sqlite:///./confraternizacao.db
```
