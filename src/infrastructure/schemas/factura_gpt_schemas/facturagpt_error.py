from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel


class FacturaGPTError(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None
