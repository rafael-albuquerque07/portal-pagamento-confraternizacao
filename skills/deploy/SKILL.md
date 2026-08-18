---
name: deploy
description: Roda o checklist de commit seguro do projeto (checa segredos vazados, roda testes se existirem, commita seguindo Git Flow e faz push). Use quando terminar uma feature e quiser subir para o repositório remoto.
argument-hint: [mensagem-curta-do-commit]
allowed-tools: Bash(git:*), Bash(pytest:*), Bash(npm:*), Read, Grep
---

Você vai executar o checklist de commit seguro deste projeto antes de subir código para o repositório remoto. Siga a ordem — não pule etapas mesmo que pareçam óbvias.

## 1. Checar segredos antes de qualquer coisa

Rode `git diff --staged` e `git status`. Procure por qualquer coisa que pareça chave de API, token, senha ou valor de `.env` real sendo adicionado ao commit (não apenas o arquivo `.env` — também valores colados por engano em código ou em `CLAUDE.md`/`README.md`). Se encontrar, **pare imediatamente** e avise o usuário — não prossiga com o commit.

## 2. Rodar testes, se existirem

- Backend: se houver testes em `backend/tests/`, rode `pytest` dentro do venv ativado. Se algum teste falhar, reporte e pergunte ao usuário se quer corrigir antes de continuar ou commitar mesmo assim.
- Frontend: se houver script de teste no `package.json`, rode `npm test`.
- Se não houver testes configurados ainda neste estágio do projeto, apenas informe isso e siga em frente — não é bloqueante nesta fase do MVP.

## 3. Montar a mensagem de commit seguindo Git Flow

O autor deste projeto já usa Git Flow profissionalmente. Siga o padrão:
- Prefixo semântico: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:` conforme a natureza da mudança.
- Mensagem curta e objetiva em português, baseada no argumento `$ARGUMENTS` se fornecido, ou inferida a partir do `git diff` se não fornecido.
- Exemplo: `feat: implementa validação de token no webhook da Asaas`

## 4. Commit e push

```bash
git add .
git commit -m "<mensagem montada no passo 3>"
git push origin <branch-atual>
```

Antes do push, confirme qual é a branch atual (`git branch --show-current`) e se ela segue o padrão esperado (`feature/`, `fix/` etc, conforme `CLAUDE.md`). Se estiver direto na `main`/`master`, avise o usuário e pergunte se é intencional antes de dar push.

## 5. Resumo final

Reporte ao usuário: o que foi commitado, se algum teste rodou (e o resultado), e se o push foi bem-sucedido.
