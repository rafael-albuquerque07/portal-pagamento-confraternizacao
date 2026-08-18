"""Wrapper de chamadas à Meta WhatsApp Cloud API (sem intermediário/BSP)."""
import os

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ADMIN_NUMBER = os.getenv("WHATSAPP_ADMIN_NUMBER")

WHATSAPP_BASE_URL = "https://graph.facebook.com/v20.0"


class WhatsAppClient:
    """Cliente para envio de notificações via Meta Cloud API. Métodos a implementar."""

    def __init__(self) -> None:
        self.token = WHATSAPP_TOKEN
        self.phone_number_id = WHATSAPP_PHONE_NUMBER_ID

    def notificar_admin_pagamento_confirmado(self, *args, **kwargs):
        raise NotImplementedError
