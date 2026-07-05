from dataclasses import dataclass

from src.domain.enums.billing_status import BillingStatus
from src.domain.enums.billing_webhook_event_type import BillingWebHookEventType
from src.domain.records.ocr_result import OcrResult
from src.domain.records.cfdi_summary import CfdiSummary
from src.domain.records.invoice_files import InvoiceFiles


@dataclass
class InvoiceResult:
    """
    Read model returned by the port after submission or a status check
    """

    session_id: str | None = None
    external_id: str | None = None
    status: BillingStatus | None = None

    event: BillingWebHookEventType | None = None
    version: str | None = None
    idempotency_key: str | None = None
    completed_at: str | None = None
    processing_time_seconds: int | None = None

    ocr_result: OcrResult | None = None
    cfdi_summary: CfdiSummary | None = None
    files: InvoiceFiles | None = None

    error_code: str | None = None
    error_message: str | None = None
