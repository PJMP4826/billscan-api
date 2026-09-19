from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse

from api.http.controllers.receive_facturagpt_webhook_controller import (
    ReceiveFacturaGPTWebhookController,
)

router = APIRouter()


@router.post("/webhooks/facturagpt")
async def webhooks_facturagpt(
    request: Request, background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    Endpoint de recepción de webhooks de FacturaGPT.

    - Verifica la firma HMAC sobre el body crudo.
    - Almacena el payload crudo de forma idempotente (idempotency_key).
    - Encola el procesamiento en background y responde 200 de inmediato
      (FacturaGPT hace entrega at-least-once: los reintentos de red se
      absorben con la idempotency_key).
    """
    controller = ReceiveFacturaGPTWebhookController()
    return await controller.handle(request=request, background_tasks=background_tasks)
