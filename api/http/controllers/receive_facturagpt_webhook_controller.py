"""
ReceiveFacturaGPTWebhookController — puerta de entrada HTTP de webhooks.

Responsabilidades SOLO de transporte:
1. Extraer del `Request` lo que el resto de la app necesita: body crudo
   (bytes exactos para verificar la firma) y cabeceras normalizadas.
2. Construir la entrada tipada `FacturaGPTWebhookDelivery`.
3. Delegar TODA la orquestación (firma, parseo, store-before-process,
   encolado) al caso de uso `ReceiveFacturaGPTWebhookUseCase`.

Las excepciones de dominio (`BillingWebhookSignatureError` -> 401,
`BillingWebhookParseError` -> 400) y cualquier error inesperado -> 500 se
traducen en el handler global de excepciones.

El caso de uso responde 200 de inmediato para los eventos aceptados:
FacturaGPT hace entrega at-least-once y los reintentos de red se absorben
con la idempotency_key. Un error inesperado responde 500 -> el proveedor
reintenta (semántica at-least-once).
"""

from fastapi import BackgroundTasks, Request, status
from fastapi.responses import JSONResponse

from api.http.requests.webhook_event_request import WebHookEventRequest
from src.application.commands.facturagpt_webhook_delivery import (
    FacturaGPTWebhookDelivery,
)
from src.bootstraps.use_cases_bootstrap import get_receive_facturagpt_webhook_use_case


class ReceiveFacturaGPTWebhookController:
    def __init__(self) -> None:
        pass

    async def handle(
        self, request: Request, body: WebHookEventRequest, background_tasks: BackgroundTasks
    ) -> JSONResponse:
        # El body se lee como bytes crudos: la firma HMAC se verifica sobre
        # el body exacto que envió FacturaGPT, no sobre un JSON re-serializado.
        raw_body = await request.body()
        headers = {k.lower(): v for k, v in request.headers.items()}

        delivery = FacturaGPTWebhookDelivery(raw_body=raw_body, headers=headers)

        use_case = get_receive_facturagpt_webhook_use_case(
            background_tasks=background_tasks
        )
        await use_case.execute(delivery=delivery, body=body.model_dump())

        # Aceptado: almacenado (y encolado si aplicaba). ACK inmediato.
        # FacturaGPT solo exige el 200; el body es informativo para debugging.
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "received"},
        )
