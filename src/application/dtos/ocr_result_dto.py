from dataclasses import dataclass


@dataclass
class OcrResult:
    """Structured data extracted from the ticket image by the provider's OCR."""

    merchant_name: str | None = None
    merchant_rfc: str | None = None
    amount: str | None = None
    net_amount: str | None = None
    tax_amount: str | None = None
    tax_rate: str | None = None
    currency: str | None = None
    date: str | None = None
    payment_method: str | None = None
    ticket_readable: bool = True
