from dataclasses import dataclass

from src.application.dtos.cfdi.cfdi_dto import CfdiDto
from src.application.dtos.invoice_files_dto import InvoiceFiles


@dataclass
class CfdiResponseDto:
    receipt_uuid: str
    cfdi: CfdiDto
    invoice: InvoiceFiles

