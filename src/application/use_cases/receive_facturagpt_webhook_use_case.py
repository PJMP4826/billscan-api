"""
ReceiveFacturaGPTWebhookUseCase — orquestación de la ingesta idempotente.

Flujo (store-before-process, at-least-once). Esta es la lógica de aplicación;
el controller HTTP solo construye la `FacturaGPTWebhookDelivery` y traduce
las excepciones a la respuesta HTTP.

1. Verificar la firma HMAC (v1=...) sobre `${timestamp}.${raw_body}`.
   Firma inválida -> lanza `BillingWebhookSignatureError` (401); NO se
   almacena ni se encola nada.
2. Parsear el payload a dominio (`InvoiceResult`).
   Payload no parseable -> lanza `BillingWebhookParseError` (400).
3. Store-before-process: INSERT ... ON CONFLICT DO NOTHING del payload crudo
   (la BD es la fuente de verdad para el worker posterior).
4. Encolar `process_facturagpt_webhook` con SOLO `{idempotency_key}` cuando el
   evento es NUEVO y por-receipt (factura.completed/.failed). Un duplicado de
   red de un evento ya almacenado NO se re-encola: si el job original quedó
   en cola, ese procesará la fila una sola vez; si la fila quedó pendiente
   (processed_at NULL), su recuperación corresponde al job de reconciliación
   (update_error deja NULL a propósito para eso).
   Los eventos informativos (batch.completed) se almacenan sin encolarse.
5. Éxito: no retorna nada (ni lanza). El controller responde 200
   inmediatamente (ACK al proveedor). FacturaGPT solo exige el 200, no lee
   body ni idempotency_key en la respuesta.
"""

from typing import Any

from src.config.logger import logger
from src.application.commands.facturagpt_webhook_delivery import (
    FacturaGPTWebhookDelivery,
)
from src.domain.enums.billing_webhook_event_type import BillingWebHookEventType
from src.domain.enums.job_names import JobName
from src.domain.ports.billing_webhook_handler_port import BillingWebhookHandlerPort
from src.domain.ports.queue_publisher_port import QueuePublisherPort
from src.domain.ports.repositories.facturagpt_webhook_repository_port import (
    FacturaGPTWebhookRepositoryPort,
)
from src.shared.errors.billing_exceptions import (
    BillingWebhookParseError,
    BillingWebhookSignatureError,
)


class ReceiveFacturaGPTWebhookUseCase:

    # Eventos por-receipt que disparan el worker. batch.completed es informativo
    # (no hay receipt que actualizar) y se almacena solo como auditoría.
    _PROCESSABLE_EVENTS = (
        BillingWebHookEventType.COMPLETED,
        BillingWebHookEventType.FAILED,
    )

    def __init__(
        self,
        webhook_handler: BillingWebhookHandlerPort,
        webhook_repository: FacturaGPTWebhookRepositoryPort,
        queue_publisher: QueuePublisherPort,
    ) -> None:
        self._webhook_handler = webhook_handler
        self._webhook_repository = webhook_repository
        self._queue_publisher = queue_publisher

    async def execute(self, delivery: FacturaGPTWebhookDelivery, body: dict[str, Any]) -> None:
        # Verificación de firma sobre el body crudo
        if not self._webhook_handler.verify_signature(
            headers=delivery.headers, raw_body=delivery.raw_body
        ):
            logger.warning("Webhook FacturaGPT con firma inválida. Se descarta sin procesar.")
            raise BillingWebhookSignatureError("La firma del webhook no es válida.")

        # El body ya viene validado desde el endpoint (WebHookEventRequest).
        # Se pasa como dict para re-parsear en el handler (Pydantic model_validate
        # sobre un dict es trivial en memoria).
        
        try:
            invoice_result = self._webhook_handler.parse_event(body)
        except Exception as exc:
            logger.error("Webhook FacturaGPT no parseable: %s", exc)
            raise BillingWebhookParseError(
                f"Could not parse FacturaGPT webhook payload: {exc}"
            ) from exc

        event = invoice_result.event
        event_type = event.value if event else "unknown"
        idempotency_key = invoice_result.idempotency_key
        session_id = invoice_result.session_id

        if not idempotency_key or not session_id:
            logger.warning(
                "Webhook FacturaGPT sin idempotency_key/session_id; se descarta. "
                "event_type=%s",
                event_type,
            )
            raise BillingWebhookParseError(
                "El webhook no trae idempotency_key ni session_id."
            )

        # Store-before-process: payload crudo persistido (idempotente).
        # Es la única escritura en el camino del request: el payload crudo
        # (con su external_id) queda como fuente de verdad para el worker.
        is_new = await self._webhook_repository.insert_if_new(
            idempotency_key=idempotency_key,
            event_type=event_type,
            session_id=session_id,
            payload=body,
        )

        if not is_new:
            logger.info(
                "Webhook FacturaGPT %s ya estaba almacenado (entrega duplicada).",
                idempotency_key,
            )

        # Encolar SOLO eventos nuevos por-receipt (completed/failed): el
        # recibo responde 200 tras un solo INSERT, sin SELECT extra. Un
        # duplicado ya se logueó arriba y NO genera otro job: la fila será
        # procesada por el job original o por reconciliación si quedó
        # pendiente (processed_at NULL).
        if is_new and event in self._PROCESSABLE_EVENTS:
            self._queue_publisher.enqueue_job(
                JobName.PROCESS_FACTURAGPT_WEBHOOK,
                {"idempotency_key": idempotency_key},
            )
            logger.info(
                "Webhook FacturaGPT %s (event=%s) encolado para procesamiento.",
                idempotency_key,
                event_type,
            )
        elif is_new:
            logger.info(
                "Webhook FacturaGPT %s (event=%s) nuevo pero informativo "
                "(solo auditoría, sin procesamiento).",
                idempotency_key,
                event_type,
            )