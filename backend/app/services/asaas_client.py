"""Wrapper de chamadas à API da Asaas (Pix Automático).

Aponta para sandbox ou produção conforme a variável de ambiente ASAAS_ENV.
"""
import os

ASAAS_ENV = os.getenv("ASAAS_ENV", "sandbox")
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")

ASAAS_BASE_URLS = {
    "sandbox": "https://api-sandbox.asaas.com/v3",
    "production": "https://api.asaas.com/v3",
}


class AsaasClient:
    """Cliente para integração com a API da Asaas. Métodos a implementar."""

    def __init__(self) -> None:
        self.base_url = ASAAS_BASE_URLS[ASAAS_ENV]
        self.api_key = ASAAS_API_KEY

    def criar_autorizacao_pix_automatico(self, participante, pagamentos):
        """Cria a autorização de recorrência do Pix Automático na Asaas.

        TODO: implementar a chamada real ao endpoint de Pix Automático (sandbox).
        Por enquanto retorna None para não bloquear o cadastro local do participante.
        """
        return None

    def obter_qr_code_pix(self, *args, **kwargs):
        raise NotImplementedError
