import asyncio
from typing import Any

import pytest

from src.application.commands.invoice_request_command import InvoiceRequestCommand
from src.domain.enums.billing_status import BillingStatus
from src.infrastructure.adapters.billing_providers.facturagpt_billing_adapter import (
    FacturaGPTBillingAdapter,
)
from src.shared.errors.billing_exceptions import (
    BillingProviderError,
    BillingUnreadableTicketError,
)

_META = {"version": "1.0", "session_id": "session-123", "timestamp": "now"}


def _request() -> InvoiceRequestCommand:
    return InvoiceRequestCommand(external_id="external-1", ticket_image_b64="aW1n")


def _build_adapter(monkeypatch: pytest.MonkeyPatch, response: dict[str, Any]):
    adapter = FacturaGPTBillingAdapter(base_url="https://example.test", api_key="key")

    async def fake_post(path: str, body: dict[str, Any]) -> dict[str, Any]:
        return response

    monkeypatch.setattr(adapter, "_post", fake_post)
    return adapter


def test_submit_raises_mapped_provider_error(monkeypatch):
    adapter = _build_adapter(
        monkeypatch,
        {
            "ok": False,
            "data": None,
            "error": {"code": "UNREADABLE_TICKET", "message": "Ticket ilegible"},
            "meta": _META,
        },
    )

    with pytest.raises(BillingUnreadableTicketError) as exc_info:
        asyncio.run(adapter.submit_invoice(_request()))

    assert exc_info.value.error_code == "UNREADABLE_TICKET"
    assert exc_info.value.get_message() == "Ticket ilegible"


def test_submit_returns_processing_result_on_success(monkeypatch):
    adapter = _build_adapter(
        monkeypatch,
        {
            "ok": True,
            "data": {
                "session_id": "session-123",
                "external_id": "external-1",
                "status": "processing",
                "ocr_result": None,
            },
            "error": None,
            "meta": _META,
        },
    )

    result = asyncio.run(adapter.submit_invoice(_request()))

    assert result.session_id == "session-123"
    assert result.external_id == "external-1"
    assert result.status is BillingStatus.PROCESSING


def test_submit_raises_when_success_response_has_no_data(monkeypatch):
    adapter = _build_adapter(
        monkeypatch,
        {"ok": True, "data": None, "error": None, "meta": _META},
    )

    with pytest.raises(BillingProviderError) as exc_info:
        asyncio.run(adapter.submit_invoice(_request()))

    assert exc_info.value.error_code == "BILLING_MISSING_DATA"
