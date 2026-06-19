from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class FacturaGPTTicketOcr(BaseModel):
    merchant_name: Optional[str] = None
    merchant_rfc: Optional[str]  = None
    total: Optional[float]       = None
    date: Optional[str]          = None
