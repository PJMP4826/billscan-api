from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class FacturaGPTOcrResult(BaseModel):
    merchant_name: Optional[str]  = None
    merchant_rfc: Optional[str]   = None
    amount: Optional[str]         = None
    net_amount: Optional[str]     = None
    tax_amount: Optional[str]     = None
    tax_rate: Optional[str]       = None
    currency: Optional[str]       = None
    date: Optional[str]           = None
    payment_method: Optional[str] = None
    ticket_readable: bool         = True
