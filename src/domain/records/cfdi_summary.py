from dataclasses import dataclass


@dataclass
class CfdiSummary:
    """Core fiscal data from the generated CFDI. Only present when COMPLETED."""

    folio_fiscal: str | None = None
    emisor_rfc: str | None = None
    receptor_rfc: str | None = None
    amount: str | None = None
    net_amount: str | None = None
    tax_amount: str | None = None
    currency: str | None = None
    fecha_timbrado: str | None = None
