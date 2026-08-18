---
name: testar-webhook
description: Simula um payload de webhook da Asaas (confirmação de pagamento ou evento de autorização de Pix Automático) contra o backend local, para validar sem precisar esperar um pagamento real. Use quando terminar ou alterar a implementação da rota /webhooks/asaas.
argument-hint: [pago|falhou|autorizacao_ativa|autorizacao_recusada|autorizacao_cancelada|autorizacao_expirada] [participante_id]
allowed-tools: Bash(curl:*), Read, Grep
---

Você vai simular um evento de webhook da Asaas contra o backend rodando localmente, para validar a rota `/webhooks/asaas` sem depender de um pagamento real.

## Contexto do projeto

Consulte `PRD.md` e `CLAUDE.md` na raiz do projeto para relembrar o modelo de dados (`Participante`, `Pagamento`) e os campos `asaas_payment_id` / `asaas_authorization_id` / `autorizacao_status`.

## Passos

1. Confirme que o backend está rodando localmente (tente `curl http://localhost:8000/docs` — se falhar, avise o usuário para rodar `uvicorn app.main:app --reload` antes de continuar, e pare aqui).

2. Antes de montar qualquer payload, leia `backend/app/routers/webhooks.py` para confirmar os nomes de evento e campos que o código espera atualmente — não invente formato sem checar o parser real. Determine o cenário a partir do argumento `$1` (padrão: `pago`):
   - `pago` → evento `PAYMENT_CONFIRMED` (cenário de pagamento).
   - `falhou` → evento `PAYMENT_OVERDUE` ou `PAYMENT_FAILED` — use o nome real conforme `EVENTOS_PAGAMENTO_CONFIRMADO`/lógica atual do arquivo (cenário de pagamento).
   - `autorizacao_ativa` → evento `PIX_AUTOMATIC_RECURRING_AUTHORIZATION_ACTIVATED` (cenário de autorização).
   - `autorizacao_recusada` → evento `PIX_AUTOMATIC_RECURRING_AUTHORIZATION_REFUSED` (cenário de autorização).
   - `autorizacao_cancelada` → evento `PIX_AUTOMATIC_RECURRING_AUTHORIZATION_CANCELLED` (cenário de autorização).
   - `autorizacao_expirada` → evento `PIX_AUTOMATIC_RECURRING_AUTHORIZATION_EXPIRED` (cenário de autorização).
   - Confira o dict `EVENTOS_AUTORIZACAO_PIX` no arquivo para garantir que o nome do evento e o status esperado (`CREATED`/`ACTIVE`/`REFUSED`/`CANCELLED`/`EXPIRED`) ainda batem antes de montar o payload.

3. Se `$2` (participante_id) não for informado, consulte o banco SQLite local para pegar um registro de teste:
   - Cenário de **pagamento**: `sqlite3 backend/confraternizacao.db "SELECT id, asaas_payment_id FROM pagamento LIMIT 1;"`.
   - Cenário de **autorização**: `sqlite3 backend/confraternizacao.db "SELECT id, asaas_authorization_id, autorizacao_status FROM pagamento LIMIT 1;"` — como a mesma autorização é compartilhada pelas 4 parcelas do participante, note quantas linhas têm o mesmo `asaas_authorization_id` (deve ser todas as parcelas dele) para depois conferir que **todas** foram atualizadas.
   - Se não houver nenhum registro (ou `asaas_authorization_id` nulo), avise o usuário que é necessário cadastrar um participante de teste primeiro (via `POST /api/admin/participantes`).

4. Monte o JSON do payload:
   - Cenário de **pagamento**: formato `{event, payment: {id, status, value, externalReference, conciliationIdentifier}}`.
   - Cenário de **autorização**: formato `{event, pixAutomaticAuthorization: {id}}`, usando o `asaas_authorization_id` obtido no passo 3 como `pixAutomaticAuthorization.id`. Isso corresponde ao que `_extrair_authorization_id` lê hoje em `webhooks.py` — se o código tiver mudado essa chave, ajuste o payload de acordo (e avise o usuário que o TODO sobre o nome do campo ainda não foi validado contra a Asaas real).

5. Envie a requisição com `curl`, incluindo o header `asaas-access-token` com o valor de `ASAAS_WEBHOOK_TOKEN` do `.env` local (leia o `.env`, nunca exiba o valor no output para o usuário — apenas use internamente):

```bash
curl -X POST http://localhost:8000/webhooks/asaas \
  -H "Content-Type: application/json" \
  -H "asaas-access-token: $ASAAS_WEBHOOK_TOKEN" \
  -d '{...payload montado no passo 4...}'
```

6. Depois do `curl`, consulte o banco novamente para confirmar a atualização:
   - Cenário de **pagamento**: `status` do `Pagamento` correspondente.
   - Cenário de **autorização**: `autorizacao_status` de **todas** as parcelas que compartilham aquele `asaas_authorization_id` (não só a primeira) — é isso que garante que o update em lote no handler funcionou.
   - Rode o mesmo `curl` uma segunda vez e confirme que a resposta é `{"status": "ja_processado"}` e que nada mudou no banco — isso valida a idempotência do handler.
   Reporte ao usuário: sucesso ou o que falhou.

7. Rode também um teste com o header `asaas-access-token` **errado** ou ausente, e confirme que o backend rejeita (deve retornar 401/403, não deve alterar nada no banco). Isso valida a regra de segurança do webhook descrita no CLAUDE.md — não pule esta etapa.

8. Reporte um resumo curto: qual(is) cenário(s) passou(aram), qual falhou, se a idempotência funcionou, e se a validação de token está funcionando.
