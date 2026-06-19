from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class FacturaGPTCfdiSummary(BaseModel):
    folio_fiscal: Optional[str]   = None
    emisor_rfc: Optional[str]     = None
    receptor_rfc: Optional[str]   = None
    amount: Optional[str]         = None
    net_amount: Optional[str]     = None
    tax_amount: Optional[str]     = None
    currency: Optional[str]       = None
    fecha_timbrado: Optional[str] = None
