# Portal de Pagamentos — Confraternização Barbearia 🏊‍♂️💈

PWA para gestão das contribuições da confraternização de final de ano, com cobrança recorrente via Pix Automático e conciliação automática de pagamentos.

> Contexto completo de produto em [`PRD.md`](./PRD.md). Diretrizes técnicas para desenvolvimento (inclusive via Claude Code) em [`CLAUDE.md`](./CLAUDE.md).

## O que este projeto faz

- Cada participante acessa um link único, instala o app na tela inicial do celular (PWA) e acompanha o status das suas 4 parcelas de R$20 (set/out/nov/dez de 2026).
- Pagamento via Pix, com autorização única de recorrência (Pix Automático) — depois da primeira parcela, as seguintes são debitadas automaticamente.
- Confirmação de pagamento é automática via webhook (sem conciliação manual).
- Notificação por WhatsApp ao organizador a cada pagamento confirmado.
- Painel administrativo com visão geral de todos os participantes e status de pagamento.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | TypeScript + Vite (PWA: manifest + service worker) |
| Backend | FastAPI (Python) |
| Banco de dados | SQLite |
| Gateway de pagamento | Asaas (Pix Automático) |
| Notificação | WhatsApp via Meta Cloud API |

## Estrutura de pastas

```
/backend    → API FastAPI, integração Asaas, webhook, notificação WhatsApp
/frontend   → PWA em TypeScript + Vite
PRD.md      → especificação de produto
CLAUDE.md   → diretrizes para desenvolvimento assistido por IA
```

## Como rodar localmente

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- Conta Asaas (sandbox) com API key
- App configurado no Meta for Developers (WhatsApp Cloud API)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # preencher com as chaves reais (nunca commitar)
uvicorn app.main:app --reload
```

Backend sobe em `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend sobe em `http://localhost:5173` (padrão do Vite).

## Variáveis de ambiente (`backend/.env`)

Ver `.env.example` para a lista completa. Nunca commitar o `.env` real — ele já está no `.gitignore`.

## Status do projeto

🚧 Em desenvolvimento — MVP para a confraternização de final de ano de 2026.

## Roadmap futuro (fora do escopo do MVP)

- Migração de conta CPF para CNPJ (MEI) na Asaas, habilitando subcontas e split de pagamento.
- Suporte a múltiplos eventos/turmas (multi-tenant).
- Notificação de confirmação também para o participante (não só o admin).
