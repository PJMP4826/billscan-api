from dataclasses import dataclass

from src.domain.value_objects.billing_customer import BillingCustomerInfo
from src.domain.enums.sat_payment_methods import SatPaymentMethodCode
from src.domain.enums.invoice_use import InvoiceUse


@dataclass
class InvoiceRequest:
    """
    Everything needed to submit an invoice request through the port.
    This is the domain's language — no provider field names here.
    """

    external_id: str
    ticket_image_b64: str

    customer_id: str | None = None
    customer_info: BillingCustomerInfo | None = None

    save_customer: bool = False
    payment_method: SatPaymentMethodCode = SatPaymentMethodCode.POR_DEFINIR
    invoice_use: InvoiceUse = InvoiceUse.G03
    webhook_url: str | None = None
    test_mode: bool = False
