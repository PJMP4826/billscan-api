from dataclasses import dataclass

from src.domain.enums.billing_status import BillingStatus
from src.domain.records.ocr_result import OcrResult
from src.domain.records.cfdi_summary import CfdiSummary
from src.domain.records.invoice_files import InvoiceFiles


@dataclass
class InvoiceResult:
    """
    Read model returned by the port after submission or a status check
    """

    session_id: str
    external_id: str
    status: BillingStatus

    ocr_result: OcrResult | None = None
    cfdi_summary: CfdiSummary | None = None
    files: InvoiceFiles | None = None

    error_code: str | None = None
    error_message: str | None = None
