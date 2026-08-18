"""Wrapper de chamadas à API da Asaas (Pix Automático).

Aponta para sandbox ou produção conforme a variável de ambiente ASAAS_ENV.

Fluxo de Pix Automático (docs.asaas.com/docs/pix-automatico-implementacao):
1. Criar a autorização (+ cobrança da 1ª parcela, com QR Code imediato).
2. Aguardar o webhook de ativação (PIX_AUTOMATIC_RECURRING_AUTHORIZATION_ACTIVATED)
   — não implementado aqui, fica para o handler de /webhooks/asaas.
3. Com a autorização ACTIVE, criar cada cobrança seguinte informando
   `pixAutomaticAuthorizationId`, dentro da janela de 2 a 10 dias úteis
   antes do vencimento — também não implementado aqui (processo futuro).
"""
import os

import httpx

ASAAS_ENV = os.getenv("ASAAS_ENV", "sandbox")
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")

ASAAS_BASE_URLS = {
    "sandbox": "https://api-sandbox.asaas.com/v3",
    "production": "https://api.asaas.com/v3",
}

TIMEOUT_SEGUNDOS = 15.0

# TODO: confirmar o path exato deste endpoint no Postman/sandbox da Asaas
# (docs.asaas.com/reference/criar-uma-autorizacao-pix-automatico) — a doc
# de referência recebida não detalhou o path, só o comportamento esperado.
CRIAR_AUTORIZACAO_PIX_AUTOMATICO_PATH = "/pixAutomatic"


class AsaasError(Exception):
    """Erro ao chamar a API da Asaas (resposta não-2xx ou falha de rede)."""


class AsaasClient:
    """Cliente para integração com a API da Asaas."""

    def __init__(self) -> None:
        self.base_url = ASAAS_BASE_URLS[ASAAS_ENV]
        self.api_key = ASAAS_API_KEY

    def _headers(self) -> dict:
        return {"access_token": self.api_key or "", "Content-Type": "application/json"}

    def _post(self, path: str, json: dict) -> dict:
        try:
            resposta = httpx.post(
                f"{self.base_url}{path}", json=json, headers=self._headers(), timeout=TIMEOUT_SEGUNDOS
            )
            resposta.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise AsaasError(f"Asaas retornou {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise AsaasError(f"Falha de rede ao chamar a Asaas: {exc}") from exc
        return resposta.json()

    def _get(self, path: str, params: dict) -> dict:
        try:
            resposta = httpx.get(
                f"{self.base_url}{path}", params=params, headers=self._headers(), timeout=TIMEOUT_SEGUNDOS
            )
            resposta.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise AsaasError(f"Asaas retornou {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise AsaasError(f"Falha de rede ao chamar a Asaas: {exc}") from exc
        return resposta.json()

    def buscar_ou_criar_cliente(self, nome: str, cpf: str, telefone: str | None) -> str:
        """Retorna o id do Customer na Asaas, reaproveitando um já existente pelo CPF."""
        existentes = self._get("/customers", params={"cpfCnpj": cpf})
        if existentes.get("data"):
            return existentes["data"][0]["id"]

        payload = {"name": nome, "cpfCnpj": cpf}
        if telefone:
            payload["mobilePhone"] = telefone

        criado = self._post("/customers", json=payload)
        return criado["id"]

    def criar_autorizacao_pix_automatico(
        self, customer_id: str, valor: float, vencimento: str, descricao: str
    ) -> dict:
        """Cria a autorização de recorrência do Pix Automático + cobrança da 1ª parcela.

        Retorna {id, payload, conciliation_identifier} — `id` precisa ser
        salvo (é usado depois para vincular as cobranças seguintes) e
        `payload` é o código copia-e-cola Pix do primeiro pagamento.

        TODO: os nomes de campo do payload (customer/value/dueDate/description)
        seguem a convenção usada em outros endpoints da Asaas (payments/
        subscriptions), mas não foram confirmados especificamente para este
        endpoint na doc de referência recebida — validar contra o Postman/
        sandbox real antes de confiar neste fluxo em produção.
        """
        payload = {
            "customer": customer_id,
            "value": valor,
            "dueDate": vencimento,
            "description": descricao,
        }
        resposta = self._post(CRIAR_AUTORIZACAO_PIX_AUTOMATICO_PATH, json=payload)
        return {
            "id": resposta.get("id"),
            "payload": resposta.get("payload"),
            "conciliation_identifier": resposta.get("conciliationIdentifier"),
        }

    def obter_qr_code_pix(self, *args, **kwargs):
        raise NotImplementedError
