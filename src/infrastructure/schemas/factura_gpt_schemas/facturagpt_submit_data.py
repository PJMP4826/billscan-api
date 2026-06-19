from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from facturagpt_ocr_result import FacturaGPTOcrResult


class FacturaGPTSubmitData(BaseModel):
    session_id: str
    external_id: str
    status: str
    ocr_result: Optional[FacturaGPTOcrResult] = None
