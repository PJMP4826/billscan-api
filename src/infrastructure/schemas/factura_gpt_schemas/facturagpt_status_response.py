from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from .facturagpt_status_data import FacturaGPTStatusData
from .facturagpt_error import FacturaGPTError
from .facturagpt_meta import FacturaGPTMeta


class FacturaGPTStatusResponse(BaseModel):
    ok: bool
    data: Optional[FacturaGPTStatusData] = None
    error: Optional[FacturaGPTError]     = None
    meta: FacturaGPTMeta
