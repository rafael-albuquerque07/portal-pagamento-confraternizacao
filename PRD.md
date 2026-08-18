# PRD — Portal de Pagamentos da Confraternização (Barbearia)

## 1. Contexto e finalidade

Sou desenvolvedor (Salesforce/Vlocity/Apex/LWC profissionalmente, Python por conta própria) e estou organizando a confraternização de final de ano de uma barbearia, num clube de piscinas. Estamos em agosto/2026, e o evento é no final do ano.

Cada integrante do grupo deve pagar um total de **R$80,00**, parcelado em **4 meses** (setembro, outubro, novembro e dezembro de 2026), ou seja, **R$20,00/mês por pessoa**.

Como desenvolvedor, quero resolver isso com uma solução própria em vez de planilha manual ou grupo de WhatsApp perguntando "quem já pagou": um **PWA** (Progressive Web App) que funcione como portal para os participantes, com cobrança via **Pix** e conciliação **automática** de pagamentos.

### Objetivo secundário (importante para as decisões técnicas)
Este projeto **não é descartável**. A intenção é evoluir esse sistema depois para um produto que possa ser oferecido a outras barbearias/pequenos grupos (modelo de assinatura/gestão de contribuições recorrentes), com potencial de monetização. Por isso, as decisões de arquitetura devem privilegiar solução limpa e extensível, mesmo que o escopo atual seja pequeno (uma única "turma" de participantes).

## 2. Objetivos do produto (fase atual — MVP)

1. Permitir que cada participante acesse um link único, instale o PWA na tela inicial do celular, e visualize o status das suas 4 parcelas.
2. Gerar cobrança Pix por parcela, com **autorização única de recorrência (Pix Automático)** — o participante autoriza uma vez no primeiro pagamento, e as parcelas seguintes são debitadas automaticamente, sem necessidade de nova ação.
3. Confirmar pagamentos **automaticamente** via webhook do provedor de pagamento (Asaas), sem conciliação manual.
4. Notificar o organizador (eu, como admin) por **WhatsApp** a cada pagamento confirmado.
5. Fornecer um painel administrativo mostrando todos os participantes e o status de cada parcela.

## 3. Fora de escopo (nesta fase)

- Split de pagamento entre múltiplos recebedores (só relevante quando/se o produto for vendido a terceiros).
- Abertura de CNPJ/MEI e criação de subcontas Asaas (necessário só na fase de monetização/multi-tenant).
- Autenticação robusta multi-usuário/multi-evento (o escopo atual é uma única confraternização, uma única "turma" de participantes).
- App nativo — é PWA, instalável via navegador.

## 4. Personas

- **Participante**: pessoa do grupo da barbearia que precisa pagar as 4 parcelas. Acessa via link, instala o PWA, visualiza suas parcelas, paga via Pix (QR Code ou copia-e-cola).
- **Admin (eu)**: organizador do evento. Acessa um painel separado (autenticado) que lista todos os participantes e status de pagamento. Recebe notificação via WhatsApp a cada pagamento confirmado.

## 5. Arquitetura definida

```
Frontend (TypeScript + Vite + manifest.json + service worker)
        │  HTTP/JSON (fetch)
        ▼
Backend (FastAPI, Python)
        │  cria cobrança/autorização, recebe webhook
        ▼
Asaas (Pix Automático) ──────────► WhatsApp (Meta Cloud API)
        │
        ▼
Banco de dados (SQLite)
```

- **Frontend**: TypeScript vanilla + Vite (sem framework — poucas telas não justificam). PWA instalável via manifest.json + service worker mínimo (cache básico de shell).
- **Backend**: FastAPI (Python). Responsável por toda regra de negócio: criação de cobrança na Asaas, recebimento e validação de webhook, atualização de status, disparo de notificação WhatsApp, exposição de API REST para o frontend.
- **Banco de dados**: SQLite. Espelho local ligando `Participante` ↔ `Pagamento` ↔ referências da Asaas (`asaas_payment_id`, `asaas_authorization_id`). Não há necessidade de Postgres nesta fase (baixo volume, único servidor).
- **Gateway de pagamento**: Asaas, usando **Pix Automático** (não cobrança Pix avulsa por mês). Fluxo: primeira cobrança já carrega os dados de autorização de recorrência → participante escaneia/paga uma vez e autoriza → parcelas seguintes são geradas e debitadas automaticamente (usando `pixAutomaticAuthorizationId`, opcionalmente com `paymentCreationMode: SUBSCRIPTION`) → webhook avisa a cada evento de débito.
- **Notificação**: WhatsApp via **Meta Cloud API diretamente** (não usar Twilio — API oficial da Meta é gratuita na camada base, sem markup de intermediário). Notificação vai para o número do admin a cada pagamento confirmado.

