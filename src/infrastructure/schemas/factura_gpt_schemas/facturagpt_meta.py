from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class FacturaGPTMeta(BaseModel):
    version: str
    session_id: Optional[str] = None
    timestamp: str
