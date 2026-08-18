"""Autenticação HTTP Basic do painel administrativo.

A senha do admin é armazenada em ADMIN_PASSWORD_HASH como o hex digest
SHA-256 da senha (nunca a senha em texto puro). Para gerar o hash:
    python -c "import hashlib; print(hashlib.sha256(b'sua-senha').hexdigest())"
"""
import hashlib
import hmac
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# auto_error=False: com o padrão (True), a ausência do header Authorization
# já dispara um 401 com WWW-Authenticate: Basic antes de chegar aqui. Esse
# header faz o navegador abrir o próprio diálogo nativo de login por cima do
# painel — quebra o formulário de senha da SPA, que trata login/erro sozinha.
security = HTTPBasic(auto_error=False)


def verificar_admin(credenciais: HTTPBasicCredentials | None = Depends(security)) -> None:
    hash_esperado = os.getenv("ADMIN_PASSWORD_HASH", "")
    hash_informado = hashlib.sha256(credenciais.password.encode()).hexdigest() if credenciais else ""

    if not hash_esperado or not credenciais or not hmac.compare_digest(hash_informado, hash_esperado):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