## 6. Modelo de dados (SQLite)

```sql
CREATE TABLE participante (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    telefone TEXT,
    slug TEXT UNIQUE NOT NULL,          -- usado na URL individual do PWA
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pagamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participante_id INTEGER NOT NULL REFERENCES participante(id),
    mes_referencia TEXT NOT NULL,        -- formato "2026-09"
    valor_esperado REAL NOT NULL DEFAULT 20.00,
    status TEXT NOT NULL DEFAULT 'pendente',  -- pendente | pago | falhou
    asaas_payment_id TEXT,               -- id da cobrança na Asaas
    asaas_authorization_id TEXT,         -- id da autorização de recorrência
    data_confirmacao TIMESTAMP,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(participante_id, mes_referencia)
);
```

## 7. Endpoints da API (Backend)

| Método | Rota | Finalidade | Auth |
|---|---|---|---|
| GET | `/api/participante/{slug}/pagamentos` | Lista as 4 parcelas do participante e status de cada uma | Não (slug funciona como token de acesso) |
| GET | `/api/participante/{slug}/pix/{mes}` | Retorna QR Code (base64) + payload copia-e-cola da cobrança daquele mês | Não |
| POST | `/webhooks/asaas` | Recebe eventos de pagamento/autorização da Asaas, valida token, atualiza status, dispara WhatsApp | Validação via header `asaas-access-token` |
| GET | `/api/admin/dashboard` | Lista todos os participantes com status de todas as parcelas | Sim (admin) |
| POST | `/api/admin/participantes` | Cadastra novo participante e cria a autorização inicial de Pix Automático na Asaas | Sim (admin) |

## 8. Requisitos não-funcionais

- **Segurança do webhook**: toda requisição recebida em `/webhooks/asaas` deve validar o header `asaas-access-token` contra o valor configurado — sem isso, qualquer requisição externa poderia forjar confirmação de pagamento.
- **HTTPS obrigatório**: tanto para o PWA (Service Worker e `navigator.clipboard` exigem contexto seguro) quanto para o backend (webhook e API).
- **Idempotência**: reprocessar o mesmo evento de webhook não deve gerar duplicidade de notificação nem inconsistência de status.
- **Ambiente de teste**: todo o fluxo (criação de cobrança, QR, webhook) deve ser validado em sandbox da Asaas antes de qualquer cobrança real.

## 9. Fluxo do participante (User Journey)

1. Recebe o link (WhatsApp/pessoalmente) → acessa o PWA.
2. Navegador oferece "adicionar à tela inicial" (Android automático; iOS via Compartilhar → Adicionar à Tela de Início, com instrução visual na tela).
3. Vê lista das 4 parcelas com status (pago/pendente).
4. Na primeira parcela pendente, vê QR Code + botão "Copiar código Pix" (copia o payload copia-e-cola via `navigator.clipboard.writeText`).
5. Paga e autoriza a recorrência no app do banco.
6. Parcelas seguintes são debitadas automaticamente nos meses seguintes, sem nova ação do participante.
7. Status atualiza automaticamente na tela a cada pagamento confirmado.

## 10. Fluxo do admin

1. Acessa painel autenticado.
2. Vê tabela: participante × 4 meses × status.
3. Recebe notificação via WhatsApp a cada novo pagamento confirmado (evento de webhook).

## 11. Considerações para evolução futura (não implementar agora, mas não travar o design)

- Migração de CPF para CNPJ (MEI) na conta Asaas quando o produto for oferecido a terceiros, habilitando subcontas e split de pagamento.
- Multi-tenant: múltiplos "eventos"/"turmas" de participantes isolados.
- Troca de SQLite por Postgres quando o volume justificar.
- Migração de notificação WhatsApp de "só admin" para "confirmação também ao participante", via templates aprovados pela Meta.
