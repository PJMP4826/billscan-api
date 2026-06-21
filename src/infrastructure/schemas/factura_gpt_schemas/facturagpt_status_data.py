from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from .facturagpt_status_ocr import FacturaGPTStatusOcr


class FacturaGPTStatusData(BaseModel):
    session_id: str
    status: str
    ocr: Optional[FacturaGPTStatusOcr] = None
