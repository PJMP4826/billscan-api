"""
ReceiveFacturaGPTWebhookController — puerta de entrada HTTP de webhooks.

Responsabilidades SOLO de transporte:
1. Extraer del `Request` lo que el resto de la app necesita: body crudo
   (bytes exactos para verificar la firma) y cabeceras normalizadas.
2. Construir la entrada tipada `FacturaGPTWebhookDelivery`.
3. Delegar TODA la orquestación (firma, parseo, store-before-process,
   encolado) al caso de uso `ReceiveFacturaGPTWebhookUseCase`.
4. Traducir las excepciones de dominio a HTTP (401/400), igual que el resto
   de los controllers (`UploadReceiptController`).

El caso de uso responde 200 de inmediato para los eventos aceptados:
FacturaGPT hace entrega at-least-once y los reintentos de red se absorben
con la idempotency_key. Un error inesperado responde 500 -> el proveedor
reintenta (semántica at-least-once).
"""

from fastapi import BackgroundTasks, Request, status
from fastapi.responses import JSONResponse

from src.config.logger import logger
from src.application.commands.facturagpt_webhook_delivery import (
    FacturaGPTWebhookDelivery,
)
from src.bootstraps.use_cases_bootstrap import get_receive_facturagpt_webhook_use_case
from src.shared.errors.billing_exceptions import (
    BillingWebhookParseError,
    BillingWebhookSignatureError,
)


class ReceiveFacturaGPTWebhookController:
    def __init__(self) -> None:
        pass

    async def handle(
        self, request: Request, background_tasks: BackgroundTasks
    ) -> JSONResponse:
        # El body se lee como bytes crudos: la firma HMAC se verifica sobre
        # el body exacto que envió FacturaGPT, no sobre un JSON re-serializado.
        raw_body = await request.body()
        headers = {k.lower(): v for k, v in request.headers.items()}

        delivery = FacturaGPTWebhookDelivery(raw_body=raw_body, headers=headers)

        try:
            use_case = get_receive_facturagpt_webhook_use_case(
                background_tasks=background_tasks
            )
            await use_case.execute(delivery=delivery)
        except BillingWebhookSignatureError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "title": "Invalid Signature",
                    "status": 401,
                    "message": str(e),
                },
            )
        except BillingWebhookParseError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "title": "Bad Request",
                    "status": 400,
                    "message": str(e),
                },
            )
        except Exception as e:
            # Inesperado: 500 -> FacturaGPT reintentará (at-least-once). El
            # INSERT es idempotente, así que un reintento no duplica nada.
            logger.exception("Error inesperado procesando webhook FacturaGPT: %s", e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "title": "Internal Server Error",
                    "status": 500,
                    "message": "No se pudo procesar el webhook.",
                },
            )

        # Aceptado: almacenado (y encolado si aplicaba). ACK inmediato.
        # FacturaGPT solo exige el 200; el body es informativo para debugging.
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "received"},
        )
