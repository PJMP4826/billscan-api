import json
import base64
import hashlib
import hmac

from src.config.logger import logger

from src.domain.records.invoice_result import InvoiceResult
from src.domain.records.invoice_files import InvoiceFiles
from src.domain.records.invoice_result import InvoiceResult
from src.domain.records.cfdi_summary import CfdiSummary
from src.domain.enums.billing_status import BillingStatus

from src.domain.ports.billing_webhook_handler_port import BillingWebhookHandlerPort
from src.shared.errors.billing_exceptions import BillingWebhookParseError
from src.infrastructure.schemas.factura_gpt_schemas.facturagpt_webhook_event import (
    FacturaGPTWebhookEvent,
)
from src.domain.enums.billing_webhook_event_type import BillingWebHookEventType


class FacturaGPTWebhookHandler(BillingWebhookHandlerPort):
    """
    Verifies and parses FacturaGPT webhook deliveries.

    webhook_secret: The whsec_... value from the FacturaGPT Dashboard.
    """

    def __init__(self, webhook_secret: str) -> None:
        # Strip the "whsec_" prefix and decode from base64
        raw = webhook_secret.removeprefix("whsec_")
        # Pad base64 if needed
        self._raw_key = base64.b64decode(raw + "==")

    def verify_signature(self, headers: dict[str, str], raw_body: bytes) -> bool:
        """
        Recomputes the expected HMAC-SHA256 signature and compares it
        against the x-facturagpt-signature header using a constant-time
        comparison to prevent timing attacks.

        Returns False instead of raising — signature failure is a business
        decision for the caller (log, discard, alert), not an exception.
        """
        timestamp = headers.get("x-facturagpt-timestamp", "")
        signature = headers.get("x-facturagpt-signature", "")

        if not timestamp or not signature:
            return False

        msg = f"{timestamp}.".encode() + raw_body
        expected = "v1=" + hmac.new(self._raw_key, msg, hashlib.sha256).hexdigest()

        return hmac.compare_digest(expected, signature)

    def parse_event(
        self, raw_body: dict[str, str | bool | dict[str, str]]
    ) -> InvoiceResult:
        """
        Parses the raw webhook body into a domain InvoiceResult.

        Handles both factura.completed and factura.failed event types.
        Unknown event types return a PROCESSING status — safe default.
        """
        try:
            event = FacturaGPTWebhookEvent.model_validate(raw_body)
        except Exception as exc:
            raise BillingWebhookParseError(
                f"Could not parse FacturaGPT webhook payload: {exc}"
            ) from exc

        return self._map_event_to_result(event)

    def _map_event_to_result(self, event: FacturaGPTWebhookEvent) -> InvoiceResult:
        status = BillingStatus.map_webhook_status_event(status=event.status)

        files = None
        cfdi = None
        error_code = None
        error_msg = None

        web_hook_result_event: BillingWebHookEventType | None = event.event

        match web_hook_result_event:
            case BillingWebHookEventType.COMPLETED:
                if event.files:
                    files = InvoiceFiles(
                        xml_url=event.files.xml_url,
                        pdf_url=event.files.pdf_url,
                    )
                if event.cfdi_summary:
                    s = event.cfdi_summary
                    cfdi = CfdiSummary(
                        folio_fiscal=s.folio_fiscal,
                        emisor_rfc=s.emisor_rfc,
                        receptor_rfc=s.receptor_rfc,
                        amount=s.amount,
                        net_amount=s.net_amount,
                        tax_amount=s.tax_amount,
                        currency=s.currency,
                        fecha_timbrado=s.fecha_timbrado,
                    )
            case BillingWebHookEventType.FAILED:
                error_code = event.reason_code
                error_msg = event.reason_message
            case BillingWebHookEventType.BATCH_COMPLETE:
                logger.warning(
                    "Webhook FacturaGPT recibido con evento batch.completed; no hay mapeo de dominio definido aún"
                )
                logger.debug(
                    "Evento recibido: %s", json.dumps(event.model_dump(), indent=5)
                )
                pass
            case _:
                pass

        return InvoiceResult(
            session_id=event.session_id,
            external_id=event.external_id,
            status=status,
            event=web_hook_result_event,
            version=event.version,
            idempotency_key=event.idempotency_key,
            completed_at=event.completed_at,
            processing_time_seconds=event.processing_time_seconds,
            files=files,
            cfdi_summary=cfdi,
            error_code=error_code,
            error_message=error_msg,
        )
