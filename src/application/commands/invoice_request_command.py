from dataclasses import dataclass

from src.application.dtos.billing_customer_dto import BillingCustomerInfoDto
from src.domain.enums.sat_payment_methods import SatPaymentMethodCode
from src.domain.enums.invoice_use import InvoiceUse


@dataclass
class InvoiceRequestCommand:
    """
    Everything needed to submit an invoice request through the port.
    This is the domain's language — no provider field names here.
    """

    external_id: str  # sera el receipt_uuid guardado en BD
    ticket_image_b64: str

    customer_id: str | None = None
    customer_info: BillingCustomerInfoDto | None = None

    save_customer: bool = False

    # se podria obtener desde BD y mapearlo al Enum o dejar que el adpater de FacturaGPT lo detecte
    payment_method: SatPaymentMethodCode | None = SatPaymentMethodCode.POR_DEFINIR
    invoice_use: InvoiceUse = InvoiceUse.G03
    webhook_url: str | None = None
    test_mode: bool = False
