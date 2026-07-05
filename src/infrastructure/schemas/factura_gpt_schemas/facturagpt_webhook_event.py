from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

from .facturagpt_webhook_files import FacturaGPTWebhookFiles
from .facturagpt_cfdi_summary import FacturaGPTCfdiSummary
from src.domain.enums.billing_webhook_event_type import BillingWebHookEventType


class FacturaGPTWebhookEvent(BaseModel):
    """
    Covers both factura.completed and factura.failed payloads.
    Fields absent in factura.failed (files, cfdi_summary) are Optional.
    """
    event: BillingWebHookEventType
    version: str
    idempotency_key: str
    session_id: str
    external_id: str
    status: str

    # completed-only fields
    completed_at: Optional[str]                    = None
    processing_time_seconds: Optional[int]         = None
    files: Optional[FacturaGPTWebhookFiles]        = None
    cfdi_summary: Optional[FacturaGPTCfdiSummary] = None

    # failed-only fields
    reason_code: Optional[str]    = None
    reason_message: Optional[str] = None
