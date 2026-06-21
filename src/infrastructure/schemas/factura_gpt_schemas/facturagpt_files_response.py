from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from .facturagpt_files_data import FacturaGPTFilesData
from .facturagpt_error import FacturaGPTError
from .facturagpt_meta import FacturaGPTMeta


class FacturaGPTFilesResponse(BaseModel):
    ok: bool
    data: Optional[FacturaGPTFilesData] = None
    error: Optional[FacturaGPTError]    = None
    meta: FacturaGPTMeta
