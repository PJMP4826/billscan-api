from dataclasses import dataclass


@dataclass
class InvoiceFiles:
    """Download URLs for the generated invoice files."""

    xml_url: str | None = None
    pdf_url: str | None = None
