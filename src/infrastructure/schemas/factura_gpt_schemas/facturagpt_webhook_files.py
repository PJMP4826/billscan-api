from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class FacturaGPTWebhookFiles(BaseModel):
    xml_url: Optional[str] = None
    pdf_url: Optional[str] = None
