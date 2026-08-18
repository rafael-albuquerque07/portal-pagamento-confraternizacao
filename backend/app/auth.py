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

security = HTTPBasic()


def verificar_admin(credenciais: HTTPBasicCredentials = Depends(security)) -> None:
    hash_esperado = os.getenv("ADMIN_PASSWORD_HASH", "")
    hash_informado = hashlib.sha256(credenciais.password.encode()).hexdigest()

    if not hash_esperado or not hmac.compare_digest(hash_informado, hash_esperado):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
