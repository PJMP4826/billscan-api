from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from facturagpt_submit_data import FacturaGPTSubmitData
from facturagpt_error import FacturaGPTError
from facturagpt_meta import FacturaGPTMeta


class FacturaGPTSubmitResponse(BaseModel):
    ok: bool
    data: Optional[FacturaGPTSubmitData] = None
    error: Optional[FacturaGPTError]     = None
    meta: FacturaGPTMeta
