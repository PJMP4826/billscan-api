from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from .facturagpt_ticket_ocr import FacturaGPTTicketOcr


class FacturaGPTStatusOcr(BaseModel):
    ticket: Optional[FacturaGPTTicketOcr] = None
