---
name: testar-webhook
description: Simula um payload de webhook da Asaas (confirmação de pagamento Pix Automático) contra o backend local, para validar sem precisar esperar um pagamento real. Use quando terminar ou alterar a implementação da rota /webhooks/asaas.
argument-hint: [pago|falhou] [participante_id]
allowed-tools: Bash(curl:*), Read, Grep
---

Você vai simular um evento de webhook da Asaas contra o backend rodando localmente, para validar a rota `/webhooks/asaas` sem depender de um pagamento real.

## Contexto do projeto

Consulte `PRD.md` e `CLAUDE.md` na raiz do projeto para relembrar o modelo de dados (`Participante`, `Pagamento`) e os campos `asaas_payment_id` / `asaas_authorization_id`.

## Passos

1. Confirme que o backend está rodando localmente (tente `curl http://localhost:8000/docs` — se falhar, avise o usuário para rodar `uvicorn app.main:app --reload` antes de continuar, e pare aqui).

2. Determine o status a simular a partir do argumento `$1` (padrão: `pago`, ou seja, evento `PAYMENT_CONFIRMED`). Se `$1` for `falhou`, simule um evento `PAYMENT_OVERDUE` ou `PAYMENT_FAILED` (use o nome de evento real conforme a implementação atual do `webhooks.py` — leia o arquivo antes de montar o payload).

3. Se `$2` (participante_id) não for informado, consulte o banco SQLite local (`sqlite3 backend/confraternizacao.db "SELECT id, asaas_payment_id FROM pagamento LIMIT 1;"`) para pegar um `asaas_payment_id` real de teste. Se não houver nenhum registro, avise o usuário que é necessário cadastrar um participante de teste primeiro.

4. Monte o JSON do payload simulando o formato de evento da Asaas (evento, payment.id, payment.status, payment.value, payment.externalReference). Antes de montar, leia `backend/app/routers/webhooks.py` para confirmar exatamente quais campos o código espera — não invente um formato sem checar o parser real.

5. Envie a requisição com `curl`, incluindo o header `asaas-access-token` com o valor de `ASAAS_WEBHOOK_TOKEN` do `.env` local (leia o `.env`, nunca exiba o valor no output para o usuário — apenas use internamente):

```bash
curl -X POST http://localhost:8000/webhooks/asaas \
  -H "Content-Type: application/json" \
  -H "asaas-access-token: $ASAAS_WEBHOOK_TOKEN" \
  -d '{...payload montado no passo 4...}'
```

6. Depois do `curl`, consulte o banco novamente para confirmar que o `status` do `Pagamento` correspondente foi atualizado corretamente, e reporte ao usuário: sucesso ou o que falhou.

7. Rode também um teste com o header `asaas-access-token` **errado** ou ausente, e confirme que o backend rejeita (deve retornar 401/403, não deve alterar nada no banco). Isso valida a regra de segurança do webhook descrita no CLAUDE.md — não pule esta etapa.

8. Reporte um resumo curto: qual cenário passou, qual falhou, e se a validação de token está funcionando.
